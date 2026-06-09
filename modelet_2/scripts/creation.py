import re
import time
import hashlib
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import SKOS, RDF, RDFS, XSD
import unicodedata
from utilities.utilities import *

piirrite = Namespace('http://piirrite.univ-lyon1.fr/ontology/core#')
pcv = Namespace('http://piirrite.univ-lyon1.fr/vocabulary#')
saref = Namespace('https://saref.etsi.org/core/')

CURRENT_MODELET = get_current_path() + '/../'
GOT_FILE = '/GoT.ttl'
OSM_WIKI_URL = 'https://wiki.openstreetmap.org/w/api.php'
TAGINFO_API_V4 = "https://taginfo.openstreetmap.org/api/4"
    
######## Récupération & traitements des données OSM ########

def get_osm_keys_from_wiki() -> list[str]:
    print('Récupération des clés depuis le wiki…')
    osm_keys = []
    params = {
        'action': 'query',
        'list': 'allpages',
        'apnamespace': 0,  # Namespace principal (pas Template)
        'apprefix': 'Key:',  # Pages Key:*
        'format': 'json',
        'aplimit': 'max'
    }

    while True:
        try:
            response = requests.get(OSM_WIKI_URL, params=params) #type:ignore
        except Exception:
            return []
        raw_keys = response.json()
        osm_keys.extend([
            raw_key_page['title'].replace('Key:', '')
            for raw_key_page in raw_keys.get('query', {}).get('allpages', [])
        ])

        if 'continue' not in raw_keys:
            break
        params.update(raw_keys['continue'])

    # osm_keys = ['amenity']

    print(f'{len(osm_keys)} clés récupérées.')
    return osm_keys


def is_excluded_key(osm_raw_key) -> bool:
    # Exclusion des pages 'exemples' ou documentaires
    if re.search(r'(examples|tagkeylink|tagvaluelink|/doc$)', osm_raw_key, re.IGNORECASE):
        return True

    # Exclusion des clés contenant au moins 1 caractère d'un autre alpahabet que le latin
    for char in osm_raw_key:
        if char.isalpha():
            name = unicodedata.name(char, '')
            if not name.startswith(('LATIN', 'COMBINING', 'SPACE')):
                return True
    
    # Exclusion des clés locales spécifiques (ex: Pt-br:, RU:, Th:)
    if ':' in osm_raw_key:
        return True
    # Exclusion des clés niches
    excluded_terms = {
        '3D', 'advertising', 'contact', 'cuisine', 'editor', 'properties',
        'abutters', 'annotation', 'kneipp water cure',
        'line', 'oslostandarden', 'post box design', 'references',
        'repair', 'restrictions', 'site type', 'source:taxon', 'tours',
        'traffic calming', 'accessories', 'archaeological site',
        'megalith type', 'man made', 'memorial', 'rental', 'recycling',
        'vending', 'historic', 'military', 'telecom', 'source', 'name'
    }
    if any(osm_raw_key.lower().startswith(term.lower()) for term in excluded_terms):
        return True
    
    # Exclusion des clés secondaires
    secondary_keys = {
        'addr extra', 'airmark',
        'hazard type', 'hazard typology',
        'place', 'name', 'geological',
        'healthcare=blood donation', 'addr',
        'cycleway', 'door', 'healthcare',
        'leisure', 'smoothness', 'public transport',
        'shop', 'tracktype', 'theatre', 'trees',
        'bus stop'
    }
    if osm_raw_key.lower() in secondary_keys:
        return True

    return False


def _chunked(seq: list[str], size: int) -> Iterable[list[str]]:
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def _get_count_all(session: requests.Session, key: str, timeout: float) -> int | None:
    url = f"{TAGINFO_API_V4}/key/overview"
    r = session.get(url, params={"key": key}, timeout=timeout)
    r.raise_for_status()
    j = r.json()

    counts = j.get("data", {}).get("counts", [])
    for c in counts:
        if c.get("type") == "all":
            return int(c.get("count", 0))
    return 0


def filter_osm_keys(
    osm_raw_keys: list[str],
    *,
    min_count_all: int = 100_000,
    request_timeout_s: float = 20.0,
    max_workers: int = 16,
    chunk_size: int = 200,
) -> list[str]:
    print("Filtrage des clés pertinentes…")

    # 1) Normalisation + exclusion
    osm_keys = [
        osm_raw_key.replace(" ", "_")
        for osm_raw_key in osm_raw_keys
        if not is_excluded_key(osm_raw_key)
    ]

    # dédoublonnage
    seen = set()
    osm_keys = [k for k in osm_keys if not (k in seen or seen.add(k))] # type:ignore

    print(f"{len(osm_keys)}/{len(osm_raw_keys)} clés ont passé le filtre local. Vérification des nombres d'occurences…")

    kept: list[str] = []

    # 2) Taginfo (pas de vrai batch côté API, donc on “batch” côté client)
    with requests.Session() as session:
        display_progress_bar(0, len(osm_keys), message=f'des {len(osm_keys)} clés vérifiées…')
        for chunk_idx, keys_chunk in enumerate(_chunked(osm_keys, chunk_size), start=1):
            futures = {}
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                for k in keys_chunk:
                    futures[pool.submit(_get_count_all, session, k, request_timeout_s)] = k

                for fut in as_completed(futures):
                    k = futures[fut]
                    try:
                        count_all = fut.result()
                    except Exception:
                        continue

                    if count_all is not None and count_all > min_count_all:
                        kept.append(k)

            display_progress_bar(min(chunk_idx * chunk_size, len(osm_keys)), len(osm_keys), message=f'des {len(osm_keys)} clés vérifiées…')
    
    print(f"{len(kept)}/{len(osm_keys)} clés conservées (au moins 100 000 occurences totales).")
    return kept


def _clean_wikitext(s: str) -> str:
    if not s:
        return ""

    # comments
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.DOTALL)

    # refs
    s = re.sub(r"<ref[^>/]*/\s*>", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"<ref[^>]*>.*?</ref>", " ", s, flags=re.IGNORECASE | re.DOTALL)

    # external links: [url label] -> label ; [url] -> ''
    s = re.sub(r"\[(https?://[^\s\]]+)\s+([^\]]+)\]", r"\2", s)
    s = re.sub(r"\[(https?://[^\s\]]+)\]", "", s)

    # wiki links: [[A|B]] -> B ; [[A]] -> A
    s = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"\2", s)
    s = re.sub(r"\[\[([^\]]+)\]\]", r"\1", s)

    # bold/italic markup
    s = s.replace("'''", "").replace("''", "")

    # HTML tags
    s = re.sub(r"</?[^>]+>", " ", s)

    # whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _extract_keydescription_block(wikitext: str) -> str | None:
    if not wikitext:
        return None

    m = re.search(r"\{\{\s*KeyDescription\b(.*?)\n\}\}", wikitext, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        # fallback: parfois fermé sur la même ligne
        m = re.search(r"\{\{\s*KeyDescription\b(.*?)\}\}", wikitext, flags=re.IGNORECASE | re.DOTALL)
    return m.group(1) if m else None


def _extract_template_param(block: str, name: str) -> str | None:
    """
    Récupère |name=... (multiligne) dans un bloc de template.
    """
    if not block:
        return None

    pattern = (
        r"\|\s*" + re.escape(name) + r"\s*=\s*(.*?)"
        r"(?=\n\|\s*[A-Za-z0-9_]+\s*=|\n\}\}|\Z)"
    )
    m = re.search(pattern, block, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return None
    return m.group(1).strip()


def _truthy_on_element(v: str | None) -> bool:
    if v is None:
        return False
    t = v.strip().lower()
    if t in {"", "no", "0", "false", "n"}:
        return False
    # la plupart des pages utilisent yes/recommended, parfois autre chose
    return t in {"yes", "true", "1", "recommended"} or t.startswith("yes")


def _parse_description_and_elements_from_wikitext(wikitext: str) -> tuple[str, list[str]]:
    block = _extract_keydescription_block(wikitext)
    if not block:
        return ("", [])

    raw_desc = _extract_template_param(block, "description") or ""
    description = _clean_wikitext(raw_desc)

    on_elements: list[str] = []
    if _truthy_on_element(_extract_template_param(block, "onNode")):
        on_elements.append("PointOfInterest")
    if _truthy_on_element(_extract_template_param(block, "onWay")):
        on_elements.append("PolylineOfInterest")
    if _truthy_on_element(_extract_template_param(block, "onArea")):
        on_elements.append("AreaOfInterest")

    return (description, on_elements)


def _fetch_wiki_wikitexts_by_batch(
    session: requests.Session,
    keys: list[str],
    *,
    wiki_chunk_size: int = 50,
    timeout_s: float = 25.0,
) -> dict[str, str]:
    """
    Retourne {key: wikitext}.
    """
    out: dict[str, str] = {}

    for keys_chunk in _chunked(keys, wiki_chunk_size):
        titles = "|".join([f"Key:{k}" for k in keys_chunk])
        r = session.get(
            OSM_WIKI_URL,
            params={
                "action": "query",
                "prop": "revisions",
                "rvprop": "content",
                "rvslots": "main",
                "formatversion": 2,
                "format": "json",
                "redirects": 1,
                "titles": titles,
            }, #type:ignore
            timeout=timeout_s,
        )
        r.raise_for_status()
        j = r.json()
        pages = j.get("query", {}).get("pages", [])

        for p in pages:
            title = p.get("title", "")
            if not title.startswith("Key:"):
                continue
            key = title.split("Key:", 1)[1]

            if "missing" in p:
                out[key] = ""
                continue

            revs = p.get("revisions") or []
            if not revs:
                out[key] = ""
                continue

            content = revs[0].get("slots", {}).get("main", {}).get("content", "")
            out[key] = content or ""

    return out


def _get_values_over_threshold(
    session: requests.Session,
    key: str,
    *,
    min_count_all: int = 10_000,
    timeout_s: float = 20.0,
    rp: int = 200,
    normalize_spaces_to_underscore: bool = True,
) -> list[str]:
    values: list[str] = []
    page = 1

    while True:
        r = session.get(
            f"{TAGINFO_API_V4}/key/values",
            params={
                "key": key,
                "page": page,
                "rp": rp,
                "sortname": "count_all",
                "sortorder": "desc",
                "filter": "all",
            }, #type:ignore
            timeout=timeout_s,
        )
        r.raise_for_status()
        j = r.json()

        data = (j.get("data") or [])
        if not data:
            break

        stop = False
        for item in data:
            cnt = int(item.get("count", 0))
            if cnt <= min_count_all:
                stop = True
                break

            v = str(item.get("value", "")).strip()
            if not v:
                continue

            if normalize_spaces_to_underscore:
                v = v.replace(" ", "_")

            values.append(v)

        if stop:
            break

        # pagination
        total = int(j.get("total", 0))
        if page * rp >= total:
            break
        page += 1

    # dédoublonnage en gardant l'ordre
    seen = set()
    values = [v for v in values if not (v in seen or seen.add(v))]  # type: ignore
    return values


def normalize_osm_key(s: str) -> str:
    s = s.replace(" ", "_").strip()
    return s


def get_osm_keys_datas(
    osm_keys: list[str],
    *,
    wiki_chunk_size: int = 50,
    taginfo_max_workers: int = 16,
    request_timeout_s: float = 25.0,
) -> tuple[dict[str, str], dict[str, list[str]], dict[str, list[str]]]:
    print("Récupération du contenu wiki des clés…")
    # normalisation + dédoublonnage (garde l’ordre)
    keys = [normalize_osm_key(k) for k in osm_keys]
    seen = set()
    keys = [k for k in keys if not (k in seen or seen.add(k))]  # type: ignore

    osm_keys_descriptions: dict[str, str] = {k: '' for k in keys}
    osm_keys_ranges: dict[str, list[str]] = {k: [] for k in keys}
    osm_keys_values: dict[str, list[str]] = {k: [] for k in keys}

    with requests.Session() as session:
        # 1) WIKI en batch
        wikitexts = _fetch_wiki_wikitexts_by_batch(
            session,
            keys,
            wiki_chunk_size=wiki_chunk_size,
            timeout_s=request_timeout_s,
        )

        n_osm_keys_desc = 0
        n_osm_keys_ranges_valid = 0
        for k, wikitext in wikitexts.items():
            k_norm = normalize_osm_key(k)

            desc, elems = _parse_description_and_elements_from_wikitext(wikitext)
            osm_keys_descriptions[k_norm] = clean_osm_description(desc)
            if desc:
                n_osm_keys_desc += 1
            
            osm_keys_ranges[k_norm] = elems
            if elems:
                n_osm_keys_ranges_valid += 1
        
        wiki_keys = set(normalize_osm_key(k) for k in wikitexts.keys())
        input_keys = set(normalize_osm_key(k) for k in keys)
        all_keys = input_keys | wiki_keys

        # 2) TAGINFO (1 req / key, parallélisé)
        futures = {}
        with ThreadPoolExecutor(max_workers=taginfo_max_workers) as pool:
            for k in all_keys:
                futures[pool.submit(
                    _get_values_over_threshold,
                    session,
                    k,
                    min_count_all=10_000,
                    timeout_s=request_timeout_s,
                    rp=200,
                    normalize_spaces_to_underscore=True,
                )] = k

            n_osm_keys_values_explicit = 0
            for fut in as_completed(futures):
                k = futures[fut]
                k_norm = normalize_osm_key(k)

                vals = fut.result()
                values = valid_values(vals)

                osm_keys_values[k_norm] = values
                if values:
                    n_osm_keys_values_explicit += 1

        print(f'{n_osm_keys_desc}/{len(osm_keys)} clés ont une description.')
        print(f'{n_osm_keys_ranges_valid}/{len(osm_keys)} clés ont au moins une range valide.')
        print(f'{n_osm_keys_values_explicit}/{len(osm_keys)} clés ont au moins une valeur explicite avec au moins 10 000 occurences et ne comportant pas de caractères non-latins.')

        return osm_keys_descriptions, osm_keys_ranges, osm_keys_values


def valid_values(raw_values:list[str]) -> list[str]:
    valid_values = []

    for raw_value in raw_values:
        is_valid_value = True

        for char in raw_value:
            if char.isalpha():
                name = unicodedata.name(char, '')
                if not name.startswith(('LATIN', 'COMBINING', 'SPACE')):
                    is_valid_value = False

        if is_valid_value: valid_values.append(raw_value)
    
    return valid_values


def clean_osm_description(description:str) -> str:
    clean_description = (
        description
        .replace('[[', '')
        .replace(']]', '')
        .replace("'''", "'")
        .replace('<br>', '')
        .strip()
    )

    # On ne veut pas les références internes au wiki
    # -> Supprimer les phrases contenant 'see (the) page' ou 'see also'
    clean_description = re.sub(
        r'[^.]*\bsee\s+(?:the\s+)?page\b[^.]*\.|[^.]*\bsee\s+also\b[^.]*\.',
        '', 
        clean_description,
        flags = re.IGNORECASE
    )
    # Supprimer les fragments contenant 'osmcarto-rendering'
    # Gère les cas avec ou sans point final, en milieu ou fin de chaîne
    clean_description = re.sub(
        r'[^.]*\bosmcarto-rendering\b[^.]*\.?',
        '',
        clean_description,
        flags=re.IGNORECASE
    )
    # Remplacer {{Tag|A|B}} par A=B
    clean_description = re.sub(
        r'\{\{Tag\|([^|}]+)\|([^}]+)\}\}', 
        r'\1=\2', 
        clean_description,
        flags = re.IGNORECASE
    )
    # Remplacer {{tag|A}} par A
    clean_description = re.sub(
        r'\{\{tag\|([^}]+)\}\}', 
        r'\1', 
        clean_description,
        flags = re.IGNORECASE
    )
    # Remplacer {{wikiIcon|…|B}} par B
    clean_description = re.sub(
        r'\{\{wikiIcon\|[^|}]+\|([^}]+)\}\}', 
        r'\1', 
        clean_description,
        flags = re.IGNORECASE
    )
    # Supprimer {{main|…}} avec espace final éventuel
    clean_description = re.sub(
        r'\{\{main\|[^}]+\}\}\s*', 
        '', 
        clean_description,
        flags = re.IGNORECASE
    )
    # Remplacer '{{Prefix|A}}' par 'A'
    clean_description = re.sub(
        r'\{\{Prefix\|([^}]+)\}\}',
        r'\1',
        clean_description
    )

    clean_description = clean_description.replace('  ', ' ') \
        .replace('Tag:', '').replace('|', '')

    return clean_description


def _fetch_wiki_wikitexts_by_titles_batch(
    session: requests.Session,
    titles: list[str],
    *,
    wiki_chunk_size: int = 25,
    timeout_s: float = 25.0,
    sleep_s: float = 0.1,
) -> dict[str, str]:
    out: dict[str, str] = {}

    def fetch_chunk(titles_chunk: list[str]) -> None:
        if not titles_chunk:
            return

        # POST -> évite les URLs trop longues
        payload = {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
            "formatversion": 2,
            "format": "json",
            "redirects": 1,
            "titles": "|".join(titles_chunk),
        }

        try:
            r = session.post(OSM_WIKI_URL, data=payload, timeout=timeout_s)
            r.raise_for_status()
            j = r.json()
        except Exception:
            # Si un chunk échoue (connexion coupée), on split en 2 pour isoler
            if len(titles_chunk) == 1:
                out[titles_chunk[0]] = ""
                return
            mid = len(titles_chunk) // 2
            fetch_chunk(titles_chunk[:mid])
            fetch_chunk(titles_chunk[mid:])
            return

        pages = j.get("query", {}).get("pages", []) or []
        for p in pages:
            title = p.get("title") or ""
            if not title:
                continue

            if "missing" in p:
                out[title] = ""
                continue

            revs = p.get("revisions") or []
            if not revs:
                out[title] = ""
                continue

            content = revs[0].get("slots", {}).get("main", {}).get("content", "")
            out[title] = content or ""

    for chunk_idx, titles_chunk in enumerate(_chunked(titles, wiki_chunk_size)):
        fetch_chunk(titles_chunk)
        if sleep_s:
            time.sleep(sleep_s)
        display_progress_bar(min((chunk_idx + 1) * wiki_chunk_size, len(titles)), len(titles), message = f'des {len(titles)} valeurs récupérées…')

    return out


def _extract_valuedescription_block(wikitext: str) -> str | None:
    if not wikitext:
        return None

    m = re.search(r"\{\{\s*ValueDescription\b(.*?)\n\}\}", wikitext, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        m = re.search(r"\{\{\s*ValueDescription\b(.*?)\}\}", wikitext, flags=re.IGNORECASE | re.DOTALL)
    return m.group(1) if m else None


def _extract_tags_from_templates(text: str) -> list[str]:
    if not text:
        return []

    out: list[str] = []

    # {{Tag|...}}
    for m in re.finditer(r"\{\{\s*Tag\s*\|\s*([^}]+?)\s*\}\}", text, flags=re.IGNORECASE | re.DOTALL):
        inside = m.group(1).strip()
        parts = [p.strip() for p in inside.split("|") if p.strip() and "=" not in p]  # ignore params nommés
        if not parts:
            continue

        if len(parts) == 1:
            t = parts[0]
        else:
            t = f"{parts[0]}={parts[1]}"
        out.append(t)

    # {{Key|...}} (on prend juste la clé)
    for m in re.finditer(r"\{\{\s*Key\s*\|\s*([^}]+?)\s*\}\}", text, flags=re.IGNORECASE | re.DOTALL):
        inside = m.group(1).strip()
        # ignore params nommés
        if "=" in inside:
            continue
        out.append(inside)

    # dédoublonnage en gardant l'ordre
    seen = set()
    out = [t for t in out if not (t in seen or seen.add(t))]  # type: ignore
    return out


def _normalize_combination_tag(tag: str) -> str:
    t = (tag or "").strip().replace(" ", "_")
    if not t:
        return ""
    if "=" in t:
        t = t.split("=", 1)[0].strip()
    return t


def _extract_combination_tags_union(wikitext: str) -> list[str]:
    raw_items: list[str] = []

    block = _extract_valuedescription_block(wikitext) or ""
    comb = _extract_template_param(block, "combination")
    if comb:
        raw_items.extend(_extract_tags_from_templates(comb))

    sec = re.search(
        r"==\s*Tags used in combination\s*==\s*(.*?)(?=\n==[^=]|\Z)",
        wikitext,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if sec:
        raw_items.extend(_extract_tags_from_templates(sec.group(1)))

    # normalize + dédoublonnage + nettoyage
    normalized: list[str] = []
    seen = set()
    for item in raw_items:
        key_only = _normalize_combination_tag(item)
        if not key_only:
            continue
        if key_only in seen:
            continue
        seen.add(key_only)
        normalized.append(key_only)

    return normalized


def _extract_value_description(wikitext: str) -> str:
    block = _extract_valuedescription_block(wikitext)
    if not block:
        return ""
    raw_desc = _extract_template_param(block, "description") or ""
    return _clean_wikitext(raw_desc)


def _title_to_key_value(title: str) -> tuple[str, str] | None:
    if not title.startswith("Tag:"):
        return None
    rest = title.split("Tag:", 1)[1]
    if "=" not in rest:
        return None
    k, v = rest.split("=", 1)
    k = k.strip().replace(" ", "_")
    v = v.strip().replace(" ", "_")
    return (k, v)


def get_osm_values_datas(
    osm_keys_values: dict[str, list[str]],
    *,
    wiki_chunk_size: int = 50,
    request_timeout_s: float = 25.0,
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, list[str]]]]:
    print("Récupération du contenu wiki des valeurs…")

    # 1) Construire la liste des titres Tag:key=value
    titles: list[str] = []
    wanted_pairs: set[tuple[str, str]] = set()

    for key, values in osm_keys_values.items():
        k = key.replace(" ", "_")
        if values:
            for value in values:
                v = value.replace(" ", "_")
                wanted_pairs.add((k, v))

                # Titre wiki en général : espaces ok (MediaWiki gère aussi les '_')
                titles.append(f"Tag:{k}={v.replace('_', ' ')}")
        else:
            wanted_pairs.add((k, "any"))

    # dédoublonnage titres (garde ordre)
    seen = set()
    titles = [t for t in titles if not (t in seen or seen.add(t))]  # type: ignore

    osm_values_descriptions: dict[str, dict[str, str]] = {}
    osm_values_combinations: dict[str, dict[str, list[str]]] = {}

    # initialisation des dictionnaires
    # pour s'assurer qu'ils ont autant d'éléments qu'osm_keys_values
    for k, values in osm_keys_values.items():
        osm_values_descriptions[k] = {}
        osm_values_combinations[k] = {}
        for v in (values if values else ["any"]):
            osm_values_descriptions[k][v] = ""
            osm_values_combinations[k][v] = []

    with requests.Session() as session:
        wikitexts_by_title = _fetch_wiki_wikitexts_by_titles_batch(
            session,
            titles,
            wiki_chunk_size=wiki_chunk_size,
            timeout_s=request_timeout_s,
        )

    # 2) Parser
    processed = 0
    for title, wikitext in wikitexts_by_title.items():
        kv = _title_to_key_value(title)
        if not kv:
            continue
        k, v = kv
        k = normalize_osm_key(k)
        v = v.replace(" ", "_").strip()
        if (k, v) not in wanted_pairs:
            continue

        desc = _extract_value_description(wikitext)
        comb_keys = _extract_combination_tags_union(wikitext)

        osm_values_descriptions.setdefault(k, {})[v] = clean_osm_description(desc)
        osm_values_combinations.setdefault(k, {})[v] = should_be_concept(comb_keys)

        processed += 1

    print(f"{processed}/{len(wanted_pairs)} pages Tag:* traitées.")
    return osm_values_descriptions, osm_values_combinations


def should_be_concept(values: list[str]) -> list[str]:
    returned_values = []

    for value in values:

        if any(b in value.lower() for b in ['yes', 'no']):
            if 'openinghours' in value.lower():
                value = 'OpeningHours'
            else:
                continue

        # certaines valeurs contiennent :00 mais ce sont toutes des horaires
        # certaines valeurs contiennent des suffixes régionaux à deux lettres,
        # mais on ne s'intéressent qu'aux clés globales
        if any(s in value for s in [':00',
            'ES:', 'NL:', 'DE:', 'FR:', 'FI:', 'IT:', 'US:']):
            continue

        if is_number(value.split('_')[0]):
            continue

        if any(value.startswith(o) for o in ['1st', '2nd', '3rd']):
            continue

        if value.startswith('http'):
            continue

        if is_color(value):
            continue

        if is_date(value):
            continue

        if is_email(value):
            continue

        # on considère que les valeurs composées de 3 mots ou plus
        # ne sont pas généralisables en concepts
        if len(value.split('_')) > 2 or len(value.split(' ')) > 3:
            continue

        # peut-être que des valeurs généralisables en concepts
        # contiennent des caractères spéciaux, mais on considère
        # que ça ne vaut pas le coup de les chercher
        if any(sc in value for sc in [':', ';', '/', ',', '~',
                                      '〜', '|', '%', '"', '!',
                                      '®', '（', '）', '«', '»',
                                      '#', '+', '*', '=']):
            continue

        value = value.replace('\'', '')
        value = value.replace('.', '_')

        returned_values.append(value)
    
    return returned_values


def filterPropertyValuesFromFeatureKinds(osm_keys_values:dict[str, list[str]]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    propertyValues = {}
    featureKinds = {}

    for osm_key, osm_values in osm_keys_values.items():
        propertyValues[osm_key] = []
        featureKinds[osm_key] = []
        
        for osm_value in osm_values:
            # valeurs OSM non-pertinentes
            if any(b in osm_value.lower() for b in ['yes', 'no']):
                continue

            if ("openinghours" in osm_value.lower()):
                continue

            if is_number(osm_value.split('_')[0]):
                continue

            # certaines valeurs contiennent :00 mais ce sont toutes des horaires
            # certaines valeurs contiennent des suffixes régionaux à deux lettres,
            # mais on ne s'intéressent qu'aux clés globales
            if any(s in osm_value for s in [':00',
                'ES:', 'NL:', 'DE:', 'FR:', 'FI:', 'IT:', 'US:']):
                continue

            # valeurs OSM pertinentes comme skos:Values
            if any(osm_value.startswith(o) for o in ['1st', '2nd', '3rd']):
                propertyValues[osm_key].append(osm_value)
                continue

            if osm_value.startswith('http'):
                propertyValues[osm_key].append(osm_value)
                continue

            if is_color(osm_value):
                propertyValues[osm_key].append(osm_value)
                continue

            if is_date(osm_value):
                propertyValues[osm_key].append(osm_value)
                continue

            if is_email(osm_value):
                propertyValues[osm_key].append(osm_value)
                continue

            # on considère que les valeurs composées de 3 mots ou plus
            # ne sont pas généralisables en concepts
            if len(osm_value.split('_')) > 2 or len(osm_value.split(' ')) > 3:
                propertyValues[osm_key].append(osm_value)
                continue

            # peut-être que des valeurs généralisables en concepts
            # contiennent des caractères spéciaux, mais on considère
            # que ça ne vaut pas le coup de les chercher
            if any(sc in osm_value for sc in [':', ';', '/', ',', '~',
                                              '〜', '|', '%', '"', '!',
                                              '®', '（', '）', '«', '»',
                                              '#', '+', '*', '=']):
                propertyValues[osm_key].append(osm_value)
                continue
            
            # valeurs OSM pertinentes comme saref:FeatureKind
            osm_value = osm_value.replace('\'', '')
            osm_value = osm_value.replace('.', '_')

            featureKinds[osm_key].append(osm_value)

    return propertyValues, featureKinds


def osmIdentifierToLocalName(osmIdentifier:str) -> str:
    s = osmIdentifier.replace('-', '_')
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r'[^A-Za-z0-9_]+', '_', s)
    s = re.sub(r'_+', '_', s)
    s = s.strip('_')
    return snake_to_camel(s)


def dealWithDuplicateFeatureKindNames(
        osm_keys_descriptions: dict[str, str],
        osm_keys_values_descriptions: dict[str, dict[str, str]]
) -> tuple[dict[str, dict[str, str | URIRef]], dict[str, dict[str, list[dict[str, str | URIRef]]]]]:
    # On gère séparement deux cas
    # A. La valeur de clé avec laquelle on va générer un featureKind n'apparait dans aucun autre conceptScheme
    #    On l'enregistre alors avec un local name de la forme K_{value}
    # B. La valeur de clé avec laquelle on va générer un featureKind apparait dans au moins un autre conceptScheme
    #    Il y a alors risque d'ambiguité et on l'enregistre avec un local name de la forme K_{value}_{scheme}
    #    De plus, on crée un featureKind "chapeau" avec un local name de la forme K_{value} qui est ambigü
    #    mais regroupe les featureKind désambigüés via skos:broader
    uniqueValues = {}
    repeatedValues = {}

    for osm_key, _ in osm_keys_descriptions.items():
        for value, value_description in osm_keys_values_descriptions[osm_key].items():
            if value in repeatedValues.keys():
                repeatedValues[value].append(
                    {
                        "desc": value_description,
                        "scheme_uri": pcv["S_" + osmIdentifierToLocalName(osm_key)],
                        "scheme_name": osm_key
                    }
                )
            else:
                if value in uniqueValues.keys():
                    repeatedValues[value] = [{
                        "desc": value_description,
                        "scheme_uri": pcv["S_" + osmIdentifierToLocalName(osm_key)],
                        "scheme_name": osm_key
                    }]
                    repeatedValues[value].append({
                        "desc": uniqueValues[value]["desc"],
                        "scheme_uri": uniqueValues[value]["scheme_uri"],
                        "scheme_name": uniqueValues[value]["scheme_name"]
                    })

                    uniqueValues.pop(value)
                else:
                    uniqueValues[value] = {
                        "desc": value_description,
                        "scheme_uri": pcv["S_" + osmIdentifierToLocalName(osm_key)],
                        "scheme_name": osm_key
                    }

    return uniqueValues, repeatedValues


def parse_osm_wiki_to_create_glossary(pcv_graph:Graph) -> None:
    osm_raw_keys = get_osm_keys_from_wiki()
    osm_keys = filter_osm_keys(osm_raw_keys)
    osm_keys_descriptions, osm_keys_ranges, osm_keys_values = get_osm_keys_datas(osm_keys)
    osm_keys_values_descriptions, osm_keys_values_tuics = get_osm_values_datas(osm_keys_values)

    # TODO récupérer les ranges (comme osm_keys_ranges) pour les saref:Property

    osm_key_property_values, osm_key_feature_kinds = filterPropertyValuesFromFeatureKinds(osm_keys_values)
    for osm_key, feature_kinds in osm_key_feature_kinds.items():
        osm_keys_values_descriptions[osm_key] = {cle: valeur for cle, valeur in osm_keys_values_descriptions[osm_key].items() if cle in feature_kinds}

    values_uris = {}
    for osm_key, property_values in osm_key_property_values.items():
        values_uris[osm_key] = []
        for property_value in property_values:
            values_uris[osm_key].append(add_Value(
                g = pcv_graph,
                local_name = osmIdentifierToLocalName(property_value),
                pref_labels = { "en": snake_to_natural(property_value, True) }
            ))

    uniqueValues, repeatedValues = dealWithDuplicateFeatureKindNames(osm_keys_descriptions, osm_keys_values_descriptions)

    for value, value_data in uniqueValues.items():
        properties_uris = []
        for tuic in osm_keys_values_tuics[value_data["scheme_name"]][value]:
            property_uri = add_Property(
                g = pcv_graph,
                local_name = osmIdentifierToLocalName(tuic),
                pref_labels = { "en": snake_to_natural(tuic) },
                definitions = {},
                scheme_uri = pcv['Properties'],
                allowed_values_uris = [],
                value_datatype_uri = None,
                unit_uri = None
            )
            properties_uris.append(property_uri)
        
        add_FeatureKind(
            g = pcv_graph,
            local_name = osmIdentifierToLocalName(value),
            pref_labels = { "en": snake_to_natural(value, True) },
            definitions = { "en": value_data["desc"] },
            scheme_uri = value_data["scheme_uri"], #type: ignore
            properties_uris = properties_uris
        )

    for value, values_data in repeatedValues.items():
        broader_FK_uri = add_BroaderFK(
            g = pcv_graph,
            local_name = osmIdentifierToLocalName(value),
            pref_labels = { "en": snake_to_natural(value, True) }
        )

        for value_data in values_data:
            properties_uris = []
            for tuic in osm_keys_values_tuics[value_data["scheme_name"]][value]: #type: ignore
                property_uri = add_Property(
                    g = pcv_graph,
                    local_name = osmIdentifierToLocalName(tuic),
                    pref_labels = { "en": snake_to_natural(tuic) },
                    definitions = {},
                    scheme_uri = pcv['Properties'],
                    allowed_values_uris = [],
                    value_datatype_uri = None,
                    unit_uri = None
                )
                properties_uris.append(property_uri)
            
            add_FeatureKind(
                g = pcv_graph,
                local_name = osmIdentifierToLocalName(value) + '_' + osmIdentifierToLocalName(value_data["scheme_name"]), #type: ignore
                pref_labels = { "en": snake_to_natural(value, True) },
                definitions = { "en": value_data["desc"] }, #type: ignore
                scheme_uri = value_data["scheme_uri"], #type: ignore
                properties_uris = properties_uris,
                broader_FK_uri = broader_FK_uri
            )

    for osm_key, key_description in osm_keys_descriptions.items():
        add_Scheme(
            g = pcv_graph,
            local_name = osmIdentifierToLocalName(osm_key),
            pref_labels = { "en": snake_to_natural(osm_key, True) },
            definitions = { "en": key_description },
            values_uris = values_uris[osm_key]
        )


######## Gestion du KG ########

def init_pcv_graph() -> Graph:
    pcv_graph = Graph()
    pcv_graph.bind('piirrite', piirrite)
    pcv_graph.bind('pcv', pcv)
    pcv_graph.bind('rdfs', RDFS)
    pcv_graph.bind('skos', SKOS)
    pcv_graph.bind('xsd', XSD)
    pcv_graph.bind('saref', saref)

    return pcv_graph


def add_Scheme(
    g: Graph,
    local_name: str,
    pref_labels: dict[str, str],
    definitions: dict[str, str],
    values_uris: list[URIRef] = []
) -> URIRef:
    scheme_uri = pcv["S_" + local_name]
    g.add((scheme_uri, RDF.type, SKOS.ConceptScheme))
    if values_uris: g.add((scheme_uri, RDF.type, saref.Property))

    for lang, pref_label in pref_labels.items():
        if pref_label != '':
            g.add((scheme_uri, SKOS.prefLabel, Literal(pref_label, lang = lang)))
    for lang, definition in definitions.items():
        if definition != '':
            g.add((scheme_uri, SKOS.definition, Literal(definition, lang = lang)))
    for value_uri in values_uris:
        g.add((scheme_uri, piirrite.hasAllowedValue, value_uri))
    
    return scheme_uri


def add_FeatureKind(
    g: Graph,
    local_name: str,
    pref_labels: dict[str, str] = {},
    definitions: dict[str, str] = {},
    scheme_uri: URIRef | None = None,
    properties_uris: list[URIRef] = [],
    broader_FK_uri: URIRef | None = None,
) -> URIRef:
    feature_kind_uri = pcv["K_" + local_name]
    g.add((feature_kind_uri, RDF.type, saref.FeatureKind))
    g.add((feature_kind_uri, RDF.type, SKOS.Concept))

    for lang, pref_label in pref_labels.items():
        if pref_label != '':
            g.add((feature_kind_uri, SKOS.prefLabel, Literal(pref_label, lang = lang)))
    for lang, definition in definitions.items():
        if definition != '':
            g.add((feature_kind_uri, SKOS.definition, Literal(definition, lang = lang)))
    if scheme_uri:
        g.add((feature_kind_uri, SKOS.inScheme, scheme_uri))
    for property_uri in properties_uris:
        g.add((feature_kind_uri, saref.hasProperty, property_uri))
    if broader_FK_uri:
        g.add((feature_kind_uri, SKOS.broader, broader_FK_uri))
        g.add((broader_FK_uri, SKOS.narrower, feature_kind_uri))
    
    return feature_kind_uri


def add_BroaderFK(
    g: Graph,
    local_name: str,
    pref_labels: dict[str, str],
) -> URIRef:
    broader_fk_uri = pcv["K_" + local_name]
    g.add((broader_fk_uri, RDF.type, saref.FeatureKind))
    g.add((broader_fk_uri, RDF.type, SKOS.Concept))

    for lang, pref_label in pref_labels.items():
        if pref_label != '':
            g.add((broader_fk_uri, SKOS.prefLabel, Literal(pref_label, lang = lang)))
    g.add((broader_fk_uri, SKOS.scopeNote, Literal("Ambiguous OSM term depending on the application context", lang = "en")))
    g.add((broader_fk_uri, SKOS.scopeNote, Literal("Terme OSM ambigü selon le contexte d'application", lang = "fr")))

    return broader_fk_uri


def add_Property(
    g: Graph,
    local_name: str,
    pref_labels: dict[str, str] = {},
    definitions: dict[str, str] = {},
    scheme_uri: URIRef = pcv['Properties'],
    allowed_values_uris: list[URIRef] = [],
    value_datatype_uri: URIRef | None  = None,
    unit_uri: URIRef | None = None,
) -> URIRef:
    property_uri = pcv["P_" + local_name]
    g.add((property_uri, RDF.type, saref.Property))
    g.add((property_uri, RDF.type, SKOS.Concept))

    for lang, pref_label in pref_labels.items():
        if pref_label != '':
            g.add((property_uri, SKOS.prefLabel, Literal(pref_label, lang = lang)))
    for lang, definition in definitions.items():
        if definition != '':
            g.add((property_uri, SKOS.definition, Literal(definition, lang = lang)))
    if scheme_uri:
        g.add((property_uri, SKOS.inScheme, scheme_uri))
    for allowed_value_uri in allowed_values_uris:
        g.add((property_uri, piirrite.hasAllowedValue, allowed_value_uri))
    if value_datatype_uri:
        g.add((property_uri, piirrite.hasValueDatatype, value_datatype_uri))
    if unit_uri:
        g.add((property_uri, piirrite.hasUnit, unit_uri))
    
    return property_uri


def add_Value(
    g: Graph,
    local_name: str,
    pref_labels: dict[str, str] = {},
    definitions: dict[str, str] = {},
    scheme_uri: URIRef = pcv['Values'],
) -> URIRef:
    hash_id = hashlib.md5(f"{local_name}".encode()).hexdigest()
    value_uri = pcv[f"value_{hash_id}"]
    g.add((value_uri, RDF.type, SKOS.Concept))

    for lang, pref_label in pref_labels.items():
        if pref_label != '':
            g.add((value_uri, SKOS.prefLabel, Literal(pref_label, lang = lang)))
    for lang, definition in definitions.items():
        if definition != '':
            g.add((value_uri, SKOS.definition, Literal(definition, lang = lang)))
    if scheme_uri:
        g.add((value_uri, SKOS.inScheme, scheme_uri))

    return value_uri


def main():
    pcv_graph = init_pcv_graph()
    
    parse_osm_wiki_to_create_glossary(pcv_graph)
    pcv_graph.serialize(CURRENT_MODELET + GOT_FILE, 'turtle')

    print(f'Glossaire créé.')

if __name__ == '__main__':
    main()
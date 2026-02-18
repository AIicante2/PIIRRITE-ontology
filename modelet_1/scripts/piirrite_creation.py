import re
import time
import requests
from requests.adapters import HTTPAdapter
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib3.util.retry import Retry
from typing import Iterable
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import SKOS, RDF, RDFS, OWL, XSD
from utilities.utilities import *

piirrite = Namespace('http://piirrite.univ-lyon1.fr/ontology/core#')
piirritev = Namespace('http://piirrite.univ-lyon1.fr/vocabulary#')
osmkey = Namespace('https://www.openstreetmap.org/wiki/Key:')
geo = Namespace('http://www.opengis.net/ont/geosparql#')
saref = Namespace('https://saref.etsi.org/core/')

CURRENT_MODELET = get_current_path() + '/../'
GOT_FILE = '/GoT.ttl'
TBOX_FILE = '/TBox.ttl'
TBOX2_FILE = '/TBox2.ttl'
OSM_WIKI_URL = 'https://wiki.openstreetmap.org/w/api.php'
TAGINFO_API_V4 = "https://taginfo.openstreetmap.org/api/4"

###########################

def init_piirrite_graph() -> Graph:
    piirrite_graph = Graph()
    piirrite_graph.bind('piirrite', piirrite)
    piirrite_graph.bind('piirritev', piirritev)
    piirrite_graph.bind('owl', OWL)
    piirrite_graph.bind('rdf', RDF)
    piirrite_graph.bind('rdfs', RDFS)
    piirrite_graph.bind('xsd', XSD)
    piirrite_graph.bind('saref', saref)
    piirrite_graph.bind('piirrite', piirrite)

    add_SpatialPoint_to_piirrite(piirrite_graph)
    add_hasRelatedOsmTag_to_piirrite(piirrite_graph)
    add_isOsmTagRelatedTo_to_piirrite(piirrite_graph)
    add_osmId_to_piirrite(piirrite_graph)
    add_OsmEntity_to_piirrite(piirrite_graph)

    return piirrite_graph

def init_piirritev_graph() -> Graph:
    piirritev_graph = Graph()
    piirritev_graph.bind('piirrite', piirrite)
    piirritev_graph.bind('piirritev', piirritev)
    piirritev_graph.bind('owl', OWL)
    piirritev_graph.bind('skos', SKOS)
    piirritev_graph.bind('saref', saref)

    return piirritev_graph

def init_piirrite2_graph() -> Graph:
    piirrite_graph = Graph()
    piirrite_graph.bind('piirrite', piirrite)
    piirrite_graph.bind('piirritev', piirritev)
    piirrite_graph.bind('owl', OWL)
    piirrite_graph.bind('rdf', RDF)
    piirrite_graph.bind('rdfs', RDFS)
    piirrite_graph.bind('xsd', XSD)
    piirrite_graph.bind('saref', saref)
    piirrite_graph.bind('piirrite', piirrite)

    return piirrite_graph

def add_SpatialPoint_to_piirrite(piirrite_graph:Graph) -> None:
    SpatialPoint_URI = piirrite.SpatialPoint
    piirrite_graph.add((SpatialPoint_URI, RDF.type, OWL.Class))
    piirrite_graph.add((SpatialPoint_URI, RDFS.subClassOf, geo.Feature))
    piirrite_graph.add((SpatialPoint_URI, RDFS.subClassOf, saref.FeatureOfInterest))
    piirrite_graph.add((SpatialPoint_URI, RDFS.label, Literal('Spatial point', lang = 'en')))
    piirrite_graph.add((SpatialPoint_URI, RDFS.label, Literal('Point spatial', lang = 'fr')))
    piirrite_graph.add((SpatialPoint_URI,
                     RDFS.comment,
                     Literal('A point located in a geographic space and possibly contextualized by properties.',
                             lang = 'en')))
    piirrite_graph.add((SpatialPoint_URI,
                     RDFS.comment,
                     Literal('Un point localisé dans un espace géographique et possiblement contextualisé par des propriétés.',
                             lang = 'fr')))

def add_hasRelatedOsmTag_to_piirrite(piirrite_graph:Graph) -> None:
    hasRelatedOsmTag_URI = piirrite.hasRelatedOsmTag
    piirrite_graph.add((hasRelatedOsmTag_URI, RDF.type, OWL.ObjectProperty))
    piirrite_graph.add((hasRelatedOsmTag_URI, RDFS.label, Literal('has related OSM tag', lang = 'en')))
    piirrite_graph.add((hasRelatedOsmTag_URI, RDFS.label, Literal('a une étiquette OSM liée', lang = 'fr')))
    piirrite_graph.add((hasRelatedOsmTag_URI,
                     RDFS.comment,
                     Literal('Links an OSM concept to an OSM tag used in combination.',
                             lang = 'en')))
    piirrite_graph.add((hasRelatedOsmTag_URI,
                     RDFS.comment,
                     Literal('Lie un concept OSM à une étiquette OSM utilisée en combinaison.',
                             lang = 'fr')))
    piirrite_graph.add((hasRelatedOsmTag_URI, RDFS.domain, piirrite.OsmEntity))
    piirrite_graph.add((hasRelatedOsmTag_URI, OWL.inverseOf, piirrite.isOsmTagRelatedTo))

def add_isOsmTagRelatedTo_to_piirrite(piirrite_graph:Graph) -> None:
    isOsmTagRelatedTo_URI = piirrite.isOsmTagRelatedTo
    piirrite_graph.add((isOsmTagRelatedTo_URI, RDF.type, OWL.ObjectProperty))
    piirrite_graph.add((isOsmTagRelatedTo_URI, RDFS.label, Literal('is an OSM tag related to', lang = 'en')))
    piirrite_graph.add((isOsmTagRelatedTo_URI, RDFS.label, Literal('est une étiquette OSM liée à', lang = 'fr')))
    piirrite_graph.add((isOsmTagRelatedTo_URI,
                     RDFS.comment,
                     Literal('Links an OSM tag to the OSM concept it is used in combination with.',
                             lang = 'en')))
    piirrite_graph.add((isOsmTagRelatedTo_URI,
                     RDFS.comment,
                     Literal('Lie une étiquette OSM au concept OSM avec lequel elle est utilisée.',
                             lang = 'fr')))
    piirrite_graph.add((isOsmTagRelatedTo_URI, RDFS.range, piirrite.OsmEntity))
    piirrite_graph.add((isOsmTagRelatedTo_URI, OWL.inverseOf, piirrite.hasRelatedOsmTag))
    
def add_osmId_to_piirrite(piirrite_graph:Graph) -> None:
    osmId_URI = piirrite.osmId
    piirrite_graph.add((osmId_URI, RDF.type, OWL.DatatypeProperty))
    piirrite_graph.add((osmId_URI, RDFS.label, Literal('has OSM id', lang = 'en')))
    piirrite_graph.add((osmId_URI, RDFS.label, Literal('a l\'id OSM', lang = 'fr')))
    piirrite_graph.add((osmId_URI,
                     RDFS.comment,
                     Literal(
                         'Links an OSM concept to its OSM machine-readable id.',
                         lang = 'en')))
    piirrite_graph.add((osmId_URI,
                     RDFS.comment,
                     Literal(
                         'Lie un concept OSM à son id OSM machine-lisible.',
                         lang = 'fr')))
    piirrite_graph.add((osmId_URI, RDFS.domain, piirrite.OsmEntity))
    piirrite_graph.add((osmId_URI, RDFS.range, XSD.string))

def add_OsmEntity_to_piirrite(piirrite_graph:Graph) -> None:
    OsmEntity_URI = piirrite.OsmEntity
    piirrite_graph.add((OsmEntity_URI, RDF.type, OWL.Class))
    piirrite_graph.add((OsmEntity_URI, RDFS.label, Literal('OSM entity', lang = 'en')))
    piirrite_graph.add((OsmEntity_URI, RDFS.label, Literal('Entité OSM', lang = 'fr')))
    piirrite_graph.add((OsmEntity_URI,
                     RDFS.comment,
                     Literal('An OSM entity used to contextualize a spatial point.',
                             lang = 'en')))
    piirrite_graph.add((OsmEntity_URI,
                     RDFS.comment,
                     Literal('Une entité OSM utilisée pour contextualiser un point spatial.',
                             lang = 'fr')))

def add_OsmConceptScheme_to_piirritev(piirritev_graph:Graph, osm_key:str, description:str) -> None:
    OsmConceptScheme_URI = piirritev[f'Osm{snake_to_camel(osm_key)}']
    piirritev_graph.add((OsmConceptScheme_URI, RDF.type, SKOS.ConceptScheme))
    piirritev_graph.add((OsmConceptScheme_URI,
                      SKOS.prefLabel,
                      Literal(f'{snake_to_natural(osm_key, True)}, types', lang = 'en')))
    piirritev_graph.add((OsmConceptScheme_URI, SKOS.definition, Literal(description, lang = 'en')))
    piirritev_graph.add((OsmConceptScheme_URI, piirrite.osmId, Literal(osm_key)))

def add_OsmConcept_to_piirritev(piirritev_graph:Graph, osm_key:str, value:str, description:str) -> None:
    if value == 'any':
        return
    OsmConcept_URI = piirritev[f'Osm{snake_to_camel(osm_key.replace(' ', '_'))}{snake_to_camel(value)}']
    piirritev_graph.add((OsmConcept_URI, RDF.type, SKOS.Concept))
    piirritev_graph.add((OsmConcept_URI, RDFS.subClassOf, piirrite.OsmEntity))
    piirritev_graph.add((OsmConcept_URI,
                      SKOS.prefLabel,
                      Literal(snake_to_natural(value, True), lang = 'en')))
    piirritev_graph.add((OsmConcept_URI, SKOS.definition, Literal(description, lang = 'en')))
    piirritev_graph.add((OsmConcept_URI, SKOS.inScheme, piirritev[f'Osm{snake_to_camel(osm_key)}']))
    piirritev_graph.add((OsmConcept_URI, piirrite.osmId, Literal(value)))

def add_hasOsmTuic_to_piirrite2(piirritev_graph:Graph, piirrite2_graph:Graph,
                             osm_key:str, value:str, tuic:str, description:str) -> None:
    if value == 'any':
        return
    value_camel = snake_to_camel(value)
    if snake_to_camel(tuic) != value_camel:
        tuic_camel = snake_to_camel(tuic)
    else:
        tuic_camel = 'Type'
    hasOsmTuic_URI = piirrite[f'hasOsm{value_camel}{tuic_camel}']
    piirrite2_graph.add((hasOsmTuic_URI, RDF.type, OWL.DatatypeProperty))
    piirrite2_graph.add((hasOsmTuic_URI, RDFS.subPropertyOf, saref.hasValue))
    piirrite2_graph.add((hasOsmTuic_URI,
                      RDFS.label,
                      Literal(snake_to_natural(tuic, True),
                              lang = 'en')))
    # piirrite2_graph.add((hasOsmTuic_URI, RDFS.comment, Literal(description, lang = 'en')))
    piirrite2_graph.add((hasOsmTuic_URI, RDFS.domain, saref.Property))
    piirrite2_graph.add((hasOsmTuic_URI, RDFS.range, RDFS.Literal))
    piirrite2_graph.add((hasOsmTuic_URI, piirrite.osmId, Literal(tuic)))
    piirrite2_graph.add((hasOsmTuic_URI, piirrite.isOsmTagRelatedTo, piirritev[f'Osm{snake_to_camel(osm_key)}{value_camel}']))
    piirritev_graph.add((piirritev[f'Osm{snake_to_camel(osm_key)}{value_camel}'], piirrite.hasRelatedOsmTag, hasOsmTuic_URI))

###########################

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
        'vending', 'historic', 'military', 'telecom'
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
        on_elements.append("SpatialPoint")
    if _truthy_on_element(_extract_template_param(block, "onWay")):
        on_elements.append("SpatialSegment")
    if _truthy_on_element(_extract_template_param(block, "onArea")):
        on_elements.append("SpatialRegion")

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

                try:
                    vals = should_be_concept(fut.result())
                except Exception:
                    vals = []

                osm_keys_values[k_norm] = vals
                if vals:
                    n_osm_keys_values_explicit += 1

        print(f'{n_osm_keys_desc}/{len(osm_keys)} clés ont une description.')
        print(f'{n_osm_keys_ranges_valid}/{len(osm_keys)} clés ont au moins une range valide.')
        print(f'{n_osm_keys_values_explicit}/{len(osm_keys)} clés ont au moins une valeur explicite avec au moins 10 000 occurences.')

        return osm_keys_descriptions, osm_keys_ranges, osm_keys_values

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

def _make_retrying_session(
    *,
    total_retries: int = 6,
    backoff_factor: float = 0.8,
    pool_maxsize: int = 32,
) -> requests.Session:
    """
    Session requests robuste (retries sur 429/5xx + erreurs réseau).
    """
    s = requests.Session()
    s.headers.update({
        # Important: certains serveurs coupent plus souvent sans User-Agent clair
        "User-Agent": "osm-wiki-fetch/1.0 (contact: you@example.com)",
        "Accept": "application/json",
    })

    retry = Retry(
        total=total_retries,
        connect=total_retries,
        read=total_retries,
        status=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=pool_maxsize, pool_maxsize=pool_maxsize)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s

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

def use_osm_wiki_to_fill_in_graphs(piirritev_graph:Graph,
                                   piirrite2_graph:Graph) -> None:
    osm_raw_keys = get_osm_keys_from_wiki()
    osm_keys = filter_osm_keys(osm_raw_keys)
    osm_keys_descriptions, osm_keys_ranges, osm_keys_values = get_osm_keys_datas(osm_keys)
    osm_keys_values_descriptions, osm_keys_values_tuics = get_osm_values_datas(osm_keys_values)

    for osm_key, key_description in osm_keys_descriptions.items():
        add_OsmConceptScheme_to_piirritev(piirritev_graph, osm_key, key_description)
        for value, value_description in osm_keys_values_descriptions[osm_key].items():
            add_OsmConcept_to_piirritev(piirritev_graph, osm_key, value, value_description)
            if value in osm_keys_values_tuics[osm_key].keys():
                for tuic in osm_keys_values_tuics[osm_key][value]:
                    add_hasOsmTuic_to_piirrite2(piirritev_graph, piirrite2_graph,
                                             osm_key, value, tuic, '')

def main():
    piirrite_graph = init_piirrite_graph()
    piirritev_graph = init_piirritev_graph()
    piirrite2_graph = init_piirrite2_graph()
    use_osm_wiki_to_fill_in_graphs(piirritev_graph, piirrite2_graph)
    piirrite_graph.serialize(CURRENT_MODELET + TBOX_FILE, 'turtle')
    piirritev_graph.serialize(CURRENT_MODELET + GOT_FILE, 'turtle')
    piirrite2_graph.serialize(CURRENT_MODELET + TBOX2_FILE, 'turtle')

    print(f'Ontologie et glossaire initialisés, remplis et sauvegardés avec succès.')

if __name__ == '__main__':
    main()
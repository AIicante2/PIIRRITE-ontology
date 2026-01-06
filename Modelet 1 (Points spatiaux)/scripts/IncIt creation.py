import re
import requests
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import SKOS, RDF, RDFS, OWL, XSD
from utilities.utilities import snake_to_camel, snake_to_natural, get_current_path, display_progress_bar

incit = Namespace('http://incit.univ-lyon1.fr/ontology/core#')
incitv = Namespace('http://incit.univ-lyon1.fr/vocabulary#')
osmkey = Namespace('https://www.openstreetmap.org/wiki/Key:')
geo = Namespace('http://www.opengis.net/ont/geosparql#')
saref = Namespace('https://saref.etsi.org/core/')

CURRENT_MODELET = get_current_path() + '/../'
INCIT_CREATION_FILE = '/script/IncIt creation.py'
INCIT_INSTANCIATION_FILE = '/script/IncIt creation.py'
GOT_FILE = '/GoT.ttl'
TBOX_FILE = '/TBox.ttl'
TBOX2_FILE = '/TBox2.ttl'
OSM_WIKI_URL = 'https://wiki.openstreetmap.org/w/api.php'

###########################

def init_incit_graph() -> Graph:
    incit_graph = Graph()
    incit_graph.bind('incit', incit)
    incit_graph.bind('incitv', incitv)
    incit_graph.bind('owl', OWL)
    incit_graph.bind('rdf', RDF)
    incit_graph.bind('rdfs', RDFS)
    incit_graph.bind('xsd', XSD)
    incit_graph.bind('saref', saref)
    incit_graph.bind('incit', incit)

    add_SpatialPoint_to_incit(incit_graph)
    add_hasRelatedOsmTag_to_incit(incit_graph)
    add_isOsmTagRelatedTo_to_incit(incit_graph)
    add_osmId_to_incit(incit_graph)
    add_OsmEntity_to_incit(incit_graph)

    return incit_graph

def init_incitv_graph() -> Graph:
    incitv_graph = Graph()
    incitv_graph.bind('incit', incit)
    incitv_graph.bind('incitv', incitv)
    incitv_graph.bind('owl', OWL)
    incitv_graph.bind('skos', SKOS)
    incitv_graph.bind('saref', saref)

    return incitv_graph

def init_incit2_graph() -> Graph:
    incit_graph = Graph()
    incit_graph.bind('incit', incit)
    incit_graph.bind('incitv', incitv)
    incit_graph.bind('owl', OWL)
    incit_graph.bind('rdf', RDF)
    incit_graph.bind('rdfs', RDFS)
    incit_graph.bind('xsd', XSD)
    incit_graph.bind('saref', saref)
    incit_graph.bind('incit', incit)

    return incit_graph

def add_SpatialPoint_to_incit(incit_graph:Graph) -> None:
    SpatialPoint_URI = incit.SpatialPoint
    incit_graph.add((SpatialPoint_URI, RDF.type, OWL.Class))
    incit_graph.add((SpatialPoint_URI, RDFS.subClassOf, geo.Feature))
    incit_graph.add((SpatialPoint_URI, RDFS.subClassOf, saref.FeatureOfInterest))
    incit_graph.add((SpatialPoint_URI, RDFS.label, Literal('Spatial point', lang = 'en')))
    incit_graph.add((SpatialPoint_URI, RDFS.label, Literal('Point spatial', lang = 'fr')))
    incit_graph.add((SpatialPoint_URI,
                     RDFS.comment,
                     Literal('A point located in a geographic space and possibly contextualized by properties.',
                             lang = 'en')))
    incit_graph.add((SpatialPoint_URI,
                     RDFS.comment,
                     Literal('Un point localisé dans un espace géographique et possiblement contextualisé par des propriétés.',
                             lang = 'fr')))

def add_hasRelatedOsmTag_to_incit(incit_graph:Graph) -> None:
    hasRelatedOsmTag_URI = incit.hasRelatedOsmTag
    incit_graph.add((hasRelatedOsmTag_URI, RDF.type, OWL.ObjectProperty))
    incit_graph.add((hasRelatedOsmTag_URI, RDFS.label, Literal('has related OSM tag', lang = 'en')))
    incit_graph.add((hasRelatedOsmTag_URI, RDFS.label, Literal('a une étiquette OSM liée', lang = 'fr')))
    incit_graph.add((hasRelatedOsmTag_URI,
                     RDFS.comment,
                     Literal('Links an OSM concept to an OSM tag used in combination.',
                             lang = 'en')))
    incit_graph.add((hasRelatedOsmTag_URI,
                     RDFS.comment,
                     Literal('Lie un concept OSM à une étiquette OSM utilisée en combinaison.',
                             lang = 'fr')))
    incit_graph.add((hasRelatedOsmTag_URI, RDFS.domain, incit.OsmEntity))
    incit_graph.add((hasRelatedOsmTag_URI, OWL.inverseOf, incit.isOsmTagRelatedTo))

def add_isOsmTagRelatedTo_to_incit(incit_graph:Graph) -> None:
    isOsmTagRelatedTo_URI = incit.isOsmTagRelatedTo
    incit_graph.add((isOsmTagRelatedTo_URI, RDF.type, OWL.ObjectProperty))
    incit_graph.add((isOsmTagRelatedTo_URI, RDFS.label, Literal('is an OSM tag related to', lang = 'en')))
    incit_graph.add((isOsmTagRelatedTo_URI, RDFS.label, Literal('est une étiquette OSM liée à', lang = 'fr')))
    incit_graph.add((isOsmTagRelatedTo_URI,
                     RDFS.comment,
                     Literal('Links an OSM tag to the OSM concept it is used in combination with.',
                             lang = 'en')))
    incit_graph.add((isOsmTagRelatedTo_URI,
                     RDFS.comment,
                     Literal('Lie une étiquette OSM au concept OSM avec lequel elle est utilisée.',
                             lang = 'fr')))
    incit_graph.add((isOsmTagRelatedTo_URI, RDFS.range, incit.OsmEntity))
    incit_graph.add((isOsmTagRelatedTo_URI, OWL.inverseOf, incit.hasRelatedOsmTag))
    
def add_osmId_to_incit(incit_graph:Graph) -> None:
    osmId_URI = incit.osmId
    incit_graph.add((osmId_URI, RDF.type, OWL.DatatypeProperty))
    incit_graph.add((osmId_URI, RDFS.label, Literal('has OSM id', lang = 'en')))
    incit_graph.add((osmId_URI, RDFS.label, Literal('a l\'id OSM', lang = 'fr')))
    incit_graph.add((osmId_URI,
                     RDFS.comment,
                     Literal(
                         'Links an OSM concept to its OSM machine-readable id.',
                         lang = 'en')))
    incit_graph.add((osmId_URI,
                     RDFS.comment,
                     Literal(
                         'Lie un concept OSM à son id OSM machine-lisible.',
                         lang = 'fr')))
    incit_graph.add((osmId_URI, RDFS.domain, incit.OsmEntity))
    incit_graph.add((osmId_URI, RDFS.range, XSD.string))

def add_OsmEntity_to_incit(incit_graph:Graph) -> None:
    OsmEntity_URI = incit.OsmEntity
    incit_graph.add((OsmEntity_URI, RDF.type, OWL.Class))
    incit_graph.add((OsmEntity_URI, RDFS.label, Literal('OSM entity', lang = 'en')))
    incit_graph.add((OsmEntity_URI, RDFS.label, Literal('Entité OSM', lang = 'fr')))
    incit_graph.add((OsmEntity_URI,
                     RDFS.comment,
                     Literal('An OSM entity used to contextualize a spatial point.',
                             lang = 'en')))
    incit_graph.add((OsmEntity_URI,
                     RDFS.comment,
                     Literal('Une entité OSM utilisée pour contextualiser un point spatial.',
                             lang = 'fr')))

def add_OsmConceptScheme_to_incitv(incitv_graph:Graph, osm_key:str, description:str) -> None:
    OsmConceptScheme_URI = incitv[f'Osm{snake_to_camel(osm_key)}']
    incitv_graph.add((OsmConceptScheme_URI, RDF.type, SKOS.ConceptScheme))
    incitv_graph.add((OsmConceptScheme_URI,
                      SKOS.prefLabel,
                      Literal(f'{snake_to_natural(osm_key, True)}, types', lang = 'en')))
    incitv_graph.add((OsmConceptScheme_URI, SKOS.definition, Literal(description, lang = 'en')))
    incitv_graph.add((OsmConceptScheme_URI, incit.osmId, Literal(osm_key)))

def add_OsmConcept_to_incitv(incitv_graph:Graph, osm_key:str, value:str, description:str) -> None:
    OsmConcept_URI = incitv[f'Osm{snake_to_camel(osm_key)}{snake_to_camel(value)}']
    incitv_graph.add((OsmConcept_URI, RDF.type, SKOS.Concept))
    incitv_graph.add((OsmConcept_URI, RDFS.subClassOf, incit.OsmEntity))
    incitv_graph.add((OsmConcept_URI,
                      SKOS.prefLabel,
                      Literal(snake_to_natural(value, True), lang = 'en')))
    incitv_graph.add((OsmConcept_URI, SKOS.definition, Literal(description, lang = 'en')))
    incitv_graph.add((OsmConcept_URI, SKOS.inScheme, incitv[f'Osm{snake_to_camel(osm_key)}']))
    incitv_graph.add((OsmConcept_URI, incit.osmId, Literal(value)))

def add_hasOsmTuic_to_incit2(incitv_graph:Graph, incit2_graph:Graph,
                             osm_key:str, value:str, tuic:str, description:str) -> None:
    value_camel = snake_to_camel(value)
    if snake_to_camel(tuic) != value_camel:
        tuic_camel = snake_to_camel(tuic)
    else:
        tuic_camel = 'Type'
    hasOsmTuic_URI = incit[f'hasOsm{value_camel}{tuic_camel}']
    incit2_graph.add((hasOsmTuic_URI, RDF.type, OWL.DatatypeProperty))
    incit2_graph.add((hasOsmTuic_URI, RDFS.subPropertyOf, saref.hasValue))
    incit2_graph.add((hasOsmTuic_URI,
                      RDFS.label,
                      Literal(snake_to_natural(tuic, True),
                              lang = 'en')))
    incit2_graph.add((hasOsmTuic_URI, RDFS.comment, Literal(description, lang = 'en')))
    incit2_graph.add((hasOsmTuic_URI, RDFS.domain, saref.Property))
    incit2_graph.add((hasOsmTuic_URI, RDFS.range, RDFS.Literal))
    incit2_graph.add((hasOsmTuic_URI, incit.osmId, Literal(tuic)))
    incit2_graph.add((hasOsmTuic_URI, incit.isOsmTagRelatedTo, incitv[f'Osm{snake_to_camel(osm_key)}{value_camel}']))
    incitv_graph.add((incitv[f'Osm{snake_to_camel(osm_key)}{value_camel}'], incit.hasRelatedOsmTag, hasOsmTuic_URI))

###########################

def get_osm_keys_from_wiki() -> list[str]:
    print('Récupération des clés depuis le wiki…')
    osm_keys = []
    params = {
        'action': 'query',
        'list': 'allpages',
        'apnamespace': 10,
        'apprefix': 'Map_Features:',
        'format': 'json',
        'aplimit': 'max'
    }

    while True:
        try:
            response = requests.get(OSM_WIKI_URL, params = params)
        except Exception:
            return []
        raw_keys = response.json()
        osm_keys.extend([
            raw_key_page['title'].replace('Template:Map Features:', '')
            for raw_key_page in raw_keys.get('query', {}).get('allpages', [])
            if not raw_key_page['title'].endswith('/doc')
        ])

        if 'continue' not in raw_keys:
            break
        params.update(raw_keys['continue'])

    print(f'{len(osm_keys)} clées récupérées.')
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

def filter_osm_keys(osm_raw_keys:list[str]) -> list[str]:
    print('Filtrage des clés pertinentes…')
    osm_keys = [
        osm_raw_key for osm_raw_key in osm_raw_keys
        if not is_excluded_key(osm_raw_key)
    ]

    print(f'{len(osm_keys)}/{len(osm_raw_keys)} clées ont passé le filtre.')
    return osm_keys

def get_osm_keys_wikitexts(osm_keys:list[str]) -> dict[str, str]:
    print('Récupération du contenu wiki de chaque clé…')
    osm_keys_wikitexts = {}

    for osm_key in osm_keys:
        wikitext = get_key_wikitext_from_wiki(osm_key)
        if wikitext:
            osm_keys_wikitexts[osm_key] = wikitext
    
    print(f'{len(osm_keys_wikitexts)}/{len(osm_keys)} wikitexts récupérés.')
    return osm_keys_wikitexts

def get_key_wikitext_from_wiki(osm_key:str) -> str:
    params = {
        'action': 'parse',
        'page': f'Template:Map_Features:{osm_key}',
        'format': 'json',
        'prop': 'wikitext'
    }
    try:
        response = requests.get(OSM_WIKI_URL, params = params)
        return response.json().get('parse', {}).get('wikitext', {}).get('*', '')
    except Exception:
        return ''

def extract_osm_key_description_from_wikitext(wikitext: str) -> str | None:
    pattern = r'\{\{\{description\|(.*?)\}\}\}'
    match = re.search(pattern, wikitext, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ''

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

def build_value_patterns(key: str) -> list[str]:
    return [r'\{\{\s*valuelink\s*\|\s*' + key + r'\s*\|\s*([a-z0-9_]+)\s*\}\}',
            r'\{\{Taglist\s*\|\s*tags\s*=\s*' + key + r'=([a-z0-9_, ]+)',
            r'\[\[\s*\{{\s*LL\s*\|\s*1\s*=\s*Tag:' + key + r'=([a-z0-9_]+)\s*\}\}\s*\|\s*[^\|]+\s*\]\]',
            r'\|\{\{\s*tag\s*\|\s*([a-z0-9_]+)\s*\}\}',
            r'\[\[\s*\{\{\{.*?\|\s*\{{\s*LL\s*\|\s*1\s*=\s*Tag:' + key + r'=([a-z0-9_]+)\s*\}\}\s*\}\}\}\s*\|\s*([a-z0-9_]+)\s*\]\]',
            r'\{\{\s*TagValue\s*\|\s*' + key + r'\s*\|\s*([a-z0-9_]+)\s*\}\}',
            r'\[\[\s*\{\{\{.*?\|\s*Tag:' + key + r'=([a-z0-9_]+)\s*\}\}\}\s*\|\s*([a-z0-9_]+)\s*\]\]'
    ]

def extract_osm_values_from_wikitext(osm_key:str, wikitext:str) -> list[str]:
    values = list()
    values_patterns = build_value_patterns(osm_key)

    # {{valuelink|key|subkey}}
    values.extend(match.group(1) for match in re.compile(values_patterns[0]).finditer(wikitext))
    # {{Taglist|tags=key=value1,value2,...}}
    for match in re.compile(values_patterns[1]).finditer(wikitext):
        tag_values = match.group(1).replace(' ', '').split(',')
        values.extend(tag_values)
    # [[Tag:key=value|value]]
    values.extend(match.group(1) for match in re.compile(values_patterns[2]).finditer(wikitext))
    # {{tag|key|value}}
    values.extend(match.group(1) for match in re.compile(values_patterns[3]).finditer(wikitext))
    # [[{{{value:value|{{LL|1=Tag:key=value}}}}} | value]]
    values.extend(match.group(1) for match in re.compile(values_patterns[4]).finditer(wikitext))
    # {{TagValue|key|value}}
    values.extend(match.group(1) for match in re.compile(values_patterns[5]).finditer(wikitext))
    # [[{{{value:value|Tag:key=value}}} | value]]
    values.extend(match.group(1) for match in re.compile(values_patterns[6]).finditer(wikitext))

    while '' in values:
        values.remove('')
    while ' ' in values:
        values.remove(' ')
    while '*' in values:
        values.remove('*')
    while None in values:
        values.remove(None)

    return list(values)

def extract_osm_value_description_from_wikitext(value:str, wikitext:str) -> str:
    pattern = rf'\{{\{{\{{\s*{re.escape(value)}:desc\|(.*?)\}}\}}\}}'
    match = re.search(pattern, wikitext, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ''

def parse_osm_keys_wikitexts(osm_keys_wikitexts:dict[str, str]) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    print('Récupération des descriptions et des valeurs possibles…')
    osm_keys_descriptions = {}
    osm_keys_values = {}
    nb_descriptions = 0
    nb_at_least_one_value = 0

    for osm_key, wikitext in osm_keys_wikitexts.items():
        description = extract_osm_key_description_from_wikitext(wikitext)
        if description:
            osm_keys_descriptions[osm_key] = clean_osm_description(description)
            nb_descriptions += 1

        values = extract_osm_values_from_wikitext(osm_key, wikitext)
        values_descriptions = {}
        if values:
            for value in values:
                value_description = extract_osm_value_description_from_wikitext(value, wikitext)
                values_descriptions[value] = clean_osm_description(value_description)
            osm_keys_values[osm_key] = values_descriptions
            nb_at_least_one_value += 1
    
    print(f'{nb_descriptions}/{len(osm_keys_wikitexts)} clés ont une description.')
    print(f'{nb_at_least_one_value}/{len(osm_keys_wikitexts)} clés ont au moins une valeur possible.')
    return osm_keys_descriptions, osm_keys_values

def get_value_wikitext_from_wiki(osm_key:str, value:str) -> str:
    params = {
        'action': 'parse',
        'page': f'Tag:{osm_key}={value}',
        'format': 'json',
        'prop': 'wikitext'
    }
    try:
        response = requests.get(OSM_WIKI_URL, params = params)
        return response.json().get('parse', {}).get('wikitext', {}).get('*', '')
    except Exception:
        return ''

def get_osm_values_wikitexts(osm_values_descriptions:dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    print('Récupération du contenu wiki de chaque valeur…')
    osm_values_wikitexts = {}
    
    count = 0
    nb_valeurs = 0
    for osm_key in osm_values_descriptions.keys():
        nb_valeurs += len(osm_values_descriptions[osm_key])
    for osm_key, values in osm_values_descriptions.items():
        osm_values_wikitexts[osm_key] = {}
        for value in values.keys():
            wikitext = get_value_wikitext_from_wiki(osm_key, value)
            if wikitext:
                osm_values_wikitexts[osm_key][value] = wikitext
            count += 1
            display_progress_bar(count, nb_valeurs, message = f'des {nb_valeurs} valeurs traitées…')
    
    return osm_values_wikitexts

def extract_osm_tuic_from_wikitext(osm_key:str, value:str, wikitext:str) -> dict[str, str]:
    pattern = r'\|\s*\{\{\s*Tag\|([^\}]+)\}\}\s*\|\s*([^\|]+)'
    matches = re.findall(pattern, wikitext)
    tuics_descriptions = {}
    for tuic, description in matches:

        # nettoyage du tuic
        # Si ce qu'il y a avant le premier | est {osm_key}, c'est la désignation de la sous-clé principale
        # -> on passe
        if tuic.startswith(str(osm_key) + '|'):
            continue
        if len(re.split(r'[:=]', tuic)) > 1:
            tuic = re.split(r'[:=]', tuic)[1]
        while '|' in tuic:
            if str(tuic.split('|')[0]) == str(value):
                tuic = tuic.split('|')[1]
            else:
                tuic = re.sub(r'\|.*$', '', tuic)
        tuic = tuic.replace("'", '').replace(' ', '').strip()

        if tuic in ['', '*', 'yellow/gray/..']:
            continue
        
        # nettoyage de la description
        if '{' in tuic:
            description = ''
        description = description.strip()
        
        if tuic not in tuics_descriptions.keys():
            tuics_descriptions[tuic] = description
    
    return tuics_descriptions

def parse_osm_values_wikitexts(osm_values_wikitexts:dict[str, dict[str, str]]) -> dict[str, dict[str, dict[str, str]]]:
    print('Récupération des étiquettes utilisées en combinaison avec des valeurs…')
    osm_values_tuics = {}
    nb_at_least_one_tuic = 0
    nb_values = 0
    
    for osm_key, values in osm_values_wikitexts.items():
        osm_values_tuics[osm_key] = {}
        nb_values += len(values.items())
        for value, wikitext in values.items():
            osm_values_tuics[osm_key][value] = extract_osm_tuic_from_wikitext(osm_key, value, wikitext)
            if osm_values_tuics[osm_key][value] != {}:
                nb_at_least_one_tuic += 1
    
    print(f'{nb_at_least_one_tuic}/{nb_values} valeurs utilisent au moins une étiquette en combinaison.')
    return osm_values_tuics

def use_osm_wiki_to_fill_in_graphs(incit_graph:Graph,
                                   incitv_graph:Graph,
                                   incit2_graph:Graph) -> None:
    osm_raw_keys = get_osm_keys_from_wiki()
    osm_keys = filter_osm_keys(osm_raw_keys)
    osm_keys_wikitexts = get_osm_keys_wikitexts(osm_keys)
    osm_keys_descriptions, osm_values_descriptions = parse_osm_keys_wikitexts(osm_keys_wikitexts)
    osm_values_wikitexts = get_osm_values_wikitexts(osm_values_descriptions)
    osm_values_tuics = parse_osm_values_wikitexts(osm_values_wikitexts)

    for osm_key, key_description in osm_keys_descriptions.items():
        add_OsmConceptScheme_to_incitv(incitv_graph, osm_key, key_description)
        for value, value_description in osm_values_descriptions[osm_key].items():
            add_OsmConcept_to_incitv(incitv_graph, osm_key, value, value_description)
            if value in osm_values_tuics[osm_key].keys():
                for tuic, tuic_description in osm_values_tuics[osm_key][value].items():
                    add_hasOsmTuic_to_incit2(incitv_graph, incit2_graph,
                                             osm_key, value, tuic, tuic_description)

def main():
    incit_graph = init_incit_graph()
    incitv_graph = init_incitv_graph()
    incit2_graph = init_incit2_graph()
    use_osm_wiki_to_fill_in_graphs(incit_graph, incitv_graph, incit2_graph)
    incit_graph.serialize(CURRENT_MODELET + TBOX_FILE, 'turtle')
    incitv_graph.serialize(CURRENT_MODELET + GOT_FILE, 'turtle')
    incit2_graph.serialize(CURRENT_MODELET + TBOX2_FILE, 'turtle')

    print(f'Ontologie et glossaire initialisés, remplis et sauvegardés avec succès.')

if __name__ == '__main__':
    main()
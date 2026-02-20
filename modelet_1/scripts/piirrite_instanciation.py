from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.namespace import OWL, RDF, RDFS, XSD, SKOS
from utilities.utilities import *
from modelet_1.scripts.piirrite_creation import should_be_concept

piirrite = Namespace('http://piirrite.univ-lyon1.fr/ontology/core#')
piirritev = Namespace('http://piirrite.univ-lyon1.fr/vocabulary#')
osm = Namespace('https://www.openstreetmap.org/')
osmnode = Namespace('https://www.openstreetmap.org/node/')
saref = Namespace('https://saref.etsi.org/core/')
geo = Namespace('http://www.opengis.net/ont/geosparql#')
geom = Namespace('https://osm2rdf.cs.uni-freiburg.de/rdf/geom#')

raw_data_file = get_current_path() + '/osm_data_natif.ttl'
GoT_file = get_current_path() + '/../GoT.ttl'
TBox_file = get_current_path() + '/../TBox.ttl'
TBox2_file = get_current_path() + '/../TBox2.ttl'
ABox_file = get_current_path() + '/../ABox.ttl'

def init_piirrite_graph() -> Graph:
    piirrite_graph = Graph()
    with open(TBox_file, 'r', encoding = 'utf-8') as TBox_file_content:
        piirrite_graph.parse(data = TBox_file_content.read(), format = 'turtle')
    with open(TBox2_file, 'r', encoding = 'utf-8') as TBox2_file_content:
        piirrite_graph.parse(data = TBox2_file_content.read(), format = 'turtle')
    
    return piirrite_graph

def init_piirritev_graph() -> Graph:
    piirritev_graph = Graph()
    with open(GoT_file, 'r', encoding = 'utf-8') as GoT_file_content:
        piirritev_graph.parse(data = GoT_file_content.read(), format = 'turtle')
    
    return piirritev_graph

def init_piirrited_graph() -> Graph:
    piirrited_graph = Graph()
    piirrited_graph.bind('piirrite', piirrite)
    piirrited_graph.bind('piirritev', piirritev)
    piirrited_graph.bind('rdfs', RDFS)
    piirrited_graph.bind('xsd', XSD)
    piirrited_graph.bind('osm', osm)
    piirrited_graph.bind('osmnode', osmnode)
    piirrited_graph.bind('geo', geo)
    piirrited_graph.bind('saref', saref)

    return piirrited_graph

def init_osmd_graph() -> Graph:
    print('Récupération des données OSM…')
    osmd_graph = Graph()
    osmd_graph.parse(raw_data_file, 'turtle')
    
    print('Données OSM récupérées.')
    return osmd_graph

def add_geometry_to_SpatialPoint(piirrited_graph:Graph,
                                 osmd_graph:Graph,
                                 SpatialPoint_URI:URIRef,
                                 osm_geometry) -> None:
    geometries_as_WKT = list(osmd_graph.objects(osm_geometry, geo.asWKT))
    if len(geometries_as_WKT) == 1:
        geometry_as_WKT = str(geometries_as_WKT[0])
        geometry = BNode()
        piirrited_graph.add((SpatialPoint_URI, geo.hasGeometry, geometry))
        piirrited_graph.add((geometry, RDF.type, geo.Geometry))
        piirrited_graph.add((geometry,
                        geo.asWKT,
                        Literal(str(geometry_as_WKT), datatype = geo['wktLiteral'])))

def value_datatype(var):
    if isinstance(var, int):
        return XSD.integer
    if isinstance(var, float):
        return XSD.float
    if isinstance(var, bool):
        return XSD.boolean
    return XSD.string

def remove_blank_node_property(g, subject, predicate, rdf_type):
    blank_nodes_to_remove = []
    
    for bn in g.objects(subject, predicate):
        if (bn, RDF.type, rdf_type) in g:
            blank_nodes_to_remove.append(bn)
    
    for bn in blank_nodes_to_remove:
        g.remove((bn, None, None))
        g.remove((subject, predicate, bn))
    
    return len(blank_nodes_to_remove)

def add_context_to_SpatialPoint(osm_node:URIRef,
                                piirrite_graph:Graph, piirritev_graph:Graph, piirrited_graph:Graph, osmd_graph:Graph,
                                SpatialPoint_URI:URIRef, osm_key:str, osm_value:str, unfounds:dict[str, dict[str, int]]) -> dict[str, dict[str, int]]:
    
    # si la valeur n'a pas pour vocation d'être conceptualisée
    # et que ce n'est pas un tuic (voir ci-dessous)
    # en suivant le dictionnaire SKOS, on l'enregistre comme telle
    if len(osm_value.split(' ')) > 1 or not should_be_concept([osm_value]):
        conceptScheme = 'Osm' + snake_to_camel(osm_key)
        if (piirritev[conceptScheme], RDF.type, SKOS.ConceptScheme) in piirritev_graph:
            context = BNode()
            piirrited_graph.add((SpatialPoint_URI, saref.hasProperty, context))
            piirrited_graph.add((context, RDF.type, piirritev[conceptScheme]))
            converted_value = str_to_best_type(osm_value)
            piirrited_graph.add((context, saref.hasValue, Literal(converted_value, datatype = value_datatype(converted_value))))

        return unfounds

    # sinon, on lance le processus de conceptualisation

    # OSM utilise du snake_case et PIIRRITE du CamelCase
    concept = 'Osm' + snake_to_camel(osm_key) + snake_to_camel(osm_value)

    # Si la clé n'est pas dans le vocabulaire, on ne l'ajoute pas
    if (piirritev[concept], RDF.type, SKOS.Concept) not in piirritev_graph:
        if concept not in unfounds['values'].keys():
            unfounds['values'][concept] = 1
        else:
            unfounds['values'][concept] += 1
        return unfounds

    # le tag courant est peut-être voué à être utilisé en combinaison avec un autre
    # tag de la spatialEntity (ex : capacity qui se rapporte à bicycleParking)
    # -- voir l'explication sur les tuic ci-dessous
    # Dans ce cas, il ne faut pas l'enregistrer comme concept à part entière
    #
    # Si c'est le cas, deux possibilités :
    # - soit il a déjà été enregistré comme tel, et pas la peine de continuer
    # - soit il n'a pas déjà été enregistré comme tel, alors on l'enregistre comme
    #   concept à part entière et on le supprimera quand on l'enregistrera comme tel
    #   (lors du traitement du tag auquel il se rapporte) : voir (*) ci-dessous
    for saref_property in piirrited_graph.objects(SpatialPoint_URI, saref.hasProperty):
        for tuic_predicate, _ in piirrited_graph.predicate_objects(saref_property):
            if tuic_predicate not in [RDF.type, saref.hasValue]:
                if str(tuic_predicate).endswith(snake_to_camel(osm_key)):
                    return unfounds

    # on enregistre la propriété contextuelle
    context = BNode()
    piirrited_graph.add((SpatialPoint_URI, saref.hasProperty, context))
    piirrited_graph.add((context, RDF.type, piirritev[concept]))

    # Il faut encore vérifier si des triplets de osmd_graph sont des
    # étiquettes utilisées en combinaison avec le concept
    #
    # Plus de détails : OSM permet à certains tags d'avoir des attributs supplémentaires
    # à travers des "tags used in combination" ("tuic").
    # ex: [amemity=bicycle_parking, capacity="12"]
    # Ici, OSM comprend implicitement que l'attribut "capacity" se rapporte au tag "bicycle_parking"
    # grâce à la logique interne des tuic.
    # PIIRRITE gère ces attributs supplémentaires !
    # Pour cela, il passe par la propriété piirrite:hasRelatedOsmTag
    # ex: piirritev:OsmAmenityBicycleParking a skos:Concept ;
    #         piirrite:hasRelatedOsmTag piirritev:hasOsmBicycleParkingCapacity
    #     osmnode:1 a piirrite:SpatialPoint ;
    #         piirrite:hasAmenity [ a saref:Property ;
    #             rdfs:isDefinedBy piirritev:OsmAmenityBicycleParking ;
    #             piirritev:hasOsmBicycleParkingCapacity '12']

    # Ensemble des propriétés liées au nœud OSM courant
    tuic_candidates = {}
    for p, o in osmd_graph.predicate_objects(osm_node):
        if 'wiki/Key:' in str(p):
            tuic_candidates[str(p).split('wiki/Key:')[-1]] = str(o)
    
    # Ensemble des étiquettes utilisées en combinaison avec le concept PIIRRITEV courant
    possible_tuics = []
    for o in piirritev_graph.objects(piirritev[concept], piirrite.hasRelatedOsmTag):
        osm_name = next(piirrite_graph.objects(URIRef(str(o)), piirrite.osmId, True), None)
        if osm_name:
            possible_tuics.append(str(osm_name))

    for tuic, tuic_value in tuic_candidates.items():
        if tuic in possible_tuics:
            # on a trouvé un tuic !
            tuic_piirritev_name = snake_to_camel(tuic) if tuic != osm_value else 'Type'
            tuic_URI = piirrite['hasOsm' + snake_to_camel(osm_key) + snake_to_camel(osm_value) + tuic_piirritev_name]
            converted_value = str_to_best_type(tuic_value)
            piirrited_graph.add((context, tuic_URI, Literal(converted_value, datatype = value_datatype(converted_value))))

            # (*) si le tuic était déjà enregistré comme concept à part entière,
            # on supprime ce concept
            for property in piirrited_graph.objects(SpatialPoint_URI, saref.hasProperty):
                for property_type in piirrited_graph.objects(property, RDF.type):
                    pt_name = str(property_type).split('#Osm')[1]
                    if pt_name == tuic_piirritev_name:
                        remove_blank_node_property(piirrited_graph,
                                                   SpatialPoint_URI,
                                                   saref.hasProperty,
                                                   property_type)

    return unfounds

def add_SpatialPoint_to_piirrited(osm_node:URIRef,
                               osmd_graph:Graph,
                               piirrite_graph:Graph,
                               piirritev_graph:Graph,
                               piirrited_graph:Graph,
                               unfounds:dict[str, dict[str, int]]) -> dict[str, dict[str, int]]:
    SpatialPoint_URI = osmnode[str(osm_node).split('/')[-1]]

    piirrited_graph.add((SpatialPoint_URI, RDF.type, piirrite.SpatialPoint))
    piirrited_graph.add((SpatialPoint_URI, RDF.type, osm.node))

    for p, o in osmd_graph.predicate_objects(osm_node):
        if p == geo.hasGeometry:
            add_geometry_to_SpatialPoint(piirrited_graph, osmd_graph, SpatialPoint_URI, o)
        
        elif isinstance(p, URIRef) and str(p).startswith(str(osm)) and 'wiki/Key:' in str(p):
            # if 'addr:' in str(p) or 'operator' in str(p):
            #     continue
            unfounds = add_context_to_SpatialPoint(
                osm_node, piirrite_graph, piirritev_graph, piirrited_graph, osmd_graph,
                SpatialPoint_URI, str(p).split('wiki/Key:')[-1], str(o), unfounds
            )

    return unfounds

###########################

def display_unfounds(unfounds:dict[str, dict[str, int]]) -> None:
    unfound_keys = 0
    for value in unfounds['keys'].values():
        unfound_keys += value
    
    unfound_values = 0
    for value in unfounds['values'].values():
        unfound_values += value
    
    print(f'{unfound_keys} clés non trouvées dans piirritev:')
    print(sort_dict_by_values(unfounds['values']), '\n')
    print(f'{unfound_values} valeurs non trouvées dans piirritev:')
    print(sort_dict_by_values(unfounds['values']))

def use_osm_data_to_fill_in_piirrited_graph(piirrite_graph:Graph,
                                         piirritev_graph:Graph,
                                         piirrited_graph:Graph) -> None:
    osmd_graph = init_osmd_graph()

    # on veut garder la trace des clés et valeurs OSM non trouvées dans PIIRRITE
    unfounds:dict[str, dict[str, int]] = {'keys': {}, 'values': {}}

    osm_nodes = list(osmd_graph.subjects(RDF.type, osm['node']))
    for count, osm_node in enumerate(osm_nodes):
        if isinstance(osm_node, URIRef):
            unfounds = add_SpatialPoint_to_piirrited(osm_node, osmd_graph, piirrite_graph,
                                                  piirritev_graph, piirrited_graph, unfounds)
        display_progress_bar(count, len(osm_nodes), message = f'des {len(osm_nodes)} nœuds traités…')
    
    display_unfounds(unfounds)

def main():
    piirrite_graph = init_piirrite_graph()
    piirritev_graph = init_piirritev_graph()
    piirrited_graph = init_piirrited_graph()
    use_osm_data_to_fill_in_piirrited_graph(piirrite_graph, piirritev_graph, piirrited_graph)
    piirrited_graph.serialize(ABox_file, 'turtle')

    print('\nOntologie peuplée avec succès.')

if __name__ == '__main__':
    main()
from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.namespace import OWL, RDF, RDFS, XSD, SKOS
from utilities.utilities import get_current_path, snake_to_camel, display_progress_bar, sort_dict_by_values, str_to_best_type

incit = Namespace('http://incit.univ-lyon1.fr/ontology/core#')
incitv = Namespace('http://incit.univ-lyon1.fr/vocabulary#')
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

def init_incit_graph() -> Graph:
    incit_graph = Graph()
    with open(TBox_file, 'r', encoding = 'utf-8') as TBox_file_content:
        incit_graph.parse(data = TBox_file_content.read(), format = 'turtle')
    with open(TBox2_file, 'r', encoding = 'utf-8') as TBox2_file_content:
        incit_graph.parse(data = TBox2_file_content.read(), format = 'turtle')
    
    return incit_graph

def init_incitv_graph() -> Graph:
    incitv_graph = Graph()
    with open(GoT_file, 'r', encoding = 'utf-8') as GoT_file_content:
        incitv_graph.parse(data = GoT_file_content.read(), format = 'turtle')
    
    return incitv_graph

def init_incitd_graph() -> Graph:
    incitd_graph = Graph()
    incitd_graph.bind('incit', incit)
    incitd_graph.bind('incitv', incitv)
    incitd_graph.bind('rdfs', RDFS)
    incitd_graph.bind('xsd', XSD)
    incitd_graph.bind('osm', osm)
    incitd_graph.bind('osmnode', osmnode)
    incitd_graph.bind('geo', geo)
    incitd_graph.bind('saref', saref)

    return incitd_graph

def init_osmd_graph() -> Graph:
    print('Récupération des données OSM…')
    osmd_graph = Graph()
    osmd_graph.parse(raw_data_file, 'turtle')
    
    print('Données OSM récupérées.')
    return osmd_graph

def add_geometry_to_SpatialPoint(incitd_graph:Graph,
                                 osmd_graph:Graph,
                                 SpatialPoint_URI:URIRef,
                                 osm_geometry) -> None:
    geometry_as_WKT = list(osmd_graph.objects(osm_geometry, geo.asWKT))
    if len(geometry_as_WKT) == 1:
        geometry_as_WKT = geometry_as_WKT[0]
        geometry = BNode()
        incitd_graph.add((SpatialPoint_URI, geo.hasGeometry, geometry))
        incitd_graph.add((geometry, RDF.type, geo.Geometry))
        incitd_graph.add((geometry,
                        geo.asWKT,
                        Literal(str(geometry_as_WKT), datatype = geo['wktLiteral'])))

def add_context_to_SpatialPoint(osm_node:URIRef,
                                incit_graph:Graph, incitv_graph:Graph, incitd_graph:Graph, osmd_graph:Graph,
                                SpatialPoint_URI:URIRef, osm_key:str, osm_value:str, unfounds:dict[str, dict[str, int]]) -> dict[str, dict[str, int]]:
    # OSM utilise du snake_case et INCIT du CamelCase
    concept = 'Osm' + snake_to_camel(osm_key) + snake_to_camel(osm_value)
    
    # Toutes les valeurs de clé possibles devraient exister.
    # Au cas où, on vérifie
    if (incitv[concept], RDF.type, SKOS.Concept) not in incitv_graph:
        if concept not in unfounds['values'].keys():
            unfounds['values'][concept] = 1
        else:
            unfounds['values'][concept] += 1
        return unfounds

    # À ce stade, plus rien ne s'oppose à l'enregistrement de la donnée contextuelle.
    # On le fait donc
    context = BNode()
    incitd_graph.add((SpatialPoint_URI, saref.hasProperty, context))
    incitd_graph.add((context, RDF.type, saref.Property))
    incitd_graph.add((context, RDF.type, incitv[concept]))

    # Il faut encore vérifier si des triplets de osmd_graph sont des
    # étiquettes utilisées en combinaison avec le concept
    #
    # Plus de détails : OSM permet à certains tags d'avoir des attributs supplémentaires
    # à travers des "tags used in combination" ("tuic").
    # ex: [amemity=bicycle_parking, capacity="12"]
    # Ici, OSM comprend implicitement que l'attribut "capacity" se rapporte au tag "bicycle_parking"
    # grâce à la logique interne des tuic.
    # INCIT gère ces attributs supplémentaires !
    # Pour cela, il passe par la propriété incit:hasRelatedOsmTag
    # ex: incitv:OsmAmenityBicycleParking a skos:Concept ;
    #         incit:hasRelatedOsmTag incitv:hasOsmBicycleParkingCapacity
    #     osmnode:1 a incit:SpatialPoint ;
    #         incit:hasAmenity [ a saref:Property ;
    #             rdfs:isDefinedBy incitv:OsmAmenityBicycleParking ;
    #             incitv:hasOsmBicycleParkingCapacity '12']

    # Ensemble des propriétés liées au nœud OSM courant
    tuic_candidates = {}
    for p, o in osmd_graph.predicate_objects(osm_node):
        if 'wiki/Key:' in str(p):
            tuic_candidates[str(p).split('wiki/Key:')[-1]] = str(o)
    
    # Ensemble des étiquettes utilisées en combinaison avec le concept INCITV courant
    possible_tuics = []
    for o in incitv_graph.objects(incitv[concept], incit.hasRelatedOsmTag):
        osm_name = next(incit_graph.objects(URIRef(str(o)), incit.osmId, True), None)
        if osm_name:
            possible_tuics.append(str(osm_name))

    for tuic, tuic_value in tuic_candidates.items():
        if tuic in possible_tuics:
            # on a trouvé un tuic !
            tuic_incitv_name = snake_to_camel(tuic) if tuic != osm_value else 'Type'
            tuic_URI = incit['hasOsm' + snake_to_camel(osm_value) + tuic_incitv_name]
            tuic_value = str_to_best_type(tuic_value)
            if isinstance(tuic_value, int):
                tuic_datatype = XSD.integer
            elif isinstance(tuic_value, float):
                tuic_datatype = XSD.float
            elif isinstance(tuic_value, bool):
                tuic_datatype = XSD.boolean
            else:
                tuic_datatype = XSD.string
            incitd_graph.add((context, tuic_URI, Literal(tuic_value, datatype = tuic_datatype)))

    return unfounds

def add_SpatialPoint_to_incitd(osm_node:URIRef,
                               osmd_graph:Graph,
                               incit_graph:Graph,
                               incitv_graph:Graph,
                               incitd_graph:Graph,
                               unfounds:dict[str, dict[str, int]]) -> dict[str, dict[str, int]]:
    SpatialPoint_URI = osmnode[str(osm_node).split('/')[-1]]

    incitd_graph.add((SpatialPoint_URI, RDF.type, incit.SpatialPoint))
    incitd_graph.add((SpatialPoint_URI, RDF.type, osm.node))

    for p, o in osmd_graph.predicate_objects(osm_node):
        if p == geo.hasGeometry:
            add_geometry_to_SpatialPoint(incitd_graph, osmd_graph, SpatialPoint_URI, o)
        
        elif isinstance(p, URIRef) and str(p).startswith(str(osm)) and 'wiki/Key:' in str(p):
            # if 'addr:' in str(p) or 'operator' in str(p):
            #     continue
            unfounds = add_context_to_SpatialPoint(
                osm_node, incit_graph, incitv_graph, incitd_graph, osmd_graph,
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
    
    print(f'{unfound_keys} clés non trouvées dans incitv:')
    print(sort_dict_by_values(unfounds['values']), '\n')
    print(f'{unfound_values} valeurs non trouvées dans incitv:')
    print(sort_dict_by_values(unfounds['values']))

def use_osm_data_to_fill_in_incitd_graph(incit_graph:Graph,
                                         incitv_graph:Graph,
                                         incitd_graph:Graph) -> None:
    osmd_graph = init_osmd_graph()

    # on veut garder la trace des clés et valeurs OSM non trouvées dans INCIT
    unfounds = {'keys': {}, 'values': {}}

    osm_nodes = list(osmd_graph.subjects(RDF.type, osm['node']))
    for count, osm_node in enumerate(osm_nodes):
        if isinstance(osm_node, URIRef):
            unfounds = add_SpatialPoint_to_incitd(osm_node, osmd_graph, incit_graph,
                                                  incitv_graph, incitd_graph, unfounds)
        display_progress_bar(count, len(osm_nodes), message = f'des {len(osm_nodes)} nœuds traitées…')
    
    display_unfounds(unfounds)

def main():
    incit_graph = init_incit_graph()
    incitv_graph = init_incitv_graph()
    incitd_graph = init_incitd_graph()
    use_osm_data_to_fill_in_incitd_graph(incit_graph, incitv_graph, incitd_graph)
    incitd_graph.serialize(ABox_file, 'turtle')

    print('\nOntologie peuplée avec succès.')

if __name__ == '__main__':
    main()
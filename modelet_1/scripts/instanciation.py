from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.namespace import OWL, RDF, RDFS, XSD, SKOS
from shapely import wkt
from shapely.ops import transform
from shapely.strtree import STRtree
from collections import defaultdict
import pyproj
from utilities.utilities import *

piirrite = Namespace('http://piirrite.univ-lyon1.fr/ontology/core#')
base     = Namespace('http://piirrite.univ-lyon1.fr/data#')
osm      = Namespace('https://www.openstreetmap.org/')
saref    = Namespace('https://saref.etsi.org/core/')
geo      = Namespace('http://www.opengis.net/ont/geosparql#')
sf       = Namespace('http://www.opengis.net/ont/sf#')


raw_data_file = get_current_path() + '/osm_data_natif.ttl'
TBox_file = get_current_path() + '/../TBox.ttl'
ABox_file = get_current_path() + '/../ABox.ttl'

path_properties = [
        # Piétons
        'highway:footway', 'highway:pedestrian',
        'highway:steps', 'highway:path', 'footway:sidewalk',
        'footway:crossing', 'footway:yes', 'sidewalk:both',
        'sidewalk:left', 'sidewalk:right', 'sidewalk:yes',
        'foot:yes', 'foot:designated', 'foot:permissive',

        # Piétons - intérieur (indoor)
        'highway:corridor', 'indoor:corridor', 'highway:elevator',
        'elevator:yes', 'conveying:forward', 'conveying:backward',
        'conveying:reversible', 'escalator:yes',

        # Vélos
        'highway:cycleway', 'bicycle:yes', 'bicycle:designated',
        'bicycle:permissive', 'cycleway:lane', 'cycleway:track',
        'cycleway:both', 'cycleway:left', 'cycleway:right',
        'cycleway:shared', 'cycleway:opposite', 'cycleway:opposite_lane',
        'cycleway:opposite_track',

        # Skateboards
        'skating:yes',

        # Fauteuils roulants
        'wheelchair:yes', 'wheelchair:designated',
        'wheelchair:limited', 'kerb:lowered', 'kerb:flush',
        'ramp:wheelchair', 'tactile_paving:yes',
    ]
aoi_properties = [
    # Bâtiments
    'building:yes', 'building:residential', 'building:commercial',
    'building:industrial', 'building:retail', 'building:office',
    'building:warehouse', 'building:garage', 'building:garages',
    'building:school', 'building:university', 'building:hospital',
    'building:hotel', 'building:church', 'building:cathedral',
    'building:chapel', 'building:mosque', 'building:temple',
    'building:synagogue', 'building:train_station', 'building:transportation',
    'building:civic', 'building:public', 'building:government',
    'building:sports_hall', 'building:stadium', 'building:greenhouse',
    'building:barn', 'building:farm', 'building:cabin',
    'building:hut', 'building:shed', 'building:roof',
    'building:terrace', 'building:apartments', 'building:part:yes',

    # Landuse (occupation du sol)
    'landuse:residential', 'landuse:commercial', 'landuse:industrial',
    'landuse:retail', 'landuse:office', 'landuse:farmland',
    'landuse:farmyard', 'landuse:forest', 'landuse:grass',
    'landuse:meadow', 'landuse:orchard', 'landuse:vineyard',
    'landuse:cemetery', 'landuse:allotments', 'landuse:recreation_ground',
    'landuse:village_green', 'landuse:military', 'landuse:quarry',
    'landuse:landfill', 'landuse:brownfield', 'landuse:greenfield',
    'landuse:construction', 'landuse:railway', 'landuse:basin',
    'landuse:reservoir', 'landuse:salt_pond', 'landuse:aquaculture',
    'landuse:plant_nursery', 'landuse:flowerbed', 'landuse:garages',

    # Zones naturelles
    'natural:wood', 'natural:scrub', 'natural:heath',
    'natural:grassland', 'natural:wetland','natural:beach',
    'natural:sand', 'natural:scree', 'natural:shingle',
    'natural:bare_rock', 'natural:glacier', 'natural:water',
    'natural:mud', 'natural:tundra', 'natural:fell',

    # Eau
    'water:lake', 'water:pond', 'water:reservoir',
    'water:basin', 'water:lagoon', 'water:river',
    'water:canal', 'water:ditch', 'water:stream',
    'water:oxbow', 'water:fish_pass', 'waterway:riverbank',
    'waterway:dock', 'waterway:boatyard',

    # Loisirs
    'leisure:park', 'leisure:garden', 'leisure:playground',
    'leisure:pitch', 'leisure:sports_centre', 'leisure:stadium',
    'leisure:track', 'leisure:golf_course', 'leisure:miniature_golf',
    'leisure:swimming_pool', 'leisure:water_park', 'leisure:marina',
    'leisure:nature_reserve', 'leisure:dog_park', 'leisure:ice_rink',
    'leisure:horse_riding', 'leisure:disc_golf_course',

    # Aménagements / Tourisme
    'amenity:parking', 'amenity:school', 'amenity:university',
    'amenity:college', 'amenity:hospital', 'amenity:clinic',
    'amenity:marketplace', 'amenity:grave_yard', 'amenity:place_of_worship',
    'amenity:prison', 'amenity:ferry_terminal', 'amenity:bus_station',
    'amenity:fuel', 'amenity:social_facility', 'amenity:arts_centre',
    'amenity:cinema', 'amenity:theatre', 'amenity:community_centre',
    'amenity:exhibition_centre', 'amenity:conference_centre',

    # Tourisme
    'tourism:attraction', 'tourism:camp_site', 'tourism:caravan_site',
    'tourism:picnic_site', 'tourism:zoo', 'tourism:theme_park',
    'tourism:museum', 'tourism:gallery',

    # Commerce / Bureaux
    'shop:mall', 'shop:supermarket', 'shop:department_store',

    # Zones militaires
    'military:airfield', 'military:barracks', 'military:danger_area',
    'military:range', 'military:naval_base', 'military:training_area',

    # Aéroports / Transports
    'aeroway:aerodrome', 'aeroway:apron', 'aeroway:terminal',
    'aeroway:hangar', 'aeroway:helipad',

    # Zones indoor
    'indoor:room', 'indoor:area', 'indoor:yes',
    'room:yes',

    # Limites administratives et places
    'place:island', 'place:islet', 'place:square',

    # tag explicite indiquant que la way fermée est une surface
    'area:yes',             
]
wgs84 = pyproj.CRS("EPSG:4326")
lambert = pyproj.CRS("EPSG:2154")
projection = pyproj.Transformer.from_crs(wgs84, lambert, always_xy = True).transform

###########################

def init_data_graph() -> Graph:
    data_graph = Graph()
    data_graph.bind('piirrite', piirrite)
    data_graph.bind('', base)
    data_graph.bind('rdfs', RDFS)
    data_graph.bind('xsd', XSD)
    data_graph.bind('geo', geo)
    data_graph.bind('sf', sf)

    return data_graph


def init_osm_graph() -> Graph:
    print('Récupération des données OSM…')
    osm_graph = Graph()
    osm_graph.parse(raw_data_file, 'turtle')
    
    print('Données OSM récupérées.')
    return osm_graph


def add_geometry_to_geoFeature(
        FeatureURI:URIRef,
        geometry_as_wkt:str,
        data_graph:Graph
) -> None:
    geometry = BNode()
    data_graph.add((FeatureURI, geo.hasGeometry, geometry))
    data_graph.add((geometry, geo.asWKT, Literal(geometry_as_wkt, datatype = geo['wktLiteral'])))
    if "POINT" in geometry_as_wkt:
        data_graph.add((geometry, RDF.type, sf.Point))
    elif "LINESTRING" in geometry_as_wkt:
        data_graph.add((geometry, RDF.type, sf.LineString))
    elif "POLYGON" in geometry_as_wkt:
        data_graph.add((geometry, RDF.type, sf.Polygon))


def get_geometry_as_wkt(
    entity,
    data_graph:Graph
) -> str | None:
    entity_geometry = list(data_graph.objects(entity, geo.hasGeometry))
    if len(entity_geometry) != 1:
        return None
    else:
        entity_wkt = list(data_graph.objects(entity_geometry[0], geo.asWKT))
        if len(entity_wkt) != 1:
            return None
        else:
            return str(entity_wkt[0])


def build_poi_spatial_index(data_graph: Graph):
    """
    Construit, en une passe sur le graphe :
      - pois_by_level : {level_str : (STRtree, [URIRef], [shape_projetée])}
    """
    pois_data = defaultdict(list)

    q = """
    PREFIX piirrite: <http://piirrite.univ-lyon1.fr/ontology/core#>
    PREFIX geo: <http://www.opengis.net/ont/geosparql#>
    SELECT ?ptoi ?wktLit WHERE {
        ?ptoi a piirrite:PointOfInterest ;
              geo:hasGeometry/geo:asWKT ?wktLit .
    }
    """
    rows = list(data_graph.query(q))

    q_levels = """
    PREFIX piirrite: <http://piirrite.univ-lyon1.fr/ontology/core#>
    SELECT ?ptoi ?prop WHERE {
        ?ptoi a piirrite:PointOfInterest ;
              piirrite:hasProperty ?prop .
        FILTER(STRSTARTS(STR(?prop), "level:"))
    }
    """
    level_map = {}
    for ptoi, prop in data_graph.query(q_levels): # type: ignore
        level_map[ptoi] = str(prop).split(':', 1)[1]

    for ptoi, wkt_lit in rows: # type: ignore
        try:
            shape = transform(projection, wkt.loads(str(wkt_lit)))
        except Exception:
            continue
        level = level_map.get(ptoi, '')
        pois_data[level].append((ptoi, shape))

    # Construit un STRtree par level
    index = {}
    for level, items in pois_data.items():
        shapes = [s for _, s in items]
        uris   = [u for u, _ in items]
        tree = STRtree(shapes) if shapes else None
        index[level] = (tree, uris, shapes)
    return index


def is_nearby(
    entity_a,
    entity_b,
    data_graph:Graph,
    max_distance:int = 5,
) -> bool:
    wkt_a = get_geometry_as_wkt(entity_a, data_graph)
    wkt_b = get_geometry_as_wkt(entity_b, data_graph)

    if not (wkt_a and wkt_b):
        raise ValueError('Au moins une des deux entités n\'a pas de geometry wkt.')

    shape_a = transform(projection, wkt.loads(wkt_a))
    shape_b = transform(projection, wkt.loads(wkt_b))

    return shape_a.distance(shape_b) < max_distance


def add_passesBy(
    path_URI:URIRef,
    path_wkt_str: str,
    path_properties: list[str],
    poi_index: dict,
    data_graph:Graph,
    max_distance: float = 5.0 # mètres
) -> None:
    # Calcule la géométrie projetée du path
    try:
        path_shape = transform(projection, wkt.loads(path_wkt_str))
    except Exception:
        return

    path_level = ''
    for p in path_properties:
        if str(p).startswith('level:'):
            path_level = str(p).split(':', 1)[1]
            break
    
    # Détermine quels étages sont compatibles
    candidate_levels = []
    for lvl in poi_index.keys():
        if lvl == path_level or lvl in path_level or path_level in lvl:
            candidate_levels.append(lvl)

    # Utilise un buffer pour une recherche spatiale rapide
    search_zone = path_shape.buffer(max_distance)

    for lvl in candidate_levels:
        tree, uris, shapes = poi_index[lvl]
        if tree is None:
            continue
        # STRtree.query renvoie les indices des candidats potentiels
        candidate_idx = tree.query(search_zone)
        for idx in candidate_idx:
            if shapes[idx].distance(path_shape) < max_distance:
                data_graph.add((path_URI, piirrite.passesBy, uris[idx]))


def add_ElementOfInterest(
        FoI_type,
        FoI_URI:URIRef,
        geometry_as_wkt,
        data_graph:Graph
) -> None:
    if geometry_as_wkt:
        data_graph.add((FoI_URI, RDF.type, FoI_type))
        add_geometry_to_geoFeature(FoI_URI, geometry_as_wkt, data_graph)


def get_geometry(
    FoI_OSM_URI:URIRef,
    osm_graph:Graph
) -> str | None:
    geometry_as_wkt = None
    for p, o in osm_graph.predicate_objects(FoI_OSM_URI): 
        if p == geo.hasGeometry:
            if geometry_as_wkt:
                # print(f"ERREUR - plusieurs géométries trouvées ({str(FoI_OSM_URI)})")
                return
            
            geometries_as_WKT = list(osm_graph.objects(o, geo.asWKT))
            if len(geometries_as_WKT) == 1:
                geometry_as_wkt = str(geometries_as_WKT[0])
            else:
                # print(f"ERREUR - nombre de géométrie(s) différent de 1 ({str(FoI_OSM_URI)})")
                return
    
    return geometry_as_wkt


def get_properties(
    FoI_OSM_URI:URIRef,
    osm_graph:Graph
) -> list[str] | None:
    properties = list()
    for p, o in osm_graph.predicate_objects(FoI_OSM_URI): 
        if isinstance(p, URIRef) and str(p).startswith(str(osm)) and 'wiki/Key:' in str(p):
                properties.append(f'{str(p).split('wiki/Key:')[1]}:{o}')

    return properties


def detect_potential_ElementOfInterest(
        FoI_OSM_URI:URIRef,
        osm_graph:Graph,
        data_graph:Graph,
        paths_to_process:list[tuple[URIRef, str, list]]
) -> list[tuple[URIRef, str, list]]:
    properties = []
    geometry_as_wkt = None

    geometry_as_wkt = get_geometry(FoI_OSM_URI, osm_graph)
    properties = get_properties(FoI_OSM_URI, osm_graph)

    entity_id = str(FoI_OSM_URI).split('/')[-1]
    if geometry_as_wkt:
        if 'node' in str(FoI_OSM_URI) and 'POINT' in geometry_as_wkt:
            if properties:
                add_ElementOfInterest(
                    piirrite.PointOfInterest,
                    base['ptoi_' + entity_id],
                    geometry_as_wkt,
                    data_graph
                )

        elif 'way' in str(FoI_OSM_URI):            
            if properties:
                if any(property in aoi_properties for property in properties) and 'POLYGON' in geometry_as_wkt:
                    add_ElementOfInterest(
                        piirrite.AreaOfInterest,
                        base['aoi_' + entity_id],
                        geometry_as_wkt,
                        data_graph
                    )

                elif any(property in path_properties for property in properties):
                    add_ElementOfInterest(
                        piirrite.NavigablePath,
                        base['path_' + entity_id],
                        geometry_as_wkt,
                        data_graph
                    )
                    paths_to_process.append((base['path_' + entity_id], geometry_as_wkt, []))

                else:
                    add_ElementOfInterest(
                        piirrite.PolylineOfInterest,
                        base['ploi_' + entity_id],
                        geometry_as_wkt,
                        data_graph
                    )

            else:
                add_ElementOfInterest(
                    piirrite.NavigablePath,
                    base['path_' + entity_id],
                    geometry_as_wkt,
                    data_graph
                )
                paths_to_process.append((base['path_' + entity_id], geometry_as_wkt, []))
    
    return paths_to_process

###########################

def use_osm_data_to_fill_in_data_graph(
        osm_graph:Graph,
        data_graph:Graph
) -> None:

    # Passe 1 : nodes
    osm_nodes = list(osm_graph.subjects(RDF.type, osm['node']))
    n = len(osm_nodes)
    for count, node in enumerate(osm_nodes):
        if isinstance(node, URIRef):
            detect_potential_ElementOfInterest(node, osm_graph, data_graph, [])
        display_progress_bar(count, n, message=f'des {n} nodes OSM traités…')
    print()

    # Passe 2 : ways sans passesBy
    paths_to_process = []
    osm_ways = list(osm_graph.subjects(RDF.type, osm['way']))
    n_osm_ways = len(osm_ways)
    for count, osm_way in enumerate(osm_ways):
        if isinstance(osm_way, URIRef):
            paths_to_process = detect_potential_ElementOfInterest(osm_way, osm_graph, data_graph, paths_to_process)
        display_progress_bar(
            count,
            n_osm_ways,
            message = f'des {n_osm_ways} ways OSM traitées…'
        )
    
    print('\nConstruction de l\'index spatial des POIs…')
    poi_index = build_poi_spatial_index(data_graph)

    # Passe 3 : passesBy
    n = len(paths_to_process)
    for count, (path_uri, path_wkt_str, props) in enumerate(paths_to_process):
        add_passesBy(path_uri, path_wkt_str, props, poi_index, data_graph)
        display_progress_bar(count, n, message=f'des {n} paths analysés…')


def main():
    osm_graph = init_osm_graph()
    data_graph = init_data_graph()

    use_osm_data_to_fill_in_data_graph(osm_graph, data_graph)
    data_graph.serialize(ABox_file, 'turtle')

    print('\nOntologie peuplée avec succès.')


if __name__ == '__main__':
    main()
import re
import requests
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import SKOS, RDF, RDFS, OWL, XSD
from utilities.utilities import snake_to_camel, snake_to_natural, get_current_path, display_progress_bar, execute_file, copyfile

incit = Namespace('http://incit.univ-lyon1.fr/ontology/core#')
incitv = Namespace('http://incit.univ-lyon1.fr/vocabulary#')
osmkey = Namespace('https://www.openstreetmap.org/wiki/Key:')
geo = Namespace('http://www.opengis.net/ont/geosparql#')
saref = Namespace('https://saref.etsi.org/core/')

PREVIOUS_MODELET = get_current_path() + '/../../Modelet 1 (Points spatiaux)/'
CURRENT_MODELET = get_current_path() + '/../'
INCIT_CREATION_FILE = '/scripts/IncIt creation.py'
INCIT_INSTANCIATION_FILE = '/scripts/IncIt creation.py'
GOT_FILE = '/GoT.ttl'
TBOX_FILE = '/TBox.ttl'
TBOX2_FILE = '/TBox2.ttl'
OSM_WIKI_URL = 'https://wiki.openstreetmap.org/w/api.php'

###########################

def update_previous_modelet(update_level:int) -> None:
    """update_level = 0 : no update
    1 : update TBox and GoT
    2 : update TBox, GoT and ABox"""
    if update_level == 0:
        return
    elif update_level == 1:
        tmp = execute_file(PREVIOUS_MODELET + INCIT_CREATION_FILE)
    elif update_level == 2:
        execute_file(PREVIOUS_MODELET + INCIT_CREATION_FILE)
        execute_file(PREVIOUS_MODELET + INCIT_INSTANCIATION_FILE)

def init_incit_graph() -> Graph:
    copyfile(PREVIOUS_MODELET + TBOX_FILE, CURRENT_MODELET + TBOX_FILE)
    incit_graph = Graph()
    with open(CURRENT_MODELET + TBOX_FILE, 'r', encoding = 'utf-8') as TBox_file_content:
        incit_graph.parse(data = TBox_file_content.read(), format = 'turtle')

    add_SpatialEntity_to_incit(incit_graph)
    add_SpatialSegment_to_incit(incit_graph)
    add_TraversableSegment_to_incit(incit_graph)
    add_TopologicalSegment_to_incit(incit_graph)
    add_hasExtremity_to_incit(incit_graph)
    add_isExtremityOf_to_incit(incit_graph)

    update_SpatialPoint(incit_graph)
    update_OsmEntity(incit_graph)

    return incit_graph

def init_incitv_graph() -> Graph:
    copyfile(PREVIOUS_MODELET + GOT_FILE, CURRENT_MODELET + GOT_FILE)
    incitv_graph = Graph()
    with open(CURRENT_MODELET + GOT_FILE, 'r', encoding = 'utf-8') as GoT_file_content:
        incitv_graph.parse(data = GoT_file_content.read(), format = 'turtle')

    return incitv_graph

def init_incit2_graph() -> Graph:
    copyfile(PREVIOUS_MODELET + TBOX2_FILE, CURRENT_MODELET + TBOX2_FILE)
    incit2_graph = Graph()
    with open(CURRENT_MODELET + TBOX2_FILE, 'r', encoding = 'utf-8') as TBox2_file_content:
        incit2_graph.parse(data = TBox2_file_content.read(), format = 'turtle')

    return incit2_graph

def add_SpatialEntity_to_incit(incit_graph:Graph) -> None:
    SpatialEntity_URI = incit.SpatialEntity
    incit_graph.add((SpatialEntity_URI, RDF.type, OWL.Class))
    incit_graph.add((SpatialEntity_URI, RDFS.subClassOf, geo.Feature))
    incit_graph.add((SpatialEntity_URI, RDFS.label, Literal('Spatial entity', lang = 'en')))
    incit_graph.add((SpatialEntity_URI, RDFS.label, Literal('Entité spatiale', lang = 'fr')))
    incit_graph.add((SpatialEntity_URI,
                     RDFS.comment,
                     Literal('An entity located in a geographic space.',
                             lang = 'en')))
    incit_graph.add((SpatialEntity_URI,
                     RDFS.comment,
                     Literal('Une entité localisée dans un espace géographique.',
                             lang = 'fr')))
    
def add_SpatialSegment_to_incit(incit_graph:Graph):
    SpatialSegment_URI = incit.SpatialSegment
    incit_graph.add((SpatialSegment_URI, RDF.type, OWL.Class))
    incit_graph.add((SpatialSegment_URI, RDFS.subClassOf, incit.SpatialEntity))
    incit_graph.add((SpatialSegment_URI, RDFS.subClassOf, saref.FeatureOfInterest))
    incit_graph.add((SpatialSegment_URI, RDFS.label, Literal('Spatial segment', lang = 'en')))
    incit_graph.add((SpatialSegment_URI, RDFS.label, Literal('Segment spatial', lang = 'fr')))
    incit_graph.add((SpatialSegment_URI,
                     RDFS.comment,
                     Literal('A segment located in a geographic space and possibly contextualized by properties.',
                             lang = 'en')))
    incit_graph.add((SpatialSegment_URI,
                     RDFS.comment,
                     Literal('Un segment localisé dans un espace géographique et possiblement contextualisé par des propriétés.',
                             lang = 'fr')))

def add_TraversableSegment_to_incit(incit_graph:Graph) -> None:
    TraversableSegment_URI = incit.TraversableSegment
    incit_graph.add((TraversableSegment_URI, RDF.type, OWL.Class))
    incit_graph.add((TraversableSegment_URI, RDFS.subClassOf, incit.SpatialSegment))
    incit_graph.add((TraversableSegment_URI, RDFS.label, Literal('Traversable segment', lang = 'en')))
    incit_graph.add((TraversableSegment_URI, RDFS.label, Literal('Segment praticable', lang = 'fr')))
    incit_graph.add((TraversableSegment_URI,
                     RDFS.comment,
                     Literal('A spatial segment that can be traversed by users.',
                             lang = 'en')))
    incit_graph.add((TraversableSegment_URI,
                     RDFS.comment,
                     Literal('Un segment spatial praticable par les utilisateurs.',
                             lang = 'fr')))

def add_TopologicalSegment_to_incit(incit_graph:Graph) -> None:
    TopologicalSegment_URI = incit.TopologicalSegment
    incit_graph.add((TopologicalSegment_URI, RDF.type, OWL.Class))
    incit_graph.add((TopologicalSegment_URI, RDFS.subClassOf, incit.SpatialSegment))
    incit_graph.add((TopologicalSegment_URI, RDFS.label, Literal('Topological segment', lang = 'en')))
    incit_graph.add((TopologicalSegment_URI, RDFS.label, Literal('Segment topologique', lang = 'fr')))
    incit_graph.add((TopologicalSegment_URI,
                     RDFS.comment,
                     Literal('A spatial segment structuring the traversed space (e.g. wall, isoline, …).',
                             lang = 'en')))
    incit_graph.add((TopologicalSegment_URI,
                     RDFS.comment,
                     Literal('Un segment spatial structurant l\'espace parcouru (e.g. mur, isoligne, …).',
                             lang = 'fr')))

def add_hasExtremity_to_incit(incit_graph:Graph) -> None:
    hasExtremity_URI = incit.hasExtremity
    incit_graph.add((hasExtremity_URI, RDF.type, OWL.ObjectProperty))
    incit_graph.add((hasExtremity_URI, RDFS.label, Literal('has extremity', lang = 'en')))
    incit_graph.add((hasExtremity_URI, RDFS.label, Literal('a l\'extrémité', lang = 'fr')))
    incit_graph.add((hasExtremity_URI,
                     RDFS.comment,
                     Literal('Links a spatial segment to one of its two extremities, which are spatial points.',
                             lang = 'en')))
    incit_graph.add((hasExtremity_URI,
                     RDFS.comment,
                     Literal('Lie un segment spatial à une de ses deux extrémités, qui sont des points spatiaux.',
                             lang = 'fr')))
    incit_graph.add((hasExtremity_URI, RDFS.domain, incit.SpatialSegment))
    incit_graph.add((hasExtremity_URI, RDFS.range, incit.SpatialPoint))
    incit_graph.add((hasExtremity_URI, OWL.inverseOf, incit.isExtremityOf))

def add_isExtremityOf_to_incit(incit_graph:Graph) -> None:
    isExtremityOf_URI = incit.isExtremityOf
    incit_graph.add((isExtremityOf_URI, RDF.type, OWL.ObjectProperty))
    incit_graph.add((isExtremityOf_URI, RDFS.label, Literal('is an extremity of', lang = 'en')))
    incit_graph.add((isExtremityOf_URI, RDFS.label, Literal('est  l\'une des extrémités de', lang = 'fr')))
    incit_graph.add((isExtremityOf_URI,
                     RDFS.comment,
                     Literal('Links a spatial point to a spatial segment of which it is an extremity.',
                             lang = 'en')))
    incit_graph.add((isExtremityOf_URI,
                     RDFS.comment,
                     Literal('Lie un point spatial à un segment spatial duquel il est une extrémité.',
                             lang = 'fr')))
    incit_graph.add((isExtremityOf_URI, RDFS.domain, incit.SpatialPoint))
    incit_graph.add((isExtremityOf_URI, RDFS.range, incit.SpatialSegment))
    incit_graph.add((isExtremityOf_URI, OWL.inverseOf, incit.hasExtremity))

def update_SpatialPoint(incit_graph:Graph) -> None:
    SpatialPoint_URI = incit.SpatialPoint
    incit_graph.remove((SpatialPoint_URI, RDFS.subClassOf, geo.Feature))
    incit_graph.add((SpatialPoint_URI, RDFS.subClassOf, incit.SpatialEntity))

def update_OsmEntity(incit_graph:Graph) -> None:
    OsmEntity_URI = incit.OsmEntity
    incit_graph.remove((OsmEntity_URI, RDFS.comment, None))
    incit_graph.add((OsmEntity_URI,
                     RDFS.comment,
                     Literal('An OSM entity used to contextualize a spatial entity.',
                             lang = 'en')))
    incit_graph.add((OsmEntity_URI,
                     RDFS.comment,
                     Literal('Une entité OSM utilisée pour contextualiser une entité spatiale.',
                             lang = 'fr')))
    
###########################

def main(update_level:int):
    update_previous_modelet(update_level)
    incit_graph = init_incit_graph()
    incitv_graph = init_incitv_graph()
    incit2_graph = init_incit2_graph()
    
    incit_graph.serialize(CURRENT_MODELET + TBOX_FILE, 'turtle')
    incitv_graph.serialize(CURRENT_MODELET + GOT_FILE, 'turtle')
    incit2_graph.serialize(CURRENT_MODELET + TBOX2_FILE, 'turtle')

    print(f'Ontologie et glossaire initialisés, remplis et sauvegardés avec succès.')

if __name__ == '__main__':
    update_level = 0
    main(update_level)
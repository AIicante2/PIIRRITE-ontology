import re
import requests
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import SKOS, RDF, RDFS, OWL, XSD
from utilities.utilities import *

piirrite = Namespace('http://piirrite.univ-lyon1.fr/ontology/core#')
piirritev = Namespace('http://piirrite.univ-lyon1.fr/vocabulary#')
osmkey = Namespace('https://www.openstreetmap.org/wiki/Key:')
geo = Namespace('http://www.opengis.net/ont/geosparql#')
saref = Namespace('https://saref.etsi.org/core/')

PREVIOUS_MODELET = get_current_path() + '/../../modelet_1/'
CURRENT_MODELET = get_current_path() + '/../'
PIIRRITE_CREATION_FILE = '/scripts/piirrite_creation.py'
PIIRRITE_INSTANCIATION_FILE = '/scripts/piirrite_instanciation.py'
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
        execute_file(PREVIOUS_MODELET + PIIRRITE_CREATION_FILE)
    elif update_level == 2:
        execute_file(PREVIOUS_MODELET + PIIRRITE_CREATION_FILE)
        execute_file(PREVIOUS_MODELET + PIIRRITE_INSTANCIATION_FILE)

def init_piirrite_graph() -> Graph:
    copy_file(PREVIOUS_MODELET + TBOX_FILE, CURRENT_MODELET + TBOX_FILE)
    piirrite_graph = Graph()
    with open(CURRENT_MODELET + TBOX_FILE, 'r', encoding = 'utf-8') as TBox_file_content:
        piirrite_graph.parse(data = TBox_file_content.read(), format = 'turtle')

    add_SpatialEntity_to_piirrite(piirrite_graph)
    add_SpatialSegment_to_piirrite(piirrite_graph)
    add_TraversableSegment_to_piirrite(piirrite_graph)
    add_TopologicalSegment_to_piirrite(piirrite_graph)
    add_hasExtremity_to_piirrite(piirrite_graph)
    add_isExtremityOf_to_piirrite(piirrite_graph)

    update_SpatialPoint(piirrite_graph)
    update_OsmEntity(piirrite_graph)

    return piirrite_graph

def init_piirritev_graph() -> Graph:
    copy_file(PREVIOUS_MODELET + GOT_FILE, CURRENT_MODELET + GOT_FILE)
    piirritev_graph = Graph()
    with open(CURRENT_MODELET + GOT_FILE, 'r', encoding = 'utf-8') as GoT_file_content:
        piirritev_graph.parse(data = GoT_file_content.read(), format = 'turtle')

    return piirritev_graph

def init_piirrite2_graph() -> Graph:
    copy_file(PREVIOUS_MODELET + TBOX2_FILE, CURRENT_MODELET + TBOX2_FILE)
    piirrite2_graph = Graph()
    with open(CURRENT_MODELET + TBOX2_FILE, 'r', encoding = 'utf-8') as TBox2_file_content:
        piirrite2_graph.parse(data = TBox2_file_content.read(), format = 'turtle')

    return piirrite2_graph

def add_SpatialEntity_to_piirrite(piirrite_graph:Graph) -> None:
    SpatialEntity_URI = piirrite.SpatialEntity
    piirrite_graph.add((SpatialEntity_URI, RDF.type, OWL.Class))
    piirrite_graph.add((SpatialEntity_URI, RDFS.subClassOf, geo.Feature))
    piirrite_graph.add((SpatialEntity_URI, RDFS.label, Literal('Spatial entity', lang = 'en')))
    piirrite_graph.add((SpatialEntity_URI, RDFS.label, Literal('Entité spatiale', lang = 'fr')))
    piirrite_graph.add((SpatialEntity_URI,
                     RDFS.comment,
                     Literal('An entity located in a geographic space.',
                             lang = 'en')))
    piirrite_graph.add((SpatialEntity_URI,
                     RDFS.comment,
                     Literal('Une entité localisée dans un espace géographique.',
                             lang = 'fr')))
    
def add_SpatialSegment_to_piirrite(piirrite_graph:Graph):
    SpatialSegment_URI = piirrite.SpatialSegment
    piirrite_graph.add((SpatialSegment_URI, RDF.type, OWL.Class))
    piirrite_graph.add((SpatialSegment_URI, RDFS.subClassOf, piirrite.SpatialEntity))
    piirrite_graph.add((SpatialSegment_URI, RDFS.subClassOf, saref.FeatureOfInterest))
    piirrite_graph.add((SpatialSegment_URI, RDFS.label, Literal('Spatial segment', lang = 'en')))
    piirrite_graph.add((SpatialSegment_URI, RDFS.label, Literal('Segment spatial', lang = 'fr')))
    piirrite_graph.add((SpatialSegment_URI,
                     RDFS.comment,
                     Literal('A segment located in a geographic space and possibly contextualized by properties.',
                             lang = 'en')))
    piirrite_graph.add((SpatialSegment_URI,
                     RDFS.comment,
                     Literal('Un segment localisé dans un espace géographique et possiblement contextualisé par des propriétés.',
                             lang = 'fr')))

def add_TraversableSegment_to_piirrite(piirrite_graph:Graph) -> None:
    TraversableSegment_URI = piirrite.TraversableSegment
    piirrite_graph.add((TraversableSegment_URI, RDF.type, OWL.Class))
    piirrite_graph.add((TraversableSegment_URI, RDFS.subClassOf, piirrite.SpatialSegment))
    piirrite_graph.add((TraversableSegment_URI, RDFS.label, Literal('Traversable segment', lang = 'en')))
    piirrite_graph.add((TraversableSegment_URI, RDFS.label, Literal('Segment praticable', lang = 'fr')))
    piirrite_graph.add((TraversableSegment_URI,
                     RDFS.comment,
                     Literal('A spatial segment that can be traversed by users.',
                             lang = 'en')))
    piirrite_graph.add((TraversableSegment_URI,
                     RDFS.comment,
                     Literal('Un segment spatial praticable par les utilisateurs.',
                             lang = 'fr')))

def add_TopologicalSegment_to_piirrite(piirrite_graph:Graph) -> None:
    TopologicalSegment_URI = piirrite.TopologicalSegment
    piirrite_graph.add((TopologicalSegment_URI, RDF.type, OWL.Class))
    piirrite_graph.add((TopologicalSegment_URI, RDFS.subClassOf, piirrite.SpatialSegment))
    piirrite_graph.add((TopologicalSegment_URI, RDFS.label, Literal('Topological segment', lang = 'en')))
    piirrite_graph.add((TopologicalSegment_URI, RDFS.label, Literal('Segment topologique', lang = 'fr')))
    piirrite_graph.add((TopologicalSegment_URI,
                     RDFS.comment,
                     Literal('A spatial segment structuring the traversed space (e.g. wall, isoline, …).',
                             lang = 'en')))
    piirrite_graph.add((TopologicalSegment_URI,
                     RDFS.comment,
                     Literal('Un segment spatial structurant l\'espace parcouru (e.g. mur, isoligne, …).',
                             lang = 'fr')))

def add_hasExtremity_to_piirrite(piirrite_graph:Graph) -> None:
    hasExtremity_URI = piirrite.hasExtremity
    piirrite_graph.add((hasExtremity_URI, RDF.type, OWL.ObjectProperty))
    piirrite_graph.add((hasExtremity_URI, RDFS.label, Literal('has extremity', lang = 'en')))
    piirrite_graph.add((hasExtremity_URI, RDFS.label, Literal('a l\'extrémité', lang = 'fr')))
    piirrite_graph.add((hasExtremity_URI,
                     RDFS.comment,
                     Literal('Links a spatial segment to one of its two extremities, which are spatial points.',
                             lang = 'en')))
    piirrite_graph.add((hasExtremity_URI,
                     RDFS.comment,
                     Literal('Lie un segment spatial à une de ses deux extrémités, qui sont des points spatiaux.',
                             lang = 'fr')))
    piirrite_graph.add((hasExtremity_URI, RDFS.domain, piirrite.SpatialSegment))
    piirrite_graph.add((hasExtremity_URI, RDFS.range, piirrite.SpatialPoint))
    piirrite_graph.add((hasExtremity_URI, OWL.inverseOf, piirrite.isExtremityOf))

def add_isExtremityOf_to_piirrite(piirrite_graph:Graph) -> None:
    isExtremityOf_URI = piirrite.isExtremityOf
    piirrite_graph.add((isExtremityOf_URI, RDF.type, OWL.ObjectProperty))
    piirrite_graph.add((isExtremityOf_URI, RDFS.label, Literal('is an extremity of', lang = 'en')))
    piirrite_graph.add((isExtremityOf_URI, RDFS.label, Literal('est  l\'une des extrémités de', lang = 'fr')))
    piirrite_graph.add((isExtremityOf_URI,
                     RDFS.comment,
                     Literal('Links a spatial point to a spatial segment of which it is an extremity.',
                             lang = 'en')))
    piirrite_graph.add((isExtremityOf_URI,
                     RDFS.comment,
                     Literal('Lie un point spatial à un segment spatial duquel il est une extrémité.',
                             lang = 'fr')))
    piirrite_graph.add((isExtremityOf_URI, RDFS.domain, piirrite.SpatialPoint))
    piirrite_graph.add((isExtremityOf_URI, RDFS.range, piirrite.SpatialSegment))
    piirrite_graph.add((isExtremityOf_URI, OWL.inverseOf, piirrite.hasExtremity))

def update_SpatialPoint(piirrite_graph:Graph) -> None:
    SpatialPoint_URI = piirrite.SpatialPoint
    piirrite_graph.remove((SpatialPoint_URI, RDFS.subClassOf, geo.Feature))
    piirrite_graph.add((SpatialPoint_URI, RDFS.subClassOf, piirrite.SpatialEntity))

def update_OsmEntity(piirrite_graph:Graph) -> None:
    OsmEntity_URI = piirrite.OsmEntity
    piirrite_graph.remove((OsmEntity_URI, RDFS.comment, None))
    piirrite_graph.add((OsmEntity_URI,
                     RDFS.comment,
                     Literal('An OSM entity used to contextualize a spatial entity.',
                             lang = 'en')))
    piirrite_graph.add((OsmEntity_URI,
                     RDFS.comment,
                     Literal('Une entité OSM utilisée pour contextualiser une entité spatiale.',
                             lang = 'fr')))
    
###########################

def main(update_level:int):
    update_previous_modelet(update_level)
    piirrite_graph = init_piirrite_graph()
    piirritev_graph = init_piirritev_graph()
    piirrite2_graph = init_piirrite2_graph()
    
    piirrite_graph.serialize(CURRENT_MODELET + TBOX_FILE, 'turtle')
    piirritev_graph.serialize(CURRENT_MODELET + GOT_FILE, 'turtle')
    piirrite2_graph.serialize(CURRENT_MODELET + TBOX2_FILE, 'turtle')

    print(f'Ontologie et glossaire initialisés, remplis et sauvegardés avec succès.')

if __name__ == '__main__':
    update_level = 0
    main(update_level)
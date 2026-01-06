import os
import types
from rdflib import Graph
from argparse import ArgumentParser
from rdflib import Namespace, RDF, RDFS, OWL, SKOS, XSD, Literal, URIRef
from script.utilities.utilities import get_current_path, run_sparql_query, is_camel_case, flatten

CURRENT_PATH = get_current_path()
CURRENT_DIR = CURRENT_PATH.split("\\")[-1]
GoT_file = CURRENT_PATH + "/GoT.ttl"
TBox_file = CURRENT_PATH + "/TBox.ttl"
ABox_file = CURRENT_PATH + "/ABox.ttl"
SQ_dir = CURRENT_PATH + "/SQ/"

incit = Namespace("http://incit.univ-lyon1.fr/ontology/core#")
incitv = Namespace("http://incit.univ-lyon1.fr/vocabulary#")
osm = Namespace("https://www.openstreetmap.org/")
osmn = Namespace("https://www.openstreetmap.org/node/")
geo = Namespace("http://www.opengis.net/ont/geosparql#")
saref = Namespace("https://saref.etsi.org/core/")

##############
# UNIT TESTS #
##############

def exists_and_subtests_passed(graph:Graph,
                               names_list:list[str],
                               name:str,
                               test_function:types.FunctionType,
                               test_type:str,
                               verbose:bool):
    all_subtests_passed = True

    if not name in names_list:
        if verbose:
            print(f"⭕ UT_{test_type}: {name} not found")
        all_subtests_passed = False
    else:
        if not test_function(graph, verbose):
            all_subtests_passed = False
    
    return all_subtests_passed

def UT_model_prefixes(incit_graph: Graph,
                      verbose: bool = False) -> bool:
    """ Checks wether the incit ontology prefixes are correct. They are correct iff all the following conditions are met:
        - http://incit.univ-lyon1.fr/ontology/core# is prefixed by incit
        - http://incit.univ-lyon1.fr/vocabulary# is prefixed by incitv
        - http://www.w3.org/2002/07/owl# is prefixed by owl
        - http://www.w3.org/2000/01/rdf-schema# is prefixed by rdfs
        - http://www.opengis.net/ont/geosparql# is prefixed by geo
        - https://saref.etsi.org/core/ is prefixed by saref
    Args:
        incit_graph (Graph): The RDFLib graph containing the modelet TBox
        verbose (bool): wether to print detailed informations about the execution.
    Returns:
        bool: Wether the incit ontology prefixes are correct.
    """

    all_subtests_passed = True

    incit_prefixes = {str(incit_prefix): str(incit_namespace) for incit_prefix, incit_namespace in incit_graph.namespaces()}
    
    if 'incit' not in incit_prefixes or incit_prefixes['incit'] != incit:
        if verbose:
            print(f"⭕ UT_model_prefixes: Missing or incorrect incit prefix. Expected {incit}, got {incit_prefixes['incit']}.")
        all_subtests_passed = False

    if 'incitv' not in incit_prefixes or incit_prefixes['incitv'] != incitv:
        if verbose:
            print(f"⭕ UT_model_prefixes: Missing or incorrect incitv prefix. Expected {incitv}, got {incit_prefixes['incitv']}.")
        all_subtests_passed = False

    if 'owl' not in incit_prefixes or incit_prefixes['owl'] != str(OWL):
        if verbose:
            print(f"⭕ UT_model_prefixes: Missing or incorrect owl prefix. Expected {OWL}, got {incit_prefixes['owl']}.")
        all_subtests_passed = False

    if 'rdfs' not in incit_prefixes or incit_prefixes['rdfs'] != str(RDFS):
        if verbose:
            print(f"⭕ UT_model_prefixes: Missing or incorrect rdfs prefix. Expected {RDFS}, got {incit_prefixes['rdfs']}.")
        all_subtests_passed = False

    if 'geo' not in incit_prefixes or incit_prefixes['geo'] != geo:
        if verbose:
            print(f"⭕ UT_model_prefixes: Missing or incorrect geo prefix. Expected {geo}, got {incit_prefixes['geo']}.")

    if 'saref' not in incit_prefixes or incit_prefixes['saref'] != saref:
        if verbose:
            print(f"⭕ UT_model_prefixes: Missing or incorrect saref prefix. Expected {saref}, got {incit_prefixes['saref']}.")
        all_subtests_passed = False

    if all_subtests_passed:
        if verbose:
            print(f"🟢 UT_model_prefixes")
        return True
    else:
        if verbose:
            print(f"🔴 UT_model_prefixes")
        return False

def UT_model_SpatialPoint(incit_graph: Graph,
                          verbose: bool = False) -> bool:
    """ Checks wether the incit ontology SpatialPoint class is correct.
    It is correct iff all the following conditions are met:
        - The incit ontology contains a class named SpatialPoint
        - It is a rdfs:subClassOf geo:Feature
        - It is a rdfs:subClassOf saref:FeatureOfInterest
        - It has a rdfs:label in english
        - It has a rdfs:label in french
        - It has a rdfs:comment in english
        - It has a rdfs:comment in french
    Args:
        incit_graph (Graph): The RDFLib graph containing the modelet TBox and GoT.
        verbose (bool): wether to print detailed informations about the execution.
    Returns:
        bool: Wether the incit ontology SpatialPoint class is correct.
    """

    all_subtests_passed = True

    SpatialPoint_URI = incit.SpatialPoint
    
    incit_class_triples = list(incit_graph.triples((SpatialPoint_URI, None, None)))
    
    if not (SpatialPoint_URI, RDFS.subClassOf, geo.Feature) in incit_class_triples:
        if verbose:
            print(f"⭕ UT_model_classes: incit:SpatialPoint is not a subclass of geo:Feature")
        all_subtests_passed = False
    
    if not (SpatialPoint_URI, RDFS.subClassOf, saref.FeatureOfInterest) in incit_class_triples:
        if verbose:
            print(f"⭕ UT_model_classes: incit:SpatialPoint is not a subclass of saref:FeatureOfInterest")
        all_subtests_passed = False
    
    incit_class_labels = list(incit_graph.objects(SpatialPoint_URI, RDFS.label))

    incit_class_english_labels = [label for label in incit_class_labels if isinstance(label, Literal) and label.language == 'en']
    if len(incit_class_english_labels) != 1:
        if verbose:
            print(f"⭕ UT_model_classes: incit:SpatialPoint has {len(incit_class_english_labels)} english rdfs:labels, expected 1")
        all_subtests_passed = False

    incit_class_french_labels = [label for label in incit_class_labels if isinstance(label, Literal) and label.language == 'fr']
    if len(incit_class_french_labels) != 1:
        if verbose:
            print(f"⭕ UT_model_classes: incit:SpatialPoint has {len(incit_class_french_labels)} french rdfs:labels, expected 1")
        all_subtests_passed = False

    incit_class_comments = list(incit_graph.objects(SpatialPoint_URI, RDFS.comment))
    incit_class_english_comments = [comment for comment in incit_class_comments if isinstance(comment, Literal) and comment.language == 'en']
    if len(incit_class_english_comments) != 1:
        if verbose:
            print(f"⭕ UT_model_classes: incit:SpatialPoint has {len(incit_class_english_comments)} english rdfs:comments, expected 1")
        all_subtests_passed = False
    
    incit_class_french_comments = [comment for comment in incit_class_comments if isinstance(comment, Literal) and comment.language == 'fr']
    if len(incit_class_french_comments) != 1:
        if verbose:
            print(f"⭕ UT_model_classes: incit:SpatialPoint has {len(incit_class_french_comments)} french rdfs:comments, expected 1")
        all_subtests_passed = False
    
    return all_subtests_passed

def UT_model_classes(incit_graph: Graph,
                     verbose: bool = False) -> bool:
    """ Checks wether the incit ontology classes are correct.
    They are correct iff all the following conditions are met:
        - The incit ontology contains exactly one owl:Class
        - It is named SpatialPoint
        - Its subtests are passed
    Args:
        incit_graph (Graph): The RDFLib graph containing the modelet TBox and GoT.
        verbose (bool): wether to print detailed informations about the execution.
    Returns:
        bool: Wether the incit ondology classes are correct.
    """

    all_subtests_passed = True

    incit_classes = [
        incit_class for incit_class in incit_graph.subjects(RDF.type, OWL.Class)
        if str(incit_class).startswith(incit)
    ]

    if len(incit_classes) != 1:
        if verbose:
            print(f"⭕ UT_model_classes: Expected 1 incit class, found {len(incit_classes)}")
        all_subtests_passed = False
    
    incit_classes_names = [str(incit_class).split('#')[-1] for incit_class in incit_classes]

    if not exists_and_subtests_passed(incit_graph, incit_classes_names,
                                      'SpatialPoint', UT_model_SpatialPoint,
                                      'model_properties', verbose):
        all_subtests_passed = False

    if all_subtests_passed:
        if verbose:
            print(f"🟢 UT_model_classes")
        return True
    else:
        if verbose:
            print(f"🔴 UT_model_classes")
        return False

def UT_model_osmId(incit_graph: Graph,
                   verbose: bool) -> bool:
    
    return False

def UT_model_hasRelatedOsmTag(incit_graph: Graph,
                              verbose: bool) -> bool:
    
    return False

def UT_model_isOsmTagRelatedTo(incit_graph: Graph,
                               verbose: bool) -> bool:
    
    return False

def UT_model_hasContext(incit_graph: Graph,
                        verbose: bool) -> bool:
    
    return False

def UT_model_properties(incit_graph: Graph,
                        verbose: bool = False) -> bool:
    """ Checks wether the incit ontology properties are correct.
    They are correct iff all the following conditions are met:
        - The incit ontology contains exactly 4 properties
        - They are named osmId, hasRelatedOsmTag, isOsmTagRelatedTo and hasContext
        - Their respective subtests are passed
    Args:
        g (Graph): The RDFLib graph containing the modelet TBox and GoT.
        verbose (bool): wether to print detailed informations about the execution.
    Returns:
        bool: True if the model properties are correct, False otherwise.
    """

    all_subtests_passed = True

    incit_object_properties = list(incit_graph.subjects(RDF.type, OWL.ObjectProperty))
    incit_datatype_properties = list(incit_graph.subjects(RDF.type, OWL.DatatypeProperty))
    incit_properties = flatten([incit_object_properties, incit_datatype_properties])

    if len(incit_properties) != 4:
        if verbose:
            print(f"⭕ UT_model_properties: Expected 4 incit properties, found {len(incit_properties)}.")
        all_subtests_passed = False
    
    incit_properties_names = [str(incit_property).split('#')[-1] for incit_property in incit_properties]

    if not exists_and_subtests_passed(incit_graph, incit_properties_names,
                                      'osmId', UT_model_osmId,
                                      'model_properties', verbose):
        all_subtests_passed = False

    if not exists_and_subtests_passed(incit_graph, incit_properties_names,
                                      'hasRelatedOsmTag', UT_model_hasRelatedOsmTag,
                                      'model_properties', verbose):
        all_subtests_passed = False

    if not exists_and_subtests_passed(incit_graph, incit_properties_names,
                                      'isOsmTagRelatedTo', UT_model_isOsmTagRelatedTo,
                                      'model_properties', verbose):
        all_subtests_passed = False

    if not exists_and_subtests_passed(incit_graph, incit_properties_names,
                                      'hasContext', UT_model_hasContext,
                                      'model_properties', verbose):
        all_subtests_passed = False

    # incorrect_names = [
    #     str(incit_property).split("#")[-1] for incit_property in incit_properties
    #     if not str(incit_property).split("#")[-1].startswith("has") or
    #        not is_camel_case(str(incit_property).split("has")[-1])
    # ]
    # if len(incorrect_names) > 0:
    #     if verbose:
    #         print(f"⭕ UT_model_properties: {len(incorrect_names)}/{len(incit_properties)} incit propertie(s) do(es) not follow the naming scheme \"has<CamelCaseWord>\": {', '.join(map(str, incorrect_names))}")
    #     all_subtests_passed = False
    
    # not_saref_hasProperty = [
    #     str(incit_property).split('#')[-1] for incit_property in incit_properties
    #     if not (incit_property, RDF.type, saref.hasProperty) in g
    # ]
    # if len(not_saref_hasProperty) > 0:
    #     if verbose:
    #         print(f"⭕ UT_model_properties: {len(not_saref_hasProperty)}/{len(incit_properties)} incit propertie(s) are not a saref:hasProperty: {', '.join(map(str, not_saref_hasProperty))}")
    #     all_subtests_passed = False
    
    # without_domain_SpatialPoint = [
    #     str(incit_property).split('#')[-1] for incit_property in incit_properties
    #     if not (incit_property, RDFS.domain, incit.SpatialPoint) in g
    # ]
    # if len(without_domain_SpatialPoint) > 0:
    #     if verbose:
    #         print(f"⭕ UT_model_properties: {len(without_domain_SpatialPoint)}/{len(incit_properties)} incit propertie(s) do(es) not have incit:SpatialPoint as domain: {', '.join(map(str, without_domain_SpatialPoint))}")
    #     all_subtests_passed = False
    
    # without_english_label = [
    #     str(incit_property).split('#')[-1] for incit_property in incit_properties
    #     if len([label for label in g.objects(incit_property, RDFS.label)
    #             if isinstance(label, Literal) and label.language == 'en']) == 0
    # ]
    # if len(without_english_label) > 0:
    #     if verbose:
    #         print(f"⭕ UT_model_properties: {len(without_english_label)}/{len(incit_properties)} incit propertie(s) do(es) not have an english rdfs:label: {', '.join(map(str, without_english_label))}")
    #     all_subtests_passed = False

    # without_english_comment = [
    #     str(incit_property).split('#')[-1] for incit_property in incit_properties
    #     if len([comment for comment in g.objects(incit_property, RDFS.comment)
    #             if isinstance(comment, Literal) and comment.language == 'en']) == 0
    # ]
    # if len(without_english_comment) > 0:
    #     if verbose:
    #         print(f"⭕ UT_model_properties: {len(without_english_comment)}/{len(incit_properties)} incit propertie(s) do(es) not have an english rdfs:comment: {', '.join(map(str, without_english_comment))}")
    #     all_subtests_passed = False
    
    # not_rdfs_isDefinedBy_conceptScheme = [
    #     str(incit_property).split('#')[-1] for incit_property in incit_properties
    #     if not any(
    #         (incit_property, RDFS.isDefinedBy, concept_scheme) in g and
    #         (str(concept_scheme).startswith(str(incitv))) and
    #         (concept_scheme, RDF.type, SKOS.ConceptScheme) in g
    #         for concept_scheme in g.objects(incit_property, RDFS.isDefinedBy)
    #     )
    # ]
    # if len(not_rdfs_isDefinedBy_conceptScheme) > 0:
    #     if verbose:
    #         print(f"⭕ UT_model_properties: {len(not_rdfs_isDefinedBy_conceptScheme)}/{len(incit_properties)} incit propertie(s) are not rdfs:isDefinedBy a incitv:ConceptScheme: {', '.join(map(str, not_rdfs_isDefinedBy_conceptScheme))}")
    #     all_subtests_passed = False

    if all_subtests_passed:
        if verbose:
            print(f"🟢 UT_model_properties")
        return True
    else:
        if verbose:
            print(f"🔴 UT_model_properties")
        return False

def UT_glossary_prefixes(g: Graph,
                         verbose: bool = False) -> bool:
    """ Checks wether the glossary prefixes are correct. They are correct iff all the following conditions are met:
        - incitv is prefixed by http://incit.univ-lyon1.fr/vocabulary#
        - owl is prefixed by http://www.w3.org/2002/07/owl#
        - skos is prefixed by http://www.w3.org/2004/02/skos/core#
        - saref is prefixed by https://saref.etsi.org/core/
    Args:
        g (Graph): The RDFLib graph containing the modelet TBox and GoT.
        verbose (bool): wether to print detailed informations about the execution.
    Returns:
        bool: True if the glossary prefixes are correct, False otherwise.
    """

    all_subtests_passed = True

    glossary_prefixes = {str(glossary_prefix): str(glossary_namespace) for glossary_prefix, glossary_namespace in g.namespaces()}
    
    if 'incitv' not in glossary_prefixes or glossary_prefixes['incitv'] != incitv:
        if verbose:
            print(f"⭕ UT_glossary_prefixes: Missing or incorrect incitv prefix. Expected {incitv}, got {glossary_prefixes['incitv']}.")
        all_subtests_passed = False

    if 'owl' not in glossary_prefixes or glossary_prefixes['owl'] != str(OWL):
        if verbose:
            print(f"⭕ UT_glossary_prefixes: Missing or incorrect owl prefix. Expected {OWL}, got {glossary_prefixes['owl']}.")
        all_subtests_passed = False

    if 'skos' not in glossary_prefixes or glossary_prefixes['skos'] != str(SKOS):
        if verbose:
            print(f"⭕ UT_glossary_prefixes: Missing or incorrect skos prefix. Expected {SKOS}, got {glossary_prefixes['skos']}.")
        all_subtests_passed = False

    if 'saref' not in glossary_prefixes or glossary_prefixes['saref'] != saref:
        if verbose:
            print(f"⭕ UT_glossary_prefixes: Missing or incorrect saref prefix. Expected {saref}, got {glossary_prefixes['saref']}.")
        all_subtests_passed = False

    if all_subtests_passed:
        if verbose:
            print(f"🟢 UT_glossary_prefixes")
        return True
    else:
        if verbose:
            print(f"🔴 UT_glossary_prefixes")
        return False

def UT_glossary_concepts(g: Graph,
                      verbose: bool = False) -> bool:
    """ Checks wether the glossary concepts are correct. They are correct iff all the following conditions are met:
        - The glossary contains more than 0 skos:Concept that are also a saref:Property
        - Each concept is a owl:Class
        - Each concept is in incitv
        - Each concept has a skos:hiddenLabel
        - Each concept has a skos:prefLabel in english
        - Each concept is skos:inScheme something and:
            - That something exists in the graph
            - That something is a concept scheme, i.e. is a skos:ConceptScheme
            - The concept scheme has a name "CS_name" such that the concept name structure is <CS_name><CamelCaseWord> 
        - If a concept if skos:related to something, then:
            - That something exists in the graph
            - That something is a subconcept, i.e. is both a skos:Concept and a saref:hasPropertyValue
            - That subconcept has a name structure <concept name><CamelCaseWord>
        - Each concept has either a skos:definition in english or no skos:definition
            - If there are concepts with no skos:definition, a warning is raised
    Args:
        g (Graph): The RDFLib graph containing the modelet TBox and GoT.
        verbose (bool): wether to print detailed informations about the execution.
    Returns:
        bool: True if the glossary concepts are correct, False otherwise.
    """

    all_subtests_passed = True

    glossary_concepts = [
        concept for concept in g.subjects(RDF.type, SKOS.Concept)
        if (concept, RDF.type, saref.Property) in g
    ]

    if len(glossary_concepts) == 0:
        if verbose:
            print(f"⭕ UT_glossary_concepts: Expected more than 0 glossary concept.")
        all_subtests_passed = False

    nb_of_not_class = 0
    for concept in glossary_concepts:
        if not (concept, RDF.type, OWL.Class) in g:
            nb_of_not_class += 1
    if nb_of_not_class > 0:
        if verbose:
            print(f"⭕ UT_glossary_concepts: {nb_of_not_class}/{len(glossary_concepts)} glossary concept(s) are not a owl:Class.")
        all_subtests_passed = False

    nb_of_not_in_incitv = 0
    for concept in glossary_concepts:
        if not str(concept).startswith(incitv):
            nb_of_not_in_incitv += 1
    if nb_of_not_in_incitv > 0:
        if verbose:
            print(f"⭕ UT_glossary_concepts: {nb_of_not_in_incitv}/{len(glossary_concepts)} glossary concept(s) are not in incitv.")
        all_subtests_passed = False

    nb_of_no_hiddenLabel = 0
    for concept in glossary_concepts:
        hiddenLabels = [
            hiddenLabel for hiddenLabel in g.objects(concept, SKOS.hiddenLabel)
        ]
        if len(hiddenLabels) == 0:
            nb_of_no_hiddenLabel += 1
    if nb_of_no_hiddenLabel > 0:
        if verbose:
            print(f"⭕ UT_glossary_concepts: {nb_of_no_hiddenLabel}/{len(glossary_concepts)} glossary concept(s) do(es) not have a skos:hiddenLabel.")
        all_subtests_passed = False
    
    nb_of_no_prefLabel_en = 0
    for concept in glossary_concepts:
        prefLabels_en = [
            prefLabel for prefLabel in g.objects(concept, SKOS.prefLabel)
            if isinstance(prefLabel, Literal) and prefLabel.language == 'en'
        ]
        if len(prefLabels_en) == 0:
            nb_of_no_prefLabel_en += 1
    if nb_of_no_prefLabel_en > 0:
        if verbose:
            print(f"⭕ UT_glossary_concepts: {nb_of_no_prefLabel_en}/{len(glossary_concepts)} glossary concept(s) do(es) not have an english skos:prefLabel.")
        all_subtests_passed = False
    
    nb_of_incorrect_or_no_inScheme = 0
    for concept in glossary_concepts:
        schemes = [scheme for scheme in g.objects(concept, SKOS.inScheme)]
        if len(schemes) == 0:
            nb_of_incorrect_or_no_inScheme += 1
            continue
        for scheme in schemes:
            if not ((scheme, RDF.type, SKOS.ConceptScheme) in g and
                    str(concept).startswith(str(scheme)) and
                    is_camel_case(''.join([c for c in str(scheme).split(str(incitv))[-1] if not c.isdigit()]))):
                nb_of_incorrect_or_no_inScheme += 1
                break
    if nb_of_incorrect_or_no_inScheme > 0:
        if verbose:
            print(f"⭕ UT_glossary_concepts: {nb_of_incorrect_or_no_inScheme}/{len(glossary_concepts)} glossary concept(s) are either in no skos:ConceptScheme or in at least 1 incorrect skos:ConceptScheme.")
        all_subtests_passed = False
    
    nb_of_incorrect_subconcepts = 0
    nb_of_concepts_related_to_subconcepts = 0
    for concept in glossary_concepts:
        subconcepts = [subconcept for subconcept in g.objects(concept, SKOS.related)]
        if len(subconcepts) == 0:
            continue
        nb_of_concepts_related_to_subconcepts += 1
        for subconcept in subconcepts:
            if not ((subconcept, RDF.type, SKOS.Concept) in g and
                    (subconcept, RDF.type, saref.hasPropertyValue) in g and
                    str(subconcept).startswith(str(concept)) and
                    is_camel_case(''.join([c for c in str(subconcept).split(str(incitv))[-1] if not c.isdigit()]))):
                nb_of_incorrect_subconcepts += 1
                break
    if nb_of_incorrect_subconcepts > 0:
        if verbose:
            print(f"⭕ UT_glossary_concepts: {nb_of_incorrect_subconcepts}/{nb_of_concepts_related_to_subconcepts} glossary concept(s) are skos:related to at least 1 incorrect subconcept.")
        all_subtests_passed = False

    nb_of_incorrect_definition = 0 
    nb_of_no_definition = 0
    for concept in glossary_concepts:
        definitions = [definition for definition in g.objects(concept, SKOS.definition)]
        if len(definitions) == 0:
            nb_of_no_definition += 1
            continue
        for definition in definitions:
            if not (isinstance(definition, Literal) and definition.language == 'en'):
                nb_of_incorrect_definition += 1
                break
    if nb_of_incorrect_definition > 0:
        if verbose:
            print(f"⭕ UT_glossary_concepts: {nb_of_incorrect_definition}/{len(glossary_concepts)} glossary concept(s) have at least 1 an incorrect skos:definition object.")
        all_subtests_passed = False
    if nb_of_no_definition > 0:
        print(f"⚠️ UT_glossary_concepts: {nb_of_no_definition}/{len(glossary_concepts)} glossary concept(s) have no skos:definition.")

    if all_subtests_passed:
        if verbose:
            print(f"🟢 UT_glossary_concepts")
        return True
    else:
        if verbose:
            print(f"🔴 UT_glossary_concepts")
        return False

def UT_glossary_subconcepts(g: Graph,
                           verbose: bool = False) -> bool:
    """ Checks wether the glossary subconcepts are correct. They are correct iff all the following conditions are met:
        - A subconcept is defined by a skos:Concept that is also a saref:hasPropertyValue
        - Each subconcept is a owl:ObjectProperty
        - Each subconcept is in incitv
        - Each subconcept has a skos:hiddenLabel
        - Each subconcept has either a skos:definition in english or no skos:definition
            - If there are subconcepts with no skos:definition, a warning is raised
    Args:
        g (Graph): The RDFLib graph containing the modelet TBox and GoT.
        verbose (bool): wether to print detailed informations about the execution.
    Returns:
        bool: True if the glossary subconcepts are correct, False otherwise.
    """

    all_subtests_passed = True

    glossary_subconcepts = [
        subconcept for subconcept in g.subjects(RDF.type, SKOS.Concept)
        if (subconcept, RDF.type, saref.hasPropertyValue) in g
    ]

    nb_of_not_ObjectProperty = 0
    for subconcept in glossary_subconcepts:
        if not (subconcept, RDF.type, OWL.ObjectProperty) in g:
            nb_of_not_ObjectProperty += 1
    if nb_of_not_ObjectProperty > 0:
        if verbose:
            print(f"⭕ UT_glossary_subconcepts: {nb_of_not_ObjectProperty}/{len(glossary_subconcepts)} glossary subconcept(s) are a owl:ObjectProperty.")
        all_subtests_passed = False

    nb_of_not_in_incitv = 0
    for subconcept in glossary_subconcepts:
        if not str(subconcept).startswith(incitv):
            nb_of_not_in_incitv += 1
    if nb_of_not_in_incitv > 0:
        if verbose:
            print(f"⭕ UT_glossary_subconcepts: {nb_of_not_in_incitv}/{len(glossary_subconcepts)} glossary subconcept(s) are not in incitv.")
        all_subtests_passed = False

    nb_of_no_hiddenLabel = 0
    for subconcept in glossary_subconcepts:
        hiddenLabels = [
            hiddenLabel for hiddenLabel in g.objects(subconcept, SKOS.hiddenLabel)
        ]
        if len(hiddenLabels) == 0:
            nb_of_no_hiddenLabel += 1
    if nb_of_no_hiddenLabel > 0:
        if verbose:
            print(f"⭕ UT_glossary_subconcepts: {nb_of_no_hiddenLabel}/{len(glossary_subconcepts)} glossary subconcept(s) do(es) not have a skos:hiddenLabel.")
        all_subtests_passed = False
    
    nb_of_incorrect_definition = 0 
    nb_of_no_definition = 0
    for subconcept in glossary_subconcepts:
        definitions = [definition for definition in g.objects(subconcept, SKOS.definition)]
        if len(definitions) == 0:
            nb_of_no_definition += 1
            continue
        for definition in definitions:
            if not (isinstance(definition, Literal) and definition.language == 'en'):
                nb_of_incorrect_definition += 1
                break
    if nb_of_incorrect_definition > 0:
        if verbose:
            print(f"⭕ UT_glossary_subconcepts: {nb_of_incorrect_definition}/{len(glossary_subconcepts)} glossary subconcept(s) have at least 1 an incorrect skos:definition object.")
        all_subtests_passed = False
    if nb_of_no_definition > 0:
        print(f"⚠️ UT_glossary_subconcepts: {nb_of_no_definition}/{len(glossary_subconcepts)} glossary subconcept(s) have no skos:definition.")

    if all_subtests_passed:
        if verbose:
            print(f"🟢 UT_glossary_subconcepts")
        return True
    else:
        if verbose:
            print(f"🔴 UT_glossary_subconcepts")
        return False

def UT_glossary_concept_schemes(g: Graph,
                             verbose: bool = False) -> bool:
    """ Checks wether the glossary concept schemes are correct. They are correct iff all the following conditions are met:
        - The glossary contains more than 0 skos:ConceptScheme
        - Each concept scheme is a owl:Class
        - Each concept is in incitv
        - Each concept scheme has a skos:hiddenLabel
        - Each concept scheme has a skos:prefLabel in english
        - Each concept scheme has either a skos:definition in english or no skos:definition
            - If there are concepts with no skos:definition, a warning is raised
    Args:
        g (Graph): The RDFLib graph containing the modelet TBox and GoT.
        verbose (bool): wether to print detailed informations about the execution.
    Returns:
        bool: True if the glossary concept schemes are correct, False otherwise.
    """

    all_subtests_passed = True

    glossary_concept_schemes = [concept for concept in g.subjects(RDF.type, SKOS.ConceptScheme)]

    if len(glossary_concept_schemes) == 0:
        if verbose:
            print(f"⭕ UT_glossary_concept_schemes: Expected more than 0 glossary concept scheme.")
        all_subtests_passed = False
    
    nb_of_not_class = 0
    for concept_scheme in glossary_concept_schemes:
        if not (concept_scheme, RDF.type, OWL.Class) in g:
            nb_of_not_class += 1
    if nb_of_not_class > 0:
        if verbose:
            print(f"⭕ UT_glossary_concept_schemes: {nb_of_not_class}/{len(glossary_concept_schemes)} glossary concept scheme(s) are not a owl:Class.")
        all_subtests_passed = False
    
    nb_of_not_in_incitv = 0
    for concept_scheme in glossary_concept_schemes:
        if not str(concept_scheme).startswith(incitv):
            nb_of_not_in_incitv += 1
    if nb_of_not_in_incitv > 0:
        if verbose:
            print(f"⭕ UT_glossary_concept_schemes: {nb_of_not_in_incitv}/{len(glossary_concept_schemes)} glossary concept scheme(s) are not in incitv.")
        all_subtests_passed = False
    
    nb_of_no_hiddenLabel = 0
    for concept_scheme in glossary_concept_schemes:
        hiddenLabels = [
            hiddenLabel for hiddenLabel in g.objects(concept_scheme, SKOS.hiddenLabel)
        ]
        if len(hiddenLabels) == 0:
            nb_of_no_hiddenLabel += 1
    if nb_of_no_hiddenLabel > 0:
        if verbose:
            print(f"⭕ UT_glossary_concept_schemes: {nb_of_no_hiddenLabel}/{len(glossary_concept_schemes)} glossary concept scheme(s) do(es) not have a skos:hiddenLabel.")
        all_subtests_passed = False
    
    nb_of_no_prefLabel_en = 0
    for concept_scheme in glossary_concept_schemes:
        prefLabels_en = [
            prefLabel for prefLabel in g.objects(concept_scheme, SKOS.prefLabel)
            if isinstance(prefLabel, Literal) and prefLabel.language == 'en'
        ]
        if len(prefLabels_en) == 0:
            nb_of_no_prefLabel_en += 1
    if nb_of_no_prefLabel_en > 0:
        if verbose:
            print(f"⭕ UT_glossary_concept_schemes: {nb_of_no_prefLabel_en}/{len(glossary_concept_schemes)} glossary concept scheme(s) do(es) not have an english skos:prefLabel.")
        all_subtests_passed = False    

    nb_of_incorrect_definition = 0 
    nb_of_no_definition = 0
    for concept_scheme in glossary_concept_schemes:
        definitions = [definition for definition in g.objects(concept_scheme, SKOS.definition)]
        if len(definitions) == 0:
            nb_of_no_definition += 1
            continue
        for definition in definitions:
            if not (isinstance(definition, Literal) and definition.language == 'en'):
                nb_of_incorrect_definition += 1
                break
    if nb_of_incorrect_definition > 0:
        if verbose:
            print(f"⭕ UT_glossary_concept_schemes: {nb_of_incorrect_definition}/{len(glossary_concept_schemes)} glossary concept scheme(s) have at least 1 an incorrect skos:definition object.")
        all_subtests_passed = False
    if nb_of_no_definition > 0:
        print(f"⚠️ UT_glossary_concept_schemes: {nb_of_no_definition}/{len(glossary_concept_schemes)} glossary concept scheme(s) have no skos:definition.")
    

    if all_subtests_passed:
        if verbose:
            print(f"🟢 UT_glossary_concept_schemes")
        return True
    else:
        if verbose:
            print(f"🔴 UT_glossary_concept_schemes")
        return False

def model_unit_tests(incit_graph: Graph,
                     incitv_graph: Graph,
                     verbose: bool = False) -> bool:
    """ Runs the model unit tests verifying the model integrity.
    Args:
        g (Graph): The RDFLib graph containing the modelet TBox and GoT.
        verbose (bool): wether to print detailed informations about the execution.
    Returns:
        bool: True if all unit tests passed, False otherwise.
    """
    unit_tests_passed = True

    if not UT_model_prefixes(incit_graph, verbose):
        unit_tests_passed = False
    if not UT_model_classes(incit_graph, verbose):
        unit_tests_passed = False
    if not UT_model_properties(incit_graph, verbose):
        unit_tests_passed = False
    if not UT_glossary_prefixes(incitv_graph, verbose):
        unit_tests_passed = False
    if not UT_glossary_concepts(incitv_graph, verbose):
        unit_tests_passed = False
    if not UT_glossary_subconcepts(incitv_graph, verbose):
        unit_tests_passed = False
    if not UT_glossary_concept_schemes(incitv_graph, verbose):
        unit_tests_passed = False
    
    return unit_tests_passed

def UT_data_prefixes(g: Graph,
                     verbose: bool = False) -> bool:
    """ Checks wether the data prefixes are correct. They are correct iff all the following conditions are met:
        - http://incit.univ-lyon1.fr/ontology/core# is prefixed by incit
        - http://incit.univ-lyon1.fr/vocabulary# is prefixed by incitv
        - http://www.w3.org/2001/XMLSchema# is prefixed by xsd
        - http://www.opengis.net/ont/geosparql# is prefixed by geo
        - https://saref.etsi.org/core/ is prefixed by saref
        - https://www.openstreetmap.org/ is prefixed by osm
        - https://www.openstreetmap.org/node/ is prefixed by osmn
    Args:
        g (Graph): The RDFLib graph containing the modelet TBox, GoT and ABox.
        verbose (bool): wether to print detailed informations about the execution.
    Returns:
        bool: True if the data prefixes are correct, False otherwise.
    """
    
    all_subtests_passed = True

    data_prefixes = {str(data_prefix): str(data_namespace) for data_prefix, data_namespace in g.namespaces()}
    
    if 'incit' not in data_prefixes or data_prefixes['incit'] != incit:
        if verbose:
            print(f"⭕ UT_model_prefixes: Missing or incorrect incit prefix. Expected {incit}, got {data_prefixes['incit']}.")
        all_subtests_passed = False

    if 'incitv' not in data_prefixes or data_prefixes['incitv'] != incitv:
        if verbose:
            print(f"⭕ UT_model_prefixes: Missing or incorrect incitv prefix. Expected {incitv}, got {data_prefixes['incitv']}.")
        all_subtests_passed = False

    if 'xsd' not in data_prefixes or data_prefixes['xsd'] != str(XSD):
        if verbose:
            print(f"⭕ UT_model_prefixes: Missing or incorrect saref prefix. Expected {XSD}, got {data_prefixes['xsd']}.")
        all_subtests_passed = False

    if 'osm' not in data_prefixes or data_prefixes['osm'] != osm:
        if verbose:
            print(f"⭕ UT_model_prefixes: Missing or incorrect saref prefix. Expected {osm}, got {data_prefixes['osm']}.")
        all_subtests_passed = False

    if 'osmn' not in data_prefixes or data_prefixes['osmn'] != osmn:
        if verbose:
            print(f"⭕ UT_model_prefixes: Missing or incorrect saref prefix. Expected {osmn}, got {data_prefixes['osm']}.")
        all_subtests_passed = False

    if 'geo' not in data_prefixes or data_prefixes['geo'] != geo:
        if verbose:
            print(f"⭕ UT_model_prefixes: Missing or incorrect geo prefix. Expected {geo}, got {data_prefixes['geo']}.")
        all_subtests_passed = False

    if 'saref' not in data_prefixes or data_prefixes['saref'] != saref:
        if verbose:
            print(f"⭕ UT_model_prefixes: Missing or incorrect saref prefix. Expected {saref}, got {data_prefixes['saref']}.")
        all_subtests_passed = False

    if all_subtests_passed:
        if verbose:
            print(f"🟢 UT_data_prefixes")
        return True
    else:
        if verbose:
            print(f"🔴 UT_data_prefixes")
        return False

def UT_data_spatial_points(g: Graph,
                        verbose: bool = False) -> bool:
    """ Checks wether the data spatial points are correct. They are correct iff all the following conditions are met:
        - The data is composed of more than 0 incit:SpatialPoint
        - Each spatial point is in osmn
        - Each spatial point name is a list of 11 integers
        - Each spatial point is a geo:Feature
        - Each spatial point is a osm:node
        - Each spatial point has a geo:Geometry
            - This geometry is represented as a geo:wktLiteral
                - This representation is a POINT() with two coordinates
        - A spatial point can be a saref:FeatureOfInterest
            - If so, it saref:hasProperty a saref:Property
                - The predicate used as a saref:hasProperty is in incit
                - The object used as a saref:Property is a concept of incitv (i.e. is both a skos:Concept and a saref:Property)
            - A property can saref:hasPropertyValue one or several value(s). If so:
                - The predicate used as a saref:hasPropertyValue is a subconcept of incitv (i.e. is both a skos:Concept and a saref:hasProperty)
                    - This predicate is a subconcept of the property
                - Each value is typed
    Args:
        g (Graph): The RDFLib graph containing the modelet TBox, GoT and ABox.
        verbose (bool): wether to print detailed informations about the execution.
    Returns:
        bool: True if the data instances are correct, False otherwise.
    """

    all_subtests_passed = True

    # TODO: finir cette fonction
    # TODO: vérifier pourquoi le query test ne fonctionne plus
    # TODO: foutre le répertoire SAMOD derrière un endpoint de la VM
    # TODO: foutre le repértoire SAMOD dans un github

    if all_subtests_passed:
        if verbose:
            print(f"🟢 UT_data_instances")
        return True
    else:
        if verbose:
            print(f"🔴 UT_data_instances")
        return False

def data_unit_tests(g: Graph,
                     verbose: bool = False) -> bool:
    """ Runs the model unit tests verifying the model integrity.
    Args:
        g (Graph): The RDFLib graph containing the modelet TBox and GoT.
        verbose (bool): wether to print detailed informations about the execution.
    Returns:
        bool: True if all unit tests passed, False otherwise.
    """
    unit_tests_passed = True

    if not UT_data_prefixes(g, verbose):
        unit_tests_passed = False
    if not UT_data_spatial_points(g, verbose):
        unit_tests_passed = False
    
    return unit_tests_passed

################
# Bag of tests #
################

def model_test(verbose: bool = False) -> None:
    """" Runs the formal model test for the given modelet.
     Args:
         verbose (bool): wether to print detailed informations about the execution.
     """
    try:
        incit_graph = Graph()
        incit_graph.parse(TBox_file, format = 'turtle', encoding = 'utf-8')
        incitv_graph = Graph()
        incitv_graph.parse(GoT_file, format = 'turtle', encoding = 'utf-8')
        if not model_unit_tests(incit_graph, incitv_graph, verbose):
            raise Exception("failed unit tests")
        print(f"🟩 Passed model test")
    except Exception as e:
        print(f"🟥 Failed model test{': ' + str(e) if verbose else ''}")

def data_test(verbose: bool = False) -> None:
    """ Runs the formal data test for the given modelet.
    Args:
        verbose (bool): wether to print detailed informations about the execution.
    """
    try:
        g = Graph()
        g.parse(TBox_file, format = 'turtle')
        g.parse(ABox_file, format = 'turtle')
        if not data_unit_tests(g, verbose):
            raise Exception("failed unit tests")
        print(f"🟩 Passed data test")
    except Exception as e:
        print(f"🟥 Failed data test{': ' + str(e) if verbose else ''}")

def print_sparql_result(SQ_file: str,
                        result: list) -> None:
    """ Prints the result of a SPARQL query along with its natural language question.
    Args:
        SQ_file (str): The name of the SPARQL query file. It is used to extract the natural language question.
        result (list): The result of the SPARQL query as a list of strings.
    """
    CQ_id = SQ_file.removesuffix('.sparql')
    CQ_natural = None
    with open(SQ_dir + SQ_file, 'r', encoding = 'utf-8') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if line.strip() == f"# {CQ_id}":
            CQ_natural = lines[i + 1].split('#', 1)[1].strip()
            break
    if CQ_natural is None:
        raise Exception(f"Incorrect structure: missing natural language question after '# {CQ_id}'")
    print(f"{CQ_id}: {CQ_natural}") # type: ignore
    for line in result[2:]:
        line = line.strip((' |-='))
        if line != '':
            if '^^' in line:
                line = line.split('^^')[0]
            print(line)

def query_test(verbose: bool = False) -> None:
    """ Runs the formal query test for the given modelet.
    Args:
        verbose (bool): wether to print detailed informations about the execution.
    """
    try:
        for SQ_file in os.listdir(SQ_dir):
            if SQ_file.endswith('.sparql'):
                result = run_sparql_query(ABox_file, SQ_dir + SQ_file)
                if verbose:
                    print_sparql_result(SQ_file, result)
        print(f"🟩 Passed query test")
    except Exception as e:
        print(f"🟥 Failed query test{': ' + str(e) if verbose else ''}")

def main(verbose: bool = False) -> None:
    """ Main function to run the bag of tests.
    Args:
        verbose (bool): wether to print detailed informations about the execution.
    """
    print(f"Running BoT for {CURRENT_DIR}")
    model_test(verbose)
    data_test(verbose)
    query_test(verbose)

if __name__ == '__main__':
    parser = ArgumentParser(description = 'Run bag of tests')
    parser.add_argument('-v', '-verbose', '--verbose', action = 'store_true',
                        help = 'Enable verbose output')
    args = parser.parse_args()
    verbose = args.verbose
    main(verbose)

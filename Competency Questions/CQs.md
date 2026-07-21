# Group 1 — Geospatial Representation of the Navigable Environment

## Scoping CQs
### $SCQ_1$
What types of spatial entities constitute the navigable environment modelled by PIIRRITE?
*Expected answer:* Points of interest, polylines of interest, areas of interest, and navigable paths.

### $SCQ_2$
What topological relations between spatial entities does the ontology represent?
*Expected answer:* A navigable path passes by one or more points of interest via `piirrite:passesBy`.

# Relationship CQs
### $RCQ_1$
Is every navigable path associated with at least one point of interest? *Expected answer:* No — the ontology enforces no minimal `piirrite:passesBy` cardinality for `piirrite:NavigablePath` instances. Some paths are only used for navigation and not for visiting `piirrite:PointsOfInterest`.

## Validating CQs
### $VCQ_1$
What are the points of interest located within a 100-meter radius of a given user position?
*Reflects:* $R_1$​, $R_3$​ — requires proximity-based spatial filtering over `piirrite:PointOfInterest` instances.

### $VCQ_2$
Which navigable polylines pass by a given point of interest on the campus?
*Reflects:* $R_3$​, $R_5$​ — requires querying the `piirrite:passesBy` relation between paths and points.

## Foundational CQs
### $FCQ_1$
What geometric types are associated with each spatial entity class?
*Expected answer:* `sf:Point` for points of interest, `sf:LineString` for polylines, `sf:Polygon` for areas.

# Group 2 — Contextual Characterization of Spatial Entities

## Scoping CQs
### $SCQ_3$
What types of contextual properties can be attached to a spatial entity in PIIRRITE?
*Expected answer:* Any `saref:PropertyValue` instance associated via `saref:hasPropertyValue` and linked to a `saref:Property` _via_ `saref:hasProperty`.

# Relationship CQs
### $RCQ_2$
What are admissible values for a given categorical/qualitative contextual property? *Expected answer:* SKOS concepts drawn from the PIIRRITE controlled vocabulary, referenced exhaustively via `piirrite:hasAllowedValue`.

### $RCQ_3$
Must every `saref:PropertyValue` be linked to a `saref:Property`? *Expected answer:* Yes — the ontology enforces `=1 saref:isValueOfProperty.saref:Property` as a necessary condition for every `saref:PropertyValue` instance, ensuring that no value exists without a typed schema definition.

## Validating CQs
### $VCQ_3$
Which areas of interest are wheelchair-accessible? *Reflects:* $R_1$, $R_6$ — requires filtering `piirrite:AreaOfInterest` instances by a categorical `saref:PropertyValue` matching the concept `piirritev:WheelchairAccessible`.

### $VCQ_4$
Where is the nearest vending machine to a bicycle park with a capacity of at least 20? *Reflects:* $R_5​$ — requires (i) feature kind filtering, (ii) quantitative property value filtering (`xsd:integer` $\geq 20$), and (iii) spatial proximity computation via `geof:distance`.

# Group 3 — Temporal Validity of Contextual Properties

## Scoping CQs
### $SCQ_4$
Which contextual properties in PIIRRITE are subject to temporal validity constraints?
*Expected answer:* Any property value instance that is associated with a `time:Interval` via `piirrite:hasTemporalValidity`.

### $SCQ_5$
How is the temporal validity of a contextual property value represented in PIIRRITE?
*Expected answer:* Via a `time:Interval` bounded by two `time:Instant` instances (`time:hasBeginning` and `time:hasEnd`) and associated to a `saref:PropertyValue` _via_ `piirrite:hasTemporalValidity`.

## Relationship CQs
### $RCQ_4$
Is every `saref:PropertyValue` associated with exactly one temporal validity interval?
*Expected answer:* No — the ontology enforces `≤1 saref:PropertyValue.hasTemporalValidity`, meaning that a given property value instance can have 0 or 1 temporal validity window.

## Validating CQs
### $VCQ_5$
Has it rained on the campus during the past two days?
*Reflects:* $R_2$​ — requires filtering `piirrite:TemporalPropertyValue` instances whose validity interval intersects the past 48 hours and whose precipitation value exceeds zero.

### $VCQ_6$
Which navigable paths pass through the area with the highest pollen levels on 1 May 2026?
*Reflects:* $R_2$​ — requires joint reasoning over (i) temporally valid pollen-level property values on the target date, (ii) ranking by pollen concentration, and (iii) geometric intersection of path and area geometries via `geof:sfIntersects`.

# Group 4 — Matching user requirements with environmental context by profiling users

## Scoping CQ
### $SCQ_6$
How could one describe the set of contextual properties that are relevant to Anna's requirements?
This CQ reflects requirements $R_1$ trough $R_6$ and requires the system to be able to describe and understand user requirements through the use of the properties that contextualize the environment. To answer this question, the system must link a class modeling a user to classes modeling his requirements. Then, a matching against the properties of the traversed environment has to be done.

### $SCQ_7$
How could one use PIIRRITE to distinguish between (i) the _importance_ and (ii) the _flexibility_ of one of his requirements?
The feedback collected during workshops designed to introduce non-specialist audiences to the challenges of inclusive routing proved particularly instructive. It led us to identify the need to distinguish between the two scores identified in the above CQ: **importance** and **flexibility**. The former quantifies the weight a given requirement holds for the user, i.e., the degree of inconvenience experienced should it not be satisfied. The latter intervenes during the matching process between a user requirement and a contextual property of a spatial entity (e.g., a `piirrite:PointOfInterest`), and characterizes the extent to which a discrepancy between the required and the actual value affects the entity's adequacy.

### $SCQ_8$
When comparing the value expected by a user with the value of an environmental property, do the position of these two operands matter?
*Expected answer:* Yes, operators like > or < are asymmetric. The ontology assumes that i. the left operand is the environmental value and ii. the right operand is the expected value.

### $SCQ_9$
Could a couple (`piirrite:TargetProperty` ; `piirrite:ExpectedValue`) be understood as an equivalent to a `saref:PropertyValue`?
*Expected answer:* No, a `piirrite:ExpectedValue` can be an interval while the value of a `saref:PropertyValue` is a set number (if it is quantitative).

## Relationship CQ
### $RCQ_5$
How many `piirrite:Requirement` are needed to define a `piirrite:UserProfile`?
*Expected answer:* Any number of requirement, from 0 to many, can be used to define a user profile. The absence of requirement is interpreted as a total indifference of the environment by the user.

### $RCQ_6$
How many `piirrite:Condition` are needed to define a `piirrite:Requirement`?
*Expected answer:* At least one. A requirement without any condition would not serve any purpose and, more strongly, would not really exist.

## Validating CQ
### $VCQ_{7}$
What set of properties could be useful to describe Anna's requirements?
*Reflects* $R_1$ to $R_6$ ​— requires that the system is able to describe and understand user requirements through the use of the properties that contextualize the environment.

### $VCQ_{8}$
How many requirements does a user have in average?
This CQ requires the PIIRRITE ontology to have the capacity to model users and requirements, as well as being able to link a user to his own set of requirements.

# Group 5 ​— Advanced user profiling through complex requirements

## Scoping CQ
### $SCQ_9$
Is there a limit to the recursive nature of a `piirrite:ComposedCondition`?
*Expected answer:* No, a `piirrite:ComposedCondition` can be nested indefinitely. Such a condition is not necessarily irreductible (e.g. $\neg\neg A \equiv A$). This is inevitable since the operators are not interpreted _per se_ by the owl reasoner.

### $SCQ_{10}$
Which distance types does `piirrite:DistanceRequisite` support?
*Expected answer:* `From bird flight`, `Following humain pathways` and `piirrite:passesBy`.

## Relationship CQ
### $RCQ_9$
Why aren't the operators (`piirrite:EQUAL` or `piirrite:AND`) `rdfs:subClassOf` `piirrite:ComparisonOperator` and `piirrite:LogicalOperator`, but are `rdf:type`?
*Expected answer:* Because they are instances of the two classes, and not classes themselves. We cannot instantiate a `piirrite:EQUAL`.

## Validating_CQ
### $VCQ_{9}
What is the subset of Anna's requirements that use at least one distance factor?
This CQ ensures that PIIRRITE is able to link a user to the conditions defining his requirements, as well as their own relations. By providing such semantics, PIIRRITE enables the modeling of complex user requirements over the traversed environment and lays stable foundations for a comprehensive and extensive _inclusive itinerary proposition system_.

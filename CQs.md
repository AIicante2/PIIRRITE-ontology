# Group 1 — Geospatial Representation of the Navigable Environment

## Scoping CQs
### $SCQ_1$
What types of spatial entities constitute the navigable environment modelled by PIIRRITE?
*Expected answer:* Points of interest, polylines of interest, areas of interest, and navigable paths.

### $SCQ_2$
What geometric types are associated with each spatial entity class?
*Expected answer:* `sf:Point` for points of interest, `sf:LineString` for polylines, `sf:Polygon` for areas.

### $SCQ_3$
What topological relations between spatial entities does the ontology represent?
*Expected answer:* A navigable path passes by one or more points of interest via `piirrite:passesBy`.

## Validating CQs
### $VCQ_1$
What are the points of interest located within a 100-metre radius of a given user position?
*Reflects:* $R_1$​, $R_3$​ — requires proximity-based spatial filtering over `piirrite:PointOfInterest` instances.

### $VCQ_2$
Which navigable polylines pass by a given point of interest on the campus?
*Reflects:* $R_3$​, $R_5$​ — requires querying the `piirrite:passesBy` relation between paths and points.

### $VCQ_3$
Is every navigable path associated with at least one point of interest? *Expected answer:* No — the ontology enforces no minimal `piirrite:passesBy` cardinality for `piirrite:NavigablePath` instances. Some paths are only used for navigation and not for visiting `piirrite:PointsOfInterest`.

# Group 2 — Contextual Characterization of Spatial Entities

## Scoping CQs
### $SCQ_4$
What types of contextual properties can be attached to a spatial entity in PIIRRITE?
*Expected answer:* Any `saref:PropertyValue` instance associated via `saref:hasPropertyValue` and linked to a `saref:Property` _via_ `saref:hasProperty`.

### $SCQ_5$
What are admissible values for a given categorical/qualitative contextual property? *Expected answer:* SKOS concepts drawn from the PIIRRITE controlled vocabulary, referenced exhaustively via `piirrite:hasAllowedValue`.

## Validating CQs
### $VCQ_4$
Which areas of interest are wheelchair-accessible? *Reflects:* $R_1$, $R_6$ — requires filtering `piirrite:AreaOfInterest` instances by a categorical `saref:PropertyValue` matching the concept `piirritev:WheelchairAccessible`.

### $VCQ_5$
Where is the nearest vending machine to a bicycle park with a capacity of at least 20? *Reflects:* $R_5​$ — requires (i) feature kind filtering, (ii) quantitative property value filtering (`xsd:integer` $\geq 20$), and (iii) spatial proximity computation via `geof:distance`.

## Completion CQ
### $CompCQ_1$
Must every `saref:PropertyValue` be linked to a `saref:Property`? *Expected answer:* Yes — the ontology enforces `=1 saref:isValueOfProperty.saref:Property` as a necessary condition for every `saref:PropertyValue` instance, ensuring that no value exists without a typed schema definition.

## Applicability CQ
### $AppCQ_1$
Given a user who requires step-free access and proximity to a vending machine, which points of interest along a given navigable path satisfy both constraints simultaneously?
*Reflects:* $R_1$, $R_5$​ — requires joint reasoning over spatial (`piirrite:passesBy`), accessibility (`saref:PropertyValue`), and feature kind (`saref:FeatureKind`) dimensions within a single query.

# Group 3 — Temporal Validity of Contextual Properties

## Scoping CQs
### $SCQ_8$
Which contextual properties in PIIRRITE are subject to temporal validity constraints?
*Expected answer:* Any property value instance that has is associated with a `time:Interval` via `piirrite:TemporalPropertyValue`.

### $SCQ_9$
How is the temporal validity of a contextual property value represented in PIIRRITE?
*Expected answer:* Via a `time:Interval` bounded by two `time:Instant` instances (`time:hasBeginning` and `time:hasEnd`) and associated to a `saref:PropertyValue` _via_ `piirrite:hasTemporalValidity`.

## Validating CQs
### $VCQ_5$
Has it rained on the campus during the past two days?
*Reflects:* $R_2$​ — requires filtering `piirrite:TemporalPropertyValue` instances whose validity interval intersects the past 48 hours and whose precipitation value exceeds zero.

### $VCQ_6$
Which navigable paths pass through the area with the highest pollen levels on 1 May 2026?
*Reflects:* $R_2$​ — requires joint reasoning over (i) temporally valid pollen-level property values on the target date, (ii) ranking by pollen concentration, and (iii) geometric intersection of path and area geometries via `geof:sfIntersects`.

## Completion CQ
### $CompCQ_3$
Is every `saref:PropertyValue` associated with exactly one temporal validity interval?
*Expected answer:* No — the ontology enforces `≤1 saref:PropertyValue.hasTemporalValidity`, meaning that a given property value instance can have 0 or 1 temporal validity window.

## Applicability CQ
### $AppCQ_1$
Given a user sensitive to pollen and rain, which navigable paths on the campus avoid high-pollen areas and uncovered outdoor segments on a given date?
*Reflects:* $R_1$​, $R_2$​ — requires joint reasoning over temporally valid pollen-level and weather property values, geometric intersection of paths with high-pollen areas, and coverage-related contextual properties of path segments.
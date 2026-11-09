# Search strings

Scopus (TITLE-ABS-KEY), searched on 30 October 2026. IEEE Xplore (All Metadata), searched on 5 November 2026.
Record the result counts in Table 2 of the paper.

## Group A - system names (Q1, main sample, all years)

```
TITLE-ABS-KEY ( "advanced distribution management system*" OR "distribution management system*" OR {DERMS}
  OR "DER management system*" OR "distributed energy resource* management system*"
  OR ( {ADMS} AND ( "power grid*" OR "distribution grid*" OR "distribution network*"
    OR "distribution system*" OR "power system*" OR "electric utilit*" OR "power utilit*" ) ) )
```

IEEE Xplore: the same string in All Metadata, with the wildcards removed from the system-name phrases
(IEEE Xplore allows at most ten wildcards per query). Paste the exact string used here.

```
TODO: exact IEEE Xplore string
```

## Q0 - existing reviews

```
TODO: exact string used (group A AND review/survey terms)
```

## Q1f - group A, 2020-2026, articles and conference papers (subset used to size Q2-Q4)

```
<group A> AND PUBYEAR > 2019 AND PUBYEAR < 2027
  AND ( LIMIT-TO ( DOCTYPE , "ar" ) OR LIMIT-TO ( DOCTYPE , "cp" ) ) AND ( LIMIT-TO ( LANGUAGE , "English" ) )
```

## Q2 - Q1f AND group B (DER and flexibility)

```
<Q1f> AND TITLE-ABS-KEY ( flexib* OR "demand response" OR "congestion management" OR "hosting capacity"
  OR "operating envelope*" OR "DER management" OR "distributed energy resource*" )
```

## Q3 - Q1f AND group C (AI and digital)

```
<Q1f> AND TITLE-ABS-KEY ( "machine learning" OR "artificial intelligence" OR "deep learning" OR forecast*
  OR "digital twin*" OR "multi-agent" OR "state estimation" )
```

## Q4 - Q1f AND group B AND group C

## Q5 - DSO flexibility estimation, without system names (coverage check)

Q5 does not exclude the system names (no AND NOT): its overlap with Q1 is measured, not imposed.

```
TITLE-ABS-KEY ( "distribution system operator*" OR DSO )
  AND TITLE-ABS-KEY ( "flexibility estimation" OR "flexibility assessment" OR "flexibility potential"
    OR "aggregated flexibility" OR "flexibility envelope*" OR "operating envelope*" )
  AND TITLE-ABS-KEY ( platform OR system OR tool OR architecture )
```

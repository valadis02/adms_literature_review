# Search strings

Scopus (TITLE-ABS-KEY): searched on 30 October 2026; Q5 re-run on 10 November 2026.
IEEE Xplore (All Metadata): searched on 5 November 2026.

## Results (Table 2 of the paper)

| Query | Records | Note |
|---|---|---|
| Q0 Reviews (group A, review or survey, 2015 onwards) | 30 | three with the ADMS as unit, none systematic |
| Q1 Group A, all years (Scopus) | 1,459 | main sample; 24 duplicates |
| Q1 Group A, all years (IEEE Xplore) | 1,048 | 696 already in Scopus; equal to the number of included records by coincidence |
| Q1f Group A, 2020-2026, articles and conference papers | 532 | subset of Q1 |
| Q2 Q1f AND group B | 266 | 50% of Q1f |
| Q3 Q1f AND group C | 126 | 24% of Q1f |
| Q4 Q1f AND groups B and C | 43 | 8% of Q1f |
| Q5 DSO flexibility estimation, system names not required | 152 (154 on 10 Nov 2026) | no record in common with Q1 |

## Group A - system names (Q1, main sample, all years)

```
TITLE-ABS-KEY ( "advanced distribution management system*" OR "distribution management system*" OR {DERMS}
  OR "DER management system*" OR "distributed energy resource* management system*"
  OR ( {ADMS} AND ( "power grid*" OR "distribution grid*" OR "distribution network*"
    OR "distribution system*" OR "power system*" OR "electric utilit*" OR "power utilit*" ) ) )
```

First version, rejected (2,753 records; Scopus stems plain DERMS/ADMS into dermatology and adrenomedullin,
and ADMS is also an atmospheric dispersion model):

```
TITLE-ABS-KEY ( "advanced distribution management system*" OR "distribution management system*" OR DERMS
  OR "DER management system*" OR "distributed energy resource* management system*"
  OR ( ADMS AND ( grid OR "distribution network*" OR "distribution system*" OR utilit* ) ) )
```

IEEE Xplore: the same string in All Metadata, with the wildcards removed from the system-name phrases
(IEEE Xplore allows at most ten wildcards per query).

```
TODO: paste the exact IEEE Xplore string used on 5 November 2026
```

## Q0 - existing reviews

```
<group A> AND ( DOCTYPE ( re ) OR TITLE ( review OR survey OR "state of the art" OR "state-of-the-art" ) )
  AND PUBYEAR > 2014
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

```
<Q1f> AND TITLE-ABS-KEY ( <group B terms> ) AND TITLE-ABS-KEY ( <group C terms> )
```

## Q5 - DSO flexibility estimation, system names not required (coverage check)

Q5 does not exclude the system names (no AND NOT). A record on flexibility estimation inside an ADMS or
DERMS would match both Q5 and Q1, since the last group includes `system`; the overlap is measured, not
imposed. Export it as `data/raw/q5_scopus.csv` and run `python src/s06_select_fulltext.py q5`.

```
TITLE-ABS-KEY ( "distribution system operator*" OR DSO )
  AND TITLE-ABS-KEY ( "flexibility estimation" OR "flexibility assessment" OR "flexibility potential"
    OR "aggregated flexibility" OR "flexibility envelope*" OR "operating envelope*" )
  AND TITLE-ABS-KEY ( platform OR system OR tool OR architecture )
```

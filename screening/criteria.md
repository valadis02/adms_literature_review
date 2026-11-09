# Screening criteria

The same text is given to the human screener and to the LLM.

## Stage 1 - metadata (applied by script, `src/s01_merge_dedup.py`)

- Journal article, conference paper or book chapter.
- English language.

## Stage 2 - title, abstract and keywords

**Include** when the record concerns the operation of electricity distribution networks (MV/LV networks,
DSOs, utilities) **and** a DMS, ADMS, DERMS or OMS is the subject (architecture, deployment, evaluation,
test bed, standards, survey) or the explicit context of the contribution (a function developed for,
integrated in or tested within such a system), **named in the title or abstract**.

Function papers (state estimation, VVO, reconfiguration, restoration, forecasting, ...) are included when
the title or abstract presents them as a DMS/ADMS/DERMS function or for use in one.

**Exclude** with one code:

| Code | Reason |
|---|---|
| E1 | Off-topic field (medicine, chemistry, logistics, air-quality modelling such as the ADMS dispersion model, document management). |
| E2 | Transmission-only or generation-only, with no distribution system. |
| E3 | The system name (DMS, ADMS, DERMS, OMS) appears only in the keywords, not in the title or abstract. |
| E4 | Not a research contribution (front matter, announcements, company news). |
| E5 | Microgrid, home or building energy management with no link to distribution-operator systems. |

Decide `include` or `exclude`; there is no "maybe".

## Capability families (code all that apply to an included record)

| # | Family | Examples |
|---|---|---|
| 1 | Observability | state estimation, pseudo-measurements, topology and phase identification |
| 2 | Forecasting | load, generation and net load per feeder or substation |
| 3 | Operational optimisation | VVO/CVR, reconfiguration, distribution OPF |
| 4 | Reliability and resilience | OMS, FLISR, restoration, islanding |
| 5 | DER and flexibility | DERMS integration, flexibility estimation and markets, TSO-DSO coordination |
| 6 | Data and AI | data quality, anomaly detection, ML for operation |
| 7 | Digital twin and simulation | real-time models, what-if, co-simulation, test beds |
| 8 | Architecture | legacy: monolithic, on-premise; next: modular, microservices, cloud/edge, open APIs |
| 9 | Interoperability and standards | CIM, IEC 61850, IEEE 2030.5, OpenADR |
| 10 | Cybersecurity | secure communications, attack detection, zero trust |
| 11 | Operator support | situational awareness, HMI, training simulators |

## Answer format

`decision` = include | exclude; `code` = E1-E5 for exclusions (empty for inclusions);
`families` = numbers separated by `;` for inclusions (e.g. `1;5;6`).

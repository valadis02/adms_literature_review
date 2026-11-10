# Full-text extraction form

One row per full text in `data/decisions/extraction.csv` (the six Q5 records go in `extraction_q5.csv`).
The form is pre-filled by the LLM and every row is checked by the reviewer against the full text.
Values in `code font` are the allowed labels.

| Column | Content |
|---|---|
| `id` | record id from `data/interim/records.csv` (R0001, I0001, ...) |
| `bibkey` | citation key used in the paper's .bib |
| `year` | publication year |
| `sample` | `cited` (selection rule of the paper); `random` only for the optional robustness sample, not used in the paper |
| `unit` | `system`, `function`, `testbed` or `review` |
| `generation` | `legacy` or `next` (definition of Section 2.3) |
| `families` | capability families addressed, `;`-separated (e.g. `1;5;6`) |
| `named_systems` | DMS/ADMS/DERMS products or platforms named |
| `maturity` | highest level reached by the study: `concept`, `simulation`, `lab/HIL testbed`, `field pilot`, `deployed in operation/product` |
| `maturity_by_family` | optional, when families reached different levels: `6:field pilot;10:simulation` |
| `validation` | what the results were validated on (e.g. IEEE test feeder, utility data, HIL, field) |
| `validation_label` | short label for the table: `Test feeder`, `Test system`, `Utility data`, `Campus data`, `Lab`, `HIL`, `Field`, `Simulation`, `--` |
| `data_inputs` | data used or required (SCADA, AMI, GIS, PMU, DER telemetry, weather, ...) |
| `standards` | standards named (CIM, IEC 61850, DNP3, IEEE 1547, IEEE 2030.5, OpenADR, IEC 62351, ICCP), or `none` |
| `gaps_stated` | gaps or limitations stated by the authors, in their words |
| `gap_quote` | supporting quotation, with page |
| `gap_themes` | coded themes, `;`-separated: `interoperability`, `data/observability`, `field validation`, `flexibility estimation`, `cybersecurity`, `AI robustness`, `scalability/control architecture`, `test beds/digital twins`, `regulation/business case` |
| `capability_summary` | one sentence: the capability the study provides to the DMS, as stated by the authors |

## Maturity levels - decision rules

| Level | Use when |
|---|---|
| `concept` | architecture, requirements or method described without quantitative evaluation |
| `simulation` | evaluated in software only, on test feeders, synthetic data or historical utility data offline |
| `lab/HIL testbed` | run on laboratory hardware or hardware-in-the-loop (controller, power or remote HIL) |
| `field pilot` | run on a real network, for a limited period or area, as a trial |
| `deployed in operation/product` | in routine use by a utility, or offered as a product with reported deployments |

Real utility data used offline is `simulation`, not `field pilot`. The level refers to the capability the
study contributes; a deployed platform that only mentions a function does not make that function deployed
(use `maturity_by_family`).

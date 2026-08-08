# Chronicle evaluation report

Generated: 2026-08-08 16:51 UTC

## Sample

- Gold Set size: **104** questions
- Categories: fact=30, temporal=34, aggregate=26, unanswerable=14
- Dataset: MIMIC-IV Clinical Database Demo v2.2 (100 patients; eMAR for 65/100).
- Subgroup composition (descriptive only; **no fairness conclusions**): demo demographics are reported in `docs/dataset-facts.md` (57 M / 43 F; ages 21–91).
- Missingness: eMAR absent for 35 patients; diagnoses/procedures sparse for some admissions (see dataset fact sheet).

## Metrics by interpreter

| Interpreter | n | Structured-fact | Temporal-order | Provenance coverage | Abstention | Kind |
|---|---:|---:|---:|---:|---:|---:|
| oracle_template | 104 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| keyword_baseline | 104 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| llm_deepseek | 104 | 0.911 | 0.000 | 1.000 | 1.000 | 0.625 |

## LLM vs keyword baseline

Both interpreters are scored on the identical Gold Set. The keyword baseline is also the offline fallback when the LLM API is unreachable.

## Representative errors

### oracle_template

- `—`: expected `None`, got `None` — (none in sample) ()

### keyword_baseline

- `—`: expected `None`, got `None` — (none in sample) ()

### llm_deepseek

- `fact-first-k`: expected `grounded`, got `abstention` — When was the first potassium lab? (kind=abstention)
- `fact-vitals-28258130`: expected `grounded`, got `abstention` — Summarize heart rate and respiratory rate for this admission. (kind=abstention)
- `fact-meds-28258130`: expected `grounded`, got `abstention` — Which medications were administered during this admission? (kind=abstention)
- `fact-vitals-22595853`: expected `no_data`, got `abstention` — Summarize heart rate and respiratory rate for this admission. ()
- `fact-meds-22595853`: expected `grounded`, got `abstention` — Which medications were administered during this admission? (kind=abstention)

## Honest failure case

**LLM interpreter over-abstains and mishandles long temporal event names**

On the identical Gold Set, the keyword baseline now scores perfectly when questions match its patterns, while DeepSeek via Zen still over-abstains on in-scope template questions and often fails to copy long eMAR strings into `event_ordering` slots (temporal-order accuracy 0.0 in the latest run). Chronicle keeps the safety property: bad classifications become Abstention or No-Data, never fabricated rows. The oracle_template path (forced gold slots) scores 1.0 across all metrics, isolating the gap to interpretation rather than SQL/assembly.

## Notes

- Provenance coverage counts answers where every patient-level fact carries table, field, row identifier, and time (or explicit untimed Billing Context / No-Data coverage).
- Oracle interpreter forces the gold template to isolate SQL/assembly correctness from classification errors.

# Chronicle evaluation report

Generated: 2026-08-09 10:26 UTC

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

## LLM vs keyword baseline

Interpreters on this report are scored on the identical Gold Set with **pure** paths: eval sets `allow_keyword_rescue=False`, so an LLM `no_template` Abstention is never silently re-routed through keyword (and a leaked `keyword_rescue` answer is scored as error). Offline runs (`--skip-llm`) omit the LLM row; production HTTP may still label `keyword_rescue` on LLM transport/API outage only.

## Representative errors

### oracle_template

- `—`: expected `None`, got `None` — (none in sample) ()

### keyword_baseline

- `—`: expected `None`, got `None` — (none in sample) ()

## Honest failure case

**LLM over-Abstention (see full `make eval` run)**

This offline report scores oracle_template and keyword_baseline only (`make eval-offline` / `--skip-llm`). Both reach 1.0 on the 104-question Gold Set after procedure_count expectations were updated for the hosp+ICU procedures union; vitals_summary and event_ordering gold cases remain valid under the post-01–04 runners. Pure scoring disables keyword rescue so interpreters are not cross-credited. Run `make eval` (with LLM credentials) to refresh live LLM metrics; prior full runs showed LLM over-Abstention on in-scope questions and weak temporal slot-filling — safety property held (Abstention/No-Data, never fabricated rows).

## Notes

- Provenance coverage counts answers where every patient-level fact carries table, field, row identifier, and time (or explicit untimed Billing Context / No-Data coverage).
- Oracle interpreter forces the gold template to isolate SQL/assembly correctness from classification errors.

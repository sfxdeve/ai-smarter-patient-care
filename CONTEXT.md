# Chronicle

A research-and-education prototype (hackathon Track 1) that reconstructs hospital encounters from the MIMIC-IV Clinical Database Demo v2.2 and answers questions only when supporting rows exist in the structured record.

## Language

**Patient**:
A person in the dataset, identified by `subject_id`. The demo contains 100 patients.
_Avoid_: subject, case

**Admission**:
One hospital stay for a Patient, identified by `hadm_id`, spanning admit to discharge.
_Avoid_: encounter, hospitalization, visit

**ICU Stay**:
A contiguous ICU episode within an Admission, identified by `stay_id`.
_Avoid_: ICU admission

**Provenance**:
The link from a patient-level statement back to its source: table, field, row identifier, and time. Every patient-level output must carry it.
_Avoid_: citation, reference

**Abstention**:
The system's explicit refusal to answer when no Query Template fits the question or the question is out of scope (e.g. requests clinical advice). An Abstention is a correct behavior, not a failure.
_Avoid_: fallback, error

**No-Data Answer**:
A Grounded Answer reporting that a valid query returned zero rows, always accompanied by the patient's coverage for the queried table. Distinct from Abstention: the system answered, and the answer is "the record shows nothing" — never a bare "no."
_Avoid_: empty result, negative answer

**Grounded Answer**:
An answer assembled from rows actually retrieved from the dataset, each carrying Provenance. The only kind of answer the system may give.
_Avoid_: generated answer, AI answer

**Timeline Event**:
A timestamped occurrence within an Admission drawn from the curated source set: admit/discharge, transfers, labs, medication administrations, microbiology, procedures, and ICU observations. Untimestamped data (e.g. billed diagnoses) are never Timeline Events.
_Avoid_: record, entry

**Billing Context**:
Admission-level discharge coding (ICD diagnoses, DRG) shown as untimed context alongside the timeline, never on it.
_Avoid_: diagnosis timeline

**Query Template**:
A documented, parameterized SQL query the system knows how to run. The LLM's only job is choosing a Query Template and filling its slots; a question no template fits triggers an Abstention.
_Avoid_: generated SQL, dynamic query

**Gold Set**:
The evaluation question set with programmatically computed correct answers, spanning fact lookup, temporal ordering, aggregation, and deliberately unanswerable questions.
_Avoid_: test set (reserved for model-training contexts)

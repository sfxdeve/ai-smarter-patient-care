# MIMIC-IV Clinical Database Demo v2.2 — Fact Sheet

Source: https://physionet.org/content/mimic-iv-demo/2.2/ (Open Data Commons ODbL, no credentialing).
Local path: `data/mimic-iv-demo-2.2/` (gitignored). All numbers computed from the csv.gz files with pandas (script: `data/analyze.py`).

## 1. Tables

### hosp/ module

| Table | Rows | Columns |
|---|---:|---|
| admissions | 275 | subject_id, hadm_id, admittime, dischtime, deathtime, admission_type, admit_provider_id, admission_location, discharge_location, insurance, language, marital_status, race, edregtime, edouttime, hospital_expire_flag |
| d_hcpcs | 89,200 | code, category, long_description, short_description |
| d_icd_diagnoses | 109,775 | icd_code, icd_version, long_title |
| d_icd_procedures | 85,257 | icd_code, icd_version, long_title |
| d_labitems | 1,622 | itemid, label, fluid, category |
| diagnoses_icd | 4,506 | subject_id, hadm_id, seq_num, icd_code, icd_version |
| drgcodes | 454 | subject_id, hadm_id, drg_type, drg_code, description, drg_severity, drg_mortality |
| emar | 35,835 | subject_id, hadm_id, emar_id, emar_seq, poe_id, pharmacy_id, enter_provider_id, charttime, medication, event_txt, scheduletime, storetime |
| emar_detail | 72,018 | subject_id, emar_id, emar_seq, parent_field_ordinal, administration_type, pharmacy_id, barcode_type, reason_for_no_barcode, complete_dose_not_given, dose_due, dose_due_unit, dose_given, dose_given_unit, will_remainder_of_dose_be_given, product_amount_given, product_unit, product_code, product_description, product_description_other, prior_infusion_rate, infusion_rate, infusion_rate_adjustment, infusion_rate_adjustment_amount, infusion_rate_unit, route, infusion_complete, completion_interval, new_iv_bag_hung, continued_infusion_in_other_location, restart_interval, side, site, non_formulary_visual_verification |
| hcpcsevents | 61 | subject_id, hadm_id, chartdate, hcpcs_cd, seq_num, short_description |
| labevents | 107,727 | labevent_id, subject_id, hadm_id, specimen_id, itemid, order_provider_id, charttime, storetime, value, valuenum, valueuom, ref_range_lower, ref_range_upper, flag, priority, comments |
| microbiologyevents | 2,899 | microevent_id, subject_id, hadm_id, micro_specimen_id, order_provider_id, chartdate, charttime, spec_itemid, spec_type_desc, test_seq, storedate, storetime, test_itemid, test_name, org_itemid, org_name, isolate_num, quantity, ab_itemid, ab_name, dilution_text, dilution_comparison, dilution_value, interpretation, comments |
| omr | 2,964 | subject_id, chartdate, seq_num, result_name, result_value |
| patients | 100 | subject_id, gender, anchor_age, anchor_year, anchor_year_group, dod |
| pharmacy | 15,306 | subject_id, hadm_id, pharmacy_id, poe_id, starttime, stoptime, medication, proc_type, status, entertime, verifiedtime, route, frequency, disp_sched, infusion_type, sliding_scale, lockout_interval, basal_rate, one_hr_max, doses_per_24_hrs, duration, duration_interval, expiration_value, expiration_unit, expirationdate, dispensation, fill_quantity |
| poe | 45,154 | poe_id, poe_seq, subject_id, hadm_id, ordertime, order_type, order_subtype, transaction_type, discontinue_of_poe_id, discontinued_by_poe_id, order_provider_id, order_status |
| poe_detail | 3,795 | poe_id, poe_seq, subject_id, field_name, field_value |
| prescriptions | 18,087 | subject_id, hadm_id, pharmacy_id, poe_id, poe_seq, order_provider_id, starttime, stoptime, drug_type, drug, formulary_drug_cd, gsn, ndc, prod_strength, form_rx, dose_val_rx, dose_unit_rx, form_val_disp, form_unit_disp, doses_per_24_hrs, route |
| procedures_icd | 722 | subject_id, hadm_id, seq_num, chartdate, icd_code, icd_version |
| provider | 40,508 | provider_id |
| services | 319 | subject_id, hadm_id, transfertime, prev_service, curr_service |
| transfers | 1,190 | subject_id, hadm_id, transfer_id, eventtype, careunit, intime, outtime |

### icu/ module

| Table | Rows | Columns |
|---|---:|---|
| caregiver | 15,468 | caregiver_id |
| chartevents | 668,862 | subject_id, hadm_id, stay_id, caregiver_id, charttime, storetime, itemid, value, valuenum, valueuom, warning |
| d_items | 4,014 | itemid, label, abbreviation, linksto, category, unitname, param_type, lownormalvalue, highnormalvalue |
| datetimeevents | 15,280 | subject_id, hadm_id, stay_id, caregiver_id, charttime, storetime, itemid, value, valueuom, warning |
| icustays | 140 | subject_id, hadm_id, stay_id, first_careunit, last_careunit, intime, outtime, los |
| ingredientevents | 25,728 | subject_id, hadm_id, stay_id, caregiver_id, starttime, endtime, storetime, itemid, amount, amountuom, rate, rateuom, orderid, linkorderid, statusdescription, originalamount, originalrate |
| inputevents | 20,404 | subject_id, hadm_id, stay_id, caregiver_id, starttime, endtime, storetime, itemid, amount, amountuom, rate, rateuom, orderid, linkorderid, ordercategoryname, secondaryordercategoryname, ordercomponenttypedescription, ordercategorydescription, patientweight, totalamount, totalamountuom, isopenbag, continueinnextdept, statusdescription, originalamount, originalrate |
| outputevents | 9,362 | subject_id, hadm_id, stay_id, caregiver_id, charttime, storetime, itemid, value, valueuom |
| procedureevents | 1,468 | subject_id, hadm_id, stay_id, caregiver_id, starttime, endtime, storetime, itemid, value, valueuom, location, locationcategory, orderid, linkorderid, ordercategoryname, ordercategorydescription, patientweight, isopenbag, continueinnextdept, statusdescription, ORIGINALAMOUNT, ORIGINALRATE |

## 2. Core counts

| Entity | Count |
|---|---:|
| Distinct patients (subject_id) | 100 |
| Hospital admissions (hadm_id) | 275 |
| ICU stays (stay_id) | 140 |
| Patients with ≥1 ICU stay | 100 (all of them) |
| Admissions with ≥1 ICU stay | 128 of 275 |

Demographics: 57 M / 43 F; anchor_age min 21, median 63, max 91.

## 3. Length of stay

| Metric | Hospital LOS (days) | ICU LOS (days) |
|---|---:|---:|
| n | 275 | 140 |
| min | 0.05 | 0.02 |
| median | 4.85 | 2.16 |
| mean | 6.88 | 3.68 |
| max | 44.93 | 20.53 |
| < 2 days | 55 | 66 |
| 2–7 days | 129 | 54 |
| > 7 days | 91 | 20 |

Hospital LOS = dischtime − admittime; ICU LOS = `icustays.los`.

## 4. Mortality

- In-hospital deaths (`hospital_expire_flag = 1`): **15 admissions**, covering **15 distinct patients**.
- Patients with a date of death recorded (`patients.dod` non-null): 31 of 100 (includes post-discharge deaths).

## 5. Top 20 items

### labevents (joined to d_labitems)

| Rank | Label | Fluid | Count |
|---:|---|---|---:|
| 1 | Potassium | Blood | 3,022 |
| 2 | Sodium | Blood | 3,007 |
| 3 | Creatinine | Blood | 3,003 |
| 4 | Chloride | Blood | 2,981 |
| 5 | Urea Nitrogen | Blood | 2,974 |
| 6 | Hematocrit | Blood | 2,913 |
| 7 | Bicarbonate | Blood | 2,863 |
| 8 | Anion Gap | Blood | 2,860 |
| 9 | Platelet Count | Blood | 2,827 |
| 10 | Hemoglobin | Blood | 2,787 |
| 11 | RDW | Blood | 2,760 |
| 12 | Red Blood Cells | Blood | 2,760 |
| 13 | White Blood Cells | Blood | 2,760 |
| 14 | MCHC | Blood | 2,760 |
| 15 | MCV | Blood | 2,760 |
| 16 | MCH | Blood | 2,760 |
| 17 | Glucose | Blood | 2,711 |
| 18 | Magnesium | Blood | 2,470 |
| 19 | Calcium, Total | Blood | 2,377 |
| 20 | Phosphate | Blood | 2,337 |

### chartevents (joined to d_items)

| Rank | Label | Category | Count |
|---:|---|---|---:|
| 1 | Safety Measures | Restraint/Support Systems | 19,330 |
| 2 | Respiratory Rate | Respiratory | 13,913 |
| 3 | Heart Rate | Routine Vital Signs | 13,913 |
| 4 | O2 saturation pulseoxymetry | Respiratory | 13,540 |
| 5 | Heart Rhythm | Routine Vital Signs | 12,460 |
| 6 | Ectopy Type 1 | Routine Vital Signs | 11,044 |
| 7 | Non Invasive Blood Pressure diastolic | Routine Vital Signs | 8,349 |
| 8 | Non Invasive Blood Pressure systolic | Routine Vital Signs | 8,347 |
| 9 | Non Invasive Blood Pressure mean | Routine Vital Signs | 8,342 |
| 10 | Less Restrictive Measures | Restraint/Support Systems | 7,675 |
| 11 | Arterial Blood Pressure mean | Routine Vital Signs | 5,560 |
| 12 | Arterial Blood Pressure systolic | Routine Vital Signs | 5,525 |
| 13 | Arterial Blood Pressure diastolic | Routine Vital Signs | 5,524 |
| 14 | Impaired Tissue Perfusion NCP - Interventions | Care Plans | 5,463 |
| 15 | Altered Respiratory Status NCP - Interventions | Care Plans | 5,398 |
| 16 | Pain Management | Pain/Sedation | 5,371 |
| 17 | Head of Bed | Treatments | 5,124 |
| 18 | Turn | Treatments | 5,045 |
| 19 | Activity Tolerance | Treatments | 4,863 |
| 20 | Position | Treatments | 4,742 |

## 6. Missingness highlights

- **No table is empty**, but some are very sparse: `hcpcsevents` (61 rows), `services` (319), `drgcodes` (454), `procedures_icd` (722).
- The demo has **no clinical notes** (the note module of MIMIC-IV is a separate, credentialed dataset) and no CXR/ED linkage.
- Null rates in `admissions` key columns:

| Column | Null % |
|---|---:|
| deathtime | 94.5% (null unless died in hospital) |
| dischtime | 0.0% |
| admission_location | 0.0% |
| discharge_location | 15.3% |
| edregtime / edouttime | 33.8% (null when not admitted via ED) |
| marital_status | 4.4% |
| race / insurance / language | 0.0% |

- `emar` covers only 65 of 100 patients (eMAR data only exists for later-era admissions).
- Dates are deidentified (shifted into 2110–2210 range); ages are anchor ages, so ages > 89 appear as 91.

## 7. Event-table coverage

| Table | Rows | Distinct patients |
|---|---:|---:|
| prescriptions | 18,087 | 100 |
| emar | 35,835 | 65 |
| microbiologyevents | 2,899 | 97 |
| diagnoses_icd | 4,506 | 100 |
| procedures_icd | 722 | 92 |

## 8. Notes for choosing a hackathon track

Feasible outcome labels with this 100-patient demo:

| Candidate outcome | Positive / total | Verdict |
|---|---|---|
| Hospital LOS category (<2d / 2–7d / >7d) | 55 / 129 / 91 of 275 admissions | Best balanced target; enough per class |
| ICU LOS > 7d | 20 of 140 stays | Usable but small positive class |
| In-hospital mortality | 15 of 275 admissions (15 patients) | Very few positives; demo-quality only, expect unstable metrics |
| ICU readmission within same hospitalization (>1 ICU stay per hadm_id) | 9 of 128 hadm with ICU | Too rare to model |
| 30-day hospital readmission | 53 admissions followed by a readmission ≤30d; 48 of 100 patients have multiple admissions | Reasonable prevalence, but only 100 patients |

Other considerations:

- Every patient has an ICU stay and labs, and chartevents is dense (669k rows, vitals every ~hour), so **time-series features (vitals + labs) are the richest signal** in the demo.
- With only 100 patients, treat any modeling as a pipeline demo; the same code scales to full MIMIC-IV (~300k patients) once credentialed.
- LOS bucket classification or 30-day readmission are the only outcomes with enough positives for a train/test split; mortality and ICU bounce-back are better framed as descriptive analyses or rule-based demos.

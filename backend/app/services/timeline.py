from __future__ import annotations

from datetime import datetime
from typing import Any

import duckdb

from app.db import VITAL_ITEMIDS, fetchall_dicts
from app.models import (
    BillingCode,
    BillingContext,
    IcuStayInterval,
    Provenance,
    TimelineEvent,
    TimelineResponse,
)

EVENT_TYPES = {
    "admit_discharge",
    "transfer",
    "lab",
    "medication",
    "microbiology",
    "procedure",
    "icu_observation",
}


def _ts(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in (
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(value[:26], fmt)
        except ValueError:
            continue
    return None


def build_timeline(
    con: duckdb.DuckDBPyConnection,
    subject_id: int,
    hadm_id: int,
    event_types: set[str] | None = None,
    start: str | None = None,
    end: str | None = None,
) -> TimelineResponse:
    types = event_types or set(EVENT_TYPES)
    unknown = types - EVENT_TYPES
    if unknown:
        raise ValueError(f"Unknown event type(s): {sorted(unknown)}")

    start_dt = _parse_ts(start) if start else None
    end_dt = _parse_ts(end) if end else None
    if start and start_dt is None:
        raise ValueError(f"Invalid start time: {start}")
    if end and end_dt is None:
        raise ValueError(f"Invalid end time: {end}")
    if start_dt and end_dt and start_dt > end_dt:
        raise ValueError("start must be <= end")

    events: list[TimelineEvent] = []

    if "admit_discharge" in types:
        adm = fetchall_dicts(
            con,
            """
            SELECT hadm_id, CAST(admittime AS VARCHAR) AS admittime,
                   CAST(dischtime AS VARCHAR) AS dischtime,
                   admission_type, admission_location, discharge_location
            FROM admissions WHERE subject_id = ? AND hadm_id = ?
            """,
            [subject_id, hadm_id],
        )
        for r in adm:
            events.append(
                TimelineEvent(
                    event_type="admit_discharge",
                    time=r["admittime"],
                    label=f"Admitted ({r['admission_type'] or 'unknown type'})",
                    detail=r["admission_location"],
                    provenance=Provenance(
                        table="admissions",
                        field="admittime",
                        row_id=hadm_id,
                        time=r["admittime"],
                    ),
                )
            )
            events.append(
                TimelineEvent(
                    event_type="admit_discharge",
                    time=r["dischtime"],
                    label="Discharged",
                    detail=r["discharge_location"],
                    provenance=Provenance(
                        table="admissions",
                        field="dischtime",
                        row_id=hadm_id,
                        time=r["dischtime"],
                    ),
                )
            )

    if "transfer" in types:
        for r in fetchall_dicts(
            con,
            """
            SELECT transfer_id, eventtype, careunit,
                   CAST(intime AS VARCHAR) AS intime,
                   CAST(outtime AS VARCHAR) AS outtime
            FROM transfers WHERE subject_id = ? AND hadm_id = ?
            """,
            [subject_id, hadm_id],
        ):
            events.append(
                TimelineEvent(
                    event_type="transfer",
                    time=r["intime"],
                    end_time=r["outtime"],
                    label=f"Transfer: {r['eventtype'] or 'event'}",
                    detail=r["careunit"],
                    provenance=Provenance(
                        table="transfers",
                        field="intime",
                        row_id=int(r["transfer_id"]),
                        time=r["intime"],
                    ),
                )
            )

    if "lab" in types:
        for r in fetchall_dicts(
            con,
            """
            SELECT l.labevent_id, CAST(l.charttime AS VARCHAR) AS charttime,
                   l.value, l.valuenum, l.valueuom, l.flag, d.label, d.fluid
            FROM labevents l
            LEFT JOIN d_labitems d ON l.itemid = d.itemid
            WHERE l.subject_id = ? AND l.hadm_id = ?
            """,
            [subject_id, hadm_id],
        ):
            val = r["value"] if r["value"] is not None else r["valuenum"]
            unit = f" {r['valueuom']}" if r["valueuom"] else ""
            flag = f" [{r['flag']}]" if r["flag"] else ""
            events.append(
                TimelineEvent(
                    event_type="lab",
                    time=r["charttime"],
                    label=r["label"] or "Lab",
                    detail=f"{val}{unit}{flag}" if val is not None else r["fluid"],
                    provenance=Provenance(
                        table="labevents",
                        field="valuenum",
                        row_id=int(r["labevent_id"]),
                        time=r["charttime"],
                    ),
                )
            )

    if "medication" in types:
        for r in fetchall_dicts(
            con,
            """
            SELECT emar_id, CAST(charttime AS VARCHAR) AS charttime,
                   medication, event_txt
            FROM emar WHERE subject_id = ? AND hadm_id = ?
            """,
            [subject_id, hadm_id],
        ):
            events.append(
                TimelineEvent(
                    event_type="medication",
                    time=r["charttime"],
                    label=r["medication"] or "Medication",
                    detail=r["event_txt"],
                    provenance=Provenance(
                        table="emar",
                        field="medication",
                        row_id=str(r["emar_id"]),
                        time=r["charttime"],
                    ),
                )
            )

    if "microbiology" in types:
        for r in fetchall_dicts(
            con,
            """
            SELECT microevent_id,
                   CAST(COALESCE(charttime, chartdate) AS VARCHAR) AS event_time,
                   spec_type_desc, test_name, org_name, interpretation
            FROM microbiologyevents
            WHERE subject_id = ? AND hadm_id = ?
            """,
            [subject_id, hadm_id],
        ):
            org = r["org_name"] or "no organism"
            events.append(
                TimelineEvent(
                    event_type="microbiology",
                    time=r["event_time"],
                    label=r["test_name"] or r["spec_type_desc"] or "Microbiology",
                    detail=f"{org}"
                    + (f" ({r['interpretation']})" if r["interpretation"] else ""),
                    provenance=Provenance(
                        table="microbiologyevents",
                        field="org_name",
                        row_id=int(r["microevent_id"]),
                        time=r["event_time"],
                    ),
                )
            )

    if "procedure" in types:
        for r in fetchall_dicts(
            con,
            """
            SELECT p.seq_num, CAST(p.chartdate AS VARCHAR) AS chartdate,
                   p.icd_code, d.long_title
            FROM procedures_icd p
            LEFT JOIN d_icd_procedures d
              ON p.icd_code = d.icd_code AND p.icd_version = d.icd_version
            WHERE p.subject_id = ? AND p.hadm_id = ?
            """,
            [subject_id, hadm_id],
        ):
            events.append(
                TimelineEvent(
                    event_type="procedure",
                    time=r["chartdate"],
                    label=r["long_title"] or f"Procedure {r['icd_code']}",
                    detail=str(r["icd_code"]),
                    provenance=Provenance(
                        table="procedures_icd",
                        field="icd_code",
                        row_id=f"{hadm_id}:{r['seq_num']}",
                        time=r["chartdate"],
                    ),
                )
            )
        for r in fetchall_dicts(
            con,
            """
            SELECT pe.orderid, pe.stay_id,
                   CAST(pe.starttime AS VARCHAR) AS starttime,
                   CAST(pe.endtime AS VARCHAR) AS endtime,
                   d.label
            FROM procedureevents pe
            LEFT JOIN d_items d ON pe.itemid = d.itemid
            WHERE pe.subject_id = ? AND pe.hadm_id = ?
            """,
            [subject_id, hadm_id],
        ):
            events.append(
                TimelineEvent(
                    event_type="procedure",
                    time=r["starttime"],
                    end_time=r["endtime"],
                    label=r["label"] or "ICU procedure",
                    stay_id=int(r["stay_id"]) if r["stay_id"] is not None else None,
                    provenance=Provenance(
                        table="procedureevents",
                        field="starttime",
                        row_id=int(r["orderid"]) if r["orderid"] is not None else None,
                        time=r["starttime"],
                    ),
                )
            )

    if "icu_observation" in types:
        item_list = ", ".join(str(i) for i in VITAL_ITEMIDS)
        raw_obs = fetchall_dicts(
            con,
            f"""
            SELECT c.subject_id, c.hadm_id, c.stay_id, c.itemid,
                   CAST(c.charttime AS VARCHAR) AS charttime,
                   c.value, c.valuenum, c.valueuom, d.label, d.category,
                   ROW_NUMBER() OVER (
                     PARTITION BY c.stay_id, c.itemid ORDER BY c.charttime
                   ) AS rn
            FROM chartevents c
            LEFT JOIN d_items d ON c.itemid = d.itemid
            WHERE c.subject_id = ? AND c.hadm_id = ?
              AND c.itemid IN ({item_list})
            ORDER BY c.charttime
            """,
            [subject_id, hadm_id],
        )
        # Band by stay_id + itemid (collapsible high-volume observations)
        bands: dict[str, list[TimelineEvent]] = {}
        for r in raw_obs:
            key = f"{r['stay_id']}:{r['itemid']}"
            val = r["valuenum"] if r["valuenum"] is not None else r["value"]
            unit = f" {r['valueuom']}" if r["valueuom"] else ""
            ev = TimelineEvent(
                event_type="icu_observation",
                time=r["charttime"],
                label=r["label"] or f"item {r['itemid']}",
                detail=f"{val}{unit}" if val is not None else None,
                stay_id=int(r["stay_id"]) if r["stay_id"] is not None else None,
                provenance=Provenance(
                    table="chartevents",
                    field="valuenum",
                    row_id=f"{r['stay_id']}:{r['itemid']}:{r['charttime']}",
                    time=r["charttime"],
                ),
            )
            bands.setdefault(key, []).append(ev)

        for key, band_events in bands.items():
            first = band_events[0]
            last = band_events[-1]
            events.append(
                TimelineEvent(
                    event_type="icu_observation",
                    time=first.time,
                    end_time=last.time,
                    label=first.label,
                    detail=f"{len(band_events)} observations",
                    stay_id=first.stay_id,
                    band_key=key,
                    band_count=len(band_events),
                    band_events=band_events,
                    provenance=first.provenance,
                )
            )

    def in_window(ev: TimelineEvent) -> bool:
        t = _parse_ts(ev.time)
        if t is None:
            return True
        if start_dt and t < start_dt:
            return False
        if end_dt and t > end_dt:
            return False
        return True

    events = [e for e in events if in_window(e)]
    events.sort(key=lambda e: (_parse_ts(e.time) or datetime.min, e.event_type, e.label))

    icu_stays = [
        IcuStayInterval(
            stay_id=int(r["stay_id"]),
            first_careunit=r["first_careunit"],
            last_careunit=r["last_careunit"],
            intime=r["intime"],
            outtime=r["outtime"],
            los=float(r["los"]) if r["los"] is not None else None,
            provenance=Provenance(
                table="icustays",
                field="intime",
                row_id=int(r["stay_id"]),
                time=r["intime"],
            ),
        )
        for r in fetchall_dicts(
            con,
            """
            SELECT stay_id, first_careunit, last_careunit,
                   CAST(intime AS VARCHAR) AS intime,
                   CAST(outtime AS VARCHAR) AS outtime, los
            FROM icustays WHERE subject_id = ? AND hadm_id = ?
            ORDER BY intime
            """,
            [subject_id, hadm_id],
        )
    ]

    return TimelineResponse(
        subject_id=subject_id,
        hadm_id=hadm_id,
        events=events,
        icu_stays=icu_stays,
        filters_applied={
            "event_types": sorted(types),
            "start": start,
            "end": end,
        },
    )


def billing_context(
    con: duckdb.DuckDBPyConnection, subject_id: int, hadm_id: int
) -> BillingContext:
    diagnoses = [
        BillingCode(
            code=str(r["icd_code"]),
            title=r["long_title"],
            seq_num=int(r["seq_num"]) if r["seq_num"] is not None else None,
            code_type="icd_diagnosis",
            provenance=Provenance(
                table="diagnoses_icd",
                field="icd_code",
                row_id=f"{hadm_id}:{r['seq_num']}",
                time=None,
            ),
        )
        for r in fetchall_dicts(
            con,
            """
            SELECT d.seq_num, d.icd_code, t.long_title
            FROM diagnoses_icd d
            LEFT JOIN d_icd_diagnoses t
              ON d.icd_code = t.icd_code AND d.icd_version = t.icd_version
            WHERE d.subject_id = ? AND d.hadm_id = ?
            ORDER BY d.seq_num
            """,
            [subject_id, hadm_id],
        )
    ]
    drg_codes = [
        BillingCode(
            code=str(r["drg_code"]),
            title=r["description"],
            code_type=str(r["drg_type"] or "drg"),
            provenance=Provenance(
                table="drgcodes",
                field="drg_code",
                row_id=f"{hadm_id}:{r['drg_code']}",
                time=None,
            ),
        )
        for r in fetchall_dicts(
            con,
            """
            SELECT drg_type, drg_code, description
            FROM drgcodes WHERE subject_id = ? AND hadm_id = ?
            """,
            [subject_id, hadm_id],
        )
    ]
    return BillingContext(
        subject_id=subject_id,
        hadm_id=hadm_id,
        diagnoses=diagnoses,
        drg_codes=drg_codes,
    )

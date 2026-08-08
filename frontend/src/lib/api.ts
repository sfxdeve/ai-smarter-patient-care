const API_BASE = import.meta.env.VITE_API_BASE ?? ""

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ?? JSON.stringify(body)
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail))
  }
  return res.json() as Promise<T>
}

export type Provenance = {
  table: string
  field: string
  row_id: string | number | null
  time: string | null
}

export type TableCoverage = {
  table: string
  has_rows: boolean
  row_count: number
  note: string | null
}

export type PatientSummary = {
  subject_id: number
  gender: string | null
  anchor_age: number | null
  anchor_year_group: string | null
  dod: string | null
  admission_count: number
  coverage: TableCoverage[]
}

export type AdmissionChapter = {
  hadm_id: number
  admittime: string | null
  dischtime: string | null
  admission_type: string | null
  admission_location: string | null
  discharge_location: string | null
  hospital_expire_flag: number | null
  icu_stay_count: number
}

export type PatientDetail = {
  subject_id: number
  gender: string | null
  anchor_age: number | null
  anchor_year: number | null
  anchor_year_group: string | null
  dod: string | null
  coverage: TableCoverage[]
  admissions: AdmissionChapter[]
  date_shift_note: string
}

export type TimelineEvent = {
  event_type: string
  time: string | null
  end_time: string | null
  label: string
  detail: string | null
  stay_id: number | null
  provenance: Provenance
  band_key: string | null
  band_count: number | null
  band_events: TimelineEvent[] | null
}

export type IcuStayInterval = {
  stay_id: number
  first_careunit: string | null
  last_careunit: string | null
  intime: string | null
  outtime: string | null
  los: number | null
  provenance: Provenance
}

export type TimelineResponse = {
  subject_id: number
  hadm_id: number
  events: TimelineEvent[]
  icu_stays: IcuStayInterval[]
  filters_applied: Record<string, unknown>
}

export type BillingCode = {
  code: string
  title: string | null
  seq_num: number | null
  code_type: string
  provenance: Provenance
}

export type BillingContext = {
  subject_id: number
  hadm_id: number
  notice: string
  diagnoses: BillingCode[]
  drg_codes: BillingCode[]
}

export type QaResponse = {
  kind: "grounded" | "no_data" | "abstention"
  question: string
  subject_id: number
  hadm_id: number | null
  summary: string
  rows: Record<string, unknown>[]
  provenance: Provenance[]
  coverage: TableCoverage[]
  template_id: string | null
  slots: Record<string, unknown>
  sql: string | null
  interpreter: "llm" | "keyword" | "keyword_fallback" | "fake"
  abstention_reason: string | null
  is_ai_phrasing: boolean
}

export type ExampleQuestion = {
  question: string
  template_id: string
  description: string
}

export const api = {
  health: () => request<{ status: string; patient_count: number; egress_note: string }>("/health"),
  safetyNotice: () => request<{ notice: string }>("/meta/safety-notice"),
  patients: () => request<PatientSummary[]>("/patients"),
  patient: (subjectId: number) => request<PatientDetail>(`/patients/${subjectId}`),
  timeline: (
    subjectId: number,
    hadmId: number,
    params?: { event_types?: string; start?: string; end?: string }
  ) => {
    const q = new URLSearchParams()
    if (params?.event_types) q.set("event_types", params.event_types)
    if (params?.start) q.set("start", params.start)
    if (params?.end) q.set("end", params.end)
    const qs = q.toString()
    return request<TimelineResponse>(
      `/patients/${subjectId}/admissions/${hadmId}/timeline${qs ? `?${qs}` : ""}`
    )
  },
  billing: (subjectId: number, hadmId: number) =>
    request<BillingContext>(`/patients/${subjectId}/admissions/${hadmId}/billing-context`),
  qa: (body: { question: string; subject_id: number; hadm_id?: number | null }) =>
    request<QaResponse>("/qa", { method: "POST", body: JSON.stringify(body) }),
  qaExamples: () => request<ExampleQuestion[]>("/qa/examples"),
  eventTypes: () => request<string[]>("/meta/event-types"),
}

export type AdmissionSearch = {
  types?: string
  from?: string
  to?: string
}

export const ALL_EVENT_TYPES = [
  "admit_discharge",
  "transfer",
  "lab",
  "medication",
  "microbiology",
  "procedure",
  "icu_observation",
] as const

export type EventType = (typeof ALL_EVENT_TYPES)[number]

export function parseTypes(types: string | undefined): EventType[] {
  if (!types?.trim()) return [...ALL_EVENT_TYPES]
  const wanted = new Set(
    types
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean)
  )
  return ALL_EVENT_TYPES.filter((t) => wanted.has(t))
}

export function searchToForm(search: AdmissionSearch) {
  return {
    types: parseTypes(search.types),
    from: search.from ?? "",
    to: search.to ?? "",
  }
}

export function formToSearch(values: {
  types: string[]
  from: string
  to: string
}): AdmissionSearch {
  const types = values.types.filter((t): t is EventType =>
    (ALL_EVENT_TYPES as readonly string[]).includes(t)
  )
  const allSelected =
    types.length === ALL_EVENT_TYPES.length &&
    ALL_EVENT_TYPES.every((t) => types.includes(t))
  return {
    types: allSelected ? undefined : types.join(","),
    from: values.from.trim() || undefined,
    to: values.to.trim() || undefined,
  }
}

function parseTimestamp(value: string): number | null {
  const trimmed = value.trim()
  if (!trimmed) return null
  const ms = Date.parse(
    trimmed.includes("T") ? trimmed : trimmed.replace(" ", "T")
  )
  return Number.isNaN(ms) ? null : ms
}

export function windowError(from: string, to: string): string | null {
  const a = from.trim()
  const b = to.trim()
  if (!a || !b) return null
  const startMs = parseTimestamp(a)
  const endMs = parseTimestamp(b)
  if (startMs == null || endMs == null) return null
  if (startMs > endMs) return "Time window is invalid: from must be ≤ to."
  return null
}

export function validateAdmissionSearch(
  search: Record<string, unknown>
): AdmissionSearch {
  const str = (key: string): string | undefined => {
    const v = search[key]
    return typeof v === "string" && v.trim() ? v : undefined
  }
  return {
    types: str("types"),
    from: str("from"),
    to: str("to"),
  }
}

import type { TableCoverage } from "@/lib/api"

export const EMAR_TABLE = "emar"

export function formatCoverageLabel(table: string): string {
  if (table === EMAR_TABLE) return "eMAR"
  return table
}

export function coverageFor(
  coverage: TableCoverage[],
  table: string
): TableCoverage | undefined {
  return coverage.find((c) => c.table === table)
}

export function formatCoverageBadge(c: TableCoverage): string {
  const label = formatCoverageLabel(c.table)
  if (!c.has_rows) return `No ${label}`
  return `${label} · ${c.row_count.toLocaleString()}`
}

import type { Provenance } from "@/lib/api"

export function ProvenanceChip({ provenance }: { provenance: Provenance }) {
  return (
    <span className="inline-flex flex-wrap items-center gap-x-2 gap-y-0.5 font-mono text-[11px] text-muted-foreground">
      <span>
        {provenance.table}.{provenance.field}
      </span>
      <span>row={String(provenance.row_id ?? "—")}</span>
      {provenance.time ? <span>t={provenance.time}</span> : <span>untimed</span>}
    </span>
  )
}

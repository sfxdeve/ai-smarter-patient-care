import { CopyIcon } from "lucide-react"
import { toast } from "sonner"

import type { Provenance } from "@/lib/api"
import { Button } from "@/components/ui/button"
import {
  Popover,
  PopoverContent,
  PopoverHeader,
  PopoverTitle,
  PopoverTrigger,
} from "@/components/ui/popover"

async function copyText(label: string, value: string) {
  try {
    await navigator.clipboard.writeText(value)
    toast.success(`Copied ${label}`)
  } catch {
    toast.error(`Could not copy ${label}`)
  }
}

function ProvenanceField({
  label,
  display,
  value,
}: {
  label: string
  display: string
  value: string | null
}) {
  return (
    <div className="flex items-start justify-between gap-2">
      <div className="min-w-0 space-y-0.5">
        <p className="text-[10px] font-medium tracking-wide text-muted-foreground uppercase">
          {label}
        </p>
        <p className="break-all font-mono text-xs">{display}</p>
      </div>
      <Button
        type="button"
        variant="ghost"
        size="icon-xs"
        aria-label={`Copy ${label}`}
        disabled={value == null}
        onClick={() => {
          if (value == null) return
          void copyText(label, value)
        }}
      >
        <CopyIcon />
      </Button>
    </div>
  )
}

export function ProvenanceChip({ provenance }: { provenance: Provenance }) {
  const rowIdDisplay =
    provenance.row_id == null ? "—" : String(provenance.row_id)
  const rowIdValue =
    provenance.row_id == null ? null : String(provenance.row_id)
  const timeDisplay = provenance.time ?? "untimed"

  return (
    <Popover>
      <PopoverTrigger
        render={
          <Button
            type="button"
            variant="outline"
            size="xs"
            className="h-5 rounded-4xl px-2 font-normal text-muted-foreground"
          />
        }
      >
        Provenance
      </PopoverTrigger>
      <PopoverContent align="start" className="w-80">
        <PopoverHeader>
          <PopoverTitle>Provenance</PopoverTitle>
        </PopoverHeader>
        <div className="space-y-2.5">
          <ProvenanceField
            label="Table"
            display={provenance.table}
            value={provenance.table}
          />
          <ProvenanceField
            label="Field"
            display={provenance.field}
            value={provenance.field}
          />
          <ProvenanceField
            label="Row id"
            display={rowIdDisplay}
            value={rowIdValue}
          />
          <ProvenanceField
            label="Time"
            display={timeDisplay}
            value={provenance.time}
          />
        </div>
      </PopoverContent>
    </Popover>
  )
}

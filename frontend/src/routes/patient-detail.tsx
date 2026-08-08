import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"

import { QaPanel } from "@/components/qa-panel"
import { TimelineView } from "@/components/timeline-view"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { api } from "@/lib/api"

export function PatientDetailPage({ subjectId }: { subjectId: number }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["patient", subjectId],
    queryFn: () => api.patient(subjectId),
  })
  const [openHadm, setOpenHadm] = useState<number | null>(null)

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading patient…</p>
  if (error) return <p className="text-sm text-destructive">{(error as Error).message}</p>
  if (!data) return null

  const activeHadm = openHadm ?? data.admissions[0]?.hadm_id ?? null

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">
          ← All patients
        </Link>
        <h1 className="font-heading text-2xl font-semibold">Patient {data.subject_id}</h1>
        <p className="text-sm text-muted-foreground">
          {data.gender ?? "—"} · anchor age {data.anchor_age ?? "—"} ·{" "}
          {data.anchor_year_group ?? "—"}
        </p>
        <p className="max-w-2xl text-sm text-muted-foreground">{data.date_shift_note}</p>
        <div className="flex flex-wrap gap-2">
          {data.coverage.map((c) => (
            <Badge key={c.table} variant={c.has_rows ? "default" : "secondary"}>
              {c.table}: {c.has_rows ? c.row_count : "none"}
            </Badge>
          ))}
        </div>
      </div>

      <section className="space-y-3">
        <h2 className="font-heading text-xl font-semibold">Admissions</h2>
        <p className="text-sm text-muted-foreground">
          Each Admission is a chapter of the hospital journey.
        </p>
        <div className="space-y-2">
          {data.admissions.map((a, idx) => (
            <div
              key={a.hadm_id}
              className={`rounded-lg border p-4 ${
                activeHadm === a.hadm_id ? "border-foreground" : ""
              }`}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs tracking-wide text-muted-foreground uppercase">
                    Chapter {idx + 1}
                  </p>
                  <p className="font-medium">hadm_id {a.hadm_id}</p>
                  <p className="font-mono text-xs text-muted-foreground">
                    {a.admittime} → {a.dischtime}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {a.admission_type} · {a.admission_location} → {a.discharge_location ?? "—"} ·{" "}
                    {a.icu_stay_count} ICU stay(s)
                  </p>
                </div>
                <Button
                  size="sm"
                  variant={activeHadm === a.hadm_id ? "default" : "outline"}
                  onClick={() => setOpenHadm(a.hadm_id)}
                >
                  Open timeline
                </Button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {activeHadm != null ? (
        <>
          <Separator />
          <section className="space-y-4">
            <h2 className="font-heading text-xl font-semibold">
              Timeline · Admission {activeHadm}
            </h2>
            <TimelineView subjectId={subjectId} hadmId={activeHadm} />
          </section>
          <Separator />
          <QaPanel subjectId={subjectId} hadmId={activeHadm} />
        </>
      ) : null}
    </div>
  )
}

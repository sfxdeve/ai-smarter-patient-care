import { Link } from "@tanstack/react-router"
import { ArrowRight, Info } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import type { AdmissionChapter, PatientDetail, TableCoverage } from "@/lib/api"
import { formatCoverageBadge } from "@/lib/coverage"

function CoverageBadges({ coverage }: { coverage: TableCoverage[] }) {
  if (coverage.length === 0) {
    return <p className="text-sm text-muted-foreground">No coverage signals.</p>
  }

  return (
    <div className="flex flex-wrap gap-2">
      {coverage.map((c) => (
        <Badge
          key={c.table}
          variant={c.has_rows ? "secondary" : "outline"}
          title={c.note ?? undefined}
        >
          {formatCoverageBadge(c)}
        </Badge>
      ))}
    </div>
  )
}

function formatRange(start: string | null, end: string | null): string {
  const a = start ?? "—"
  const b = end ?? "—"
  return `${a} → ${b}`
}

function locationLine(admission: AdmissionChapter): string {
  const type = admission.admission_type ?? "—"
  const from = admission.admission_location ?? "—"
  const to = admission.discharge_location ?? "—"
  const icu =
    admission.icu_stay_count === 1
      ? "1 ICU Stay"
      : `${admission.icu_stay_count} ICU Stays`
  return `${type} · ${from} → ${to} · ${icu}`
}

function AdmissionChapterCard({
  subjectId,
  admission,
  chapter,
}: {
  subjectId: number
  admission: AdmissionChapter
  chapter: number
}) {
  return (
    <Card size="sm" className="relative transition-colors hover:bg-muted/30">
      <CardHeader className="border-b">
        <CardDescription className="text-xs tracking-wide uppercase">
          Chapter {chapter}
        </CardDescription>
        <CardTitle className="tabular-nums">
          Admission {admission.hadm_id}
        </CardTitle>
        <CardAction>
          <Button variant="outline" size="sm" render={<span />}>
            Open
            <ArrowRight className="size-3.5" />
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent className="space-y-1 pt-0">
        <p className="font-mono text-xs text-muted-foreground tabular-nums">
          {formatRange(admission.admittime, admission.dischtime)}
        </p>
        <p className="text-sm text-muted-foreground">
          {locationLine(admission)}
        </p>
        {admission.hospital_expire_flag === 1 ? (
          <Badge variant="outline">In-hospital death flag</Badge>
        ) : null}
      </CardContent>
      <Link
        to="/patients/$subjectId/admissions/$hadmId"
        params={{
          subjectId: String(subjectId),
          hadmId: String(admission.hadm_id),
        }}
        className="absolute inset-0 rounded-xl"
        aria-label={`Open Admission ${admission.hadm_id}, chapter ${chapter}`}
      />
    </Card>
  )
}

export function PatientOverview({ patient }: { patient: PatientDetail }) {
  const demographics = [
    patient.gender ?? "—",
    patient.anchor_age == null ? "anchor age —" : `anchor age ${patient.anchor_age}`,
    patient.anchor_year_group ?? "—",
    patient.anchor_year == null ? null : `anchor year ${patient.anchor_year}`,
    patient.dod ? `DOD ${patient.dod}` : null,
  ]
    .filter(Boolean)
    .join(" · ")

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="font-heading text-2xl font-semibold tabular-nums">
          Patient {patient.subject_id}
        </h1>
        <p className="text-sm text-muted-foreground">{demographics}</p>
      </div>

      <Alert>
        <Info />
        <AlertTitle>Date-shifted timestamps</AlertTitle>
        <AlertDescription>{patient.date_shift_note}</AlertDescription>
      </Alert>

      <section className="space-y-3">
        <div>
          <h2 className="font-heading text-lg font-semibold">Coverage</h2>
          <p className="text-sm text-muted-foreground">
            Table presence for this Patient before opening an Admission.
          </p>
        </div>
        <CoverageBadges coverage={patient.coverage} />
      </section>

      <section className="space-y-3">
        <div>
          <h2 className="font-heading text-lg font-semibold">Admissions</h2>
          <p className="text-sm text-muted-foreground">
            Each Admission is a chapter of the hospital journey.
          </p>
        </div>

        {patient.admissions.length === 0 ? (
          <Empty className="border py-12">
            <EmptyHeader>
              <EmptyTitle>No Admissions</EmptyTitle>
              <EmptyDescription>
                This Patient has no Admissions in the demo cohort.
              </EmptyDescription>
            </EmptyHeader>
            <EmptyContent>
              <Button variant="outline" size="sm" render={<Link to="/" />}>
                Back to Patients
              </Button>
            </EmptyContent>
          </Empty>
        ) : (
          <div className="space-y-2">
            {patient.admissions.map((admission, idx) => (
              <AdmissionChapterCard
                key={admission.hadm_id}
                subjectId={patient.subject_id}
                admission={admission}
                chapter={idx + 1}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

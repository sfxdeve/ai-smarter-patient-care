import { useQuery } from "@tanstack/react-query"
import { Link, useNavigate } from "@tanstack/react-router"
import { AlertCircle, Info } from "lucide-react"

import { AdmissionTimeline } from "@/components/admission-timeline"
import { BillingPanel } from "@/components/billing-panel"
import type { AdmissionSearch } from "@/lib/admission-search"
import { RouteBreadcrumbs } from "@/components/route-breadcrumbs"
import { WithQaRail } from "@/components/with-qa-rail"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"

function AdmissionSkeleton() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Loading Admission">
      <div className="space-y-2">
        <Skeleton className="h-8 w-56" />
        <Skeleton className="h-4 w-80 max-w-full" />
      </div>
      <Skeleton className="h-20 w-full" />
      <Skeleton className="h-40 w-full" />
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} className="h-16 w-full" />
      ))}
    </div>
  )
}

function isUnknownPatient(error: unknown): boolean {
  return (
    error instanceof Error && error.message.startsWith("Unknown Patient")
  )
}

function formatRange(start: string | null, end: string | null): string {
  return `${start ?? "—"} → ${end ?? "—"}`
}

export function AdmissionPage({
  subjectId,
  hadmId,
  search,
}: {
  subjectId: string
  hadmId: string
  search: AdmissionSearch
}) {
  const navigate = useNavigate()
  const subjectIdNum = Number(subjectId)
  const hadmIdNum = Number(hadmId)
  const validIds = Number.isFinite(subjectIdNum) && Number.isFinite(hadmIdNum)

  const patient = useQuery({
    queryKey: ["patient", subjectIdNum],
    queryFn: () => api.patient(subjectIdNum),
    enabled: validIds,
  })

  const chapter = patient.data?.admissions.find((a) => a.hadm_id === hadmIdNum)

  const notFoundIds = !validIds
  const unknownPatient =
    validIds && patient.isError && isUnknownPatient(patient.error)
  const unknownAdmission =
    validIds && patient.isSuccess && chapter == null

  const onSearchChange = (next: AdmissionSearch) => {
    void navigate({
      to: "/patients/$subjectId/admissions/$hadmId",
      params: { subjectId, hadmId },
      search: next,
      replace: true,
    })
  }

  return (
    <div className="space-y-6">
      <RouteBreadcrumbs
        items={[
          { kind: "link", label: "Patients", to: "/" },
          {
            kind: "link",
            label: `Patient ${subjectId}`,
            to: "/patients/$subjectId",
            params: { subjectId },
          },
          { kind: "page", label: `Admission ${hadmId}` },
        ]}
      />

      {notFoundIds || unknownPatient || unknownAdmission ? (
        <Empty className="border py-12">
          <EmptyHeader>
            <EmptyTitle>
              {unknownAdmission ? "Admission not found" : "Patient not found"}
            </EmptyTitle>
            <EmptyDescription>
              {notFoundIds
                ? "The URL does not contain valid Patient and Admission identifiers."
                : unknownPatient
                  ? "No Patient matches this identifier in the demo cohort."
                  : `Patient ${subjectId} has no Admission ${hadmId} in the demo cohort.`}
            </EmptyDescription>
          </EmptyHeader>
          <EmptyContent>
            {unknownAdmission && validIds ? (
              <Button
                variant="outline"
                size="sm"
                render={
                  <Link
                    to="/patients/$subjectId"
                    params={{ subjectId }}
                  />
                }
              >
                Back to Patient
              </Button>
            ) : (
              <Button variant="outline" size="sm" render={<Link to="/" />}>
                Back to Patients
              </Button>
            )}
          </EmptyContent>
        </Empty>
      ) : null}

      {validIds && patient.isPending ? <AdmissionSkeleton /> : null}

      {validIds && patient.isError && !isUnknownPatient(patient.error) ? (
        <Alert variant="destructive">
          <AlertCircle />
          <AlertTitle>Could not load Admission</AlertTitle>
          <AlertDescription>
            {patient.error instanceof Error
              ? patient.error.message
              : "Request failed."}
          </AlertDescription>
          <div className="col-start-2 mt-2 flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => void patient.refetch()}
            >
              Retry
            </Button>
            <Button variant="outline" size="sm" render={<Link to="/" />}>
              Back to Patients
            </Button>
          </div>
        </Alert>
      ) : null}

      {validIds && patient.isSuccess && chapter ? (
        <WithQaRail subjectId={subjectIdNum} hadmId={hadmIdNum}>
          <div className="space-y-6">
            <div className="space-y-2">
              <h1 className="font-heading text-2xl font-semibold tabular-nums">
                Admission {hadmId}
              </h1>
              <p className="text-sm text-muted-foreground">
                {[
                  chapter.admission_type ?? "—",
                  formatRange(chapter.admittime, chapter.dischtime),
                  chapter.icu_stay_count === 1
                    ? "1 ICU Stay"
                    : `${chapter.icu_stay_count} ICU Stays`,
                ].join(" · ")}
              </p>
            </div>

            <Alert>
              <Info />
              <AlertTitle>Date-shifted timestamps</AlertTitle>
              <AlertDescription>{patient.data.date_shift_note}</AlertDescription>
            </Alert>

            <div className="grid gap-8 xl:grid-cols-[1fr_20rem]">
              <AdmissionTimeline
                subjectId={subjectIdNum}
                hadmId={hadmIdNum}
                search={search}
                onSearchChange={onSearchChange}
              />
              <BillingPanel subjectId={subjectIdNum} hadmId={hadmIdNum} />
            </div>
          </div>
        </WithQaRail>
      ) : null}
    </div>
  )
}

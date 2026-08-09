import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"

import {
  LoadingBlock,
  EmptyState,
  ErrorAlert,
} from "@/components/async-state"
import { PatientOverview } from "@/components/patient-overview"
import { RouteBreadcrumbs } from "@/components/route-breadcrumbs"
import { WithQaRail } from "@/components/with-qa-rail"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"

function PatientOverviewSkeleton() {
  return (
    <LoadingBlock label="Loading Patient" className="space-y-8">
      <div className="space-y-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-80 max-w-full" />
      </div>
      <Skeleton className="h-20 w-full" />
      <div className="space-y-3">
        <Skeleton className="h-6 w-32" />
        <div className="flex flex-wrap gap-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-6 w-28" />
          ))}
        </div>
      </div>
      <div className="space-y-3">
        <Skeleton className="h-6 w-36" />
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-28 w-full" />
        ))}
      </div>
    </LoadingBlock>
  )
}

function isUnknownPatient(error: unknown): boolean {
  return (
    error instanceof Error && error.message.startsWith("Unknown Patient")
  )
}

export function PatientPage({ subjectId }: { subjectId: string }) {
  const subjectIdNum = Number(subjectId)
  const validId = Number.isFinite(subjectIdNum)

  const patient = useQuery({
    queryKey: ["patient", subjectIdNum],
    queryFn: () => api.patient(subjectIdNum),
    enabled: validId,
  })

  const notFound =
    !validId || (patient.isError && isUnknownPatient(patient.error))

  return (
    <div className="space-y-6">
      <RouteBreadcrumbs
        items={[
          { kind: "link", label: "Patients", to: "/" },
          { kind: "page", label: `Patient ${subjectId}` },
        ]}
      />

      {notFound ? (
        <EmptyState
          title="Patient not found"
          description={
            !validId
              ? `“${subjectId}” is not a valid Patient identifier.`
              : "No Patient matches this identifier in the demo cohort."
          }
          action={
            <Button variant="outline" size="sm" render={<Link to="/" />}>
              Back to Patients
            </Button>
          }
        />
      ) : null}

      {validId && patient.isPending ? <PatientOverviewSkeleton /> : null}

      {validId && patient.isError && !isUnknownPatient(patient.error) ? (
        <ErrorAlert
          title="Could not load Patient"
          message={patient.error}
          onRetry={() => void patient.refetch()}
          actions={
            <Button variant="outline" size="sm" render={<Link to="/" />}>
              Back to Patients
            </Button>
          }
        />
      ) : null}

      {validId && patient.isSuccess ? (
        <WithQaRail subjectId={subjectIdNum} hadmId={null}>
          <PatientOverview patient={patient.data} />
        </WithQaRail>
      ) : null}
    </div>
  )
}

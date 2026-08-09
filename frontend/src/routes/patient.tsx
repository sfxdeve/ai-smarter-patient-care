import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { AlertCircle } from "lucide-react"

import { PatientOverview } from "@/components/patient-overview"
import { RouteBreadcrumbs } from "@/components/route-breadcrumbs"
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

function PatientOverviewSkeleton() {
  return (
    <div className="space-y-8" aria-busy="true" aria-label="Loading Patient">
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
    </div>
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
        <Empty className="border py-12">
          <EmptyHeader>
            <EmptyTitle>Patient not found</EmptyTitle>
            <EmptyDescription>
              {!validId
                ? `“${subjectId}” is not a valid Patient identifier.`
                : "No Patient matches this identifier in the demo cohort."}
            </EmptyDescription>
          </EmptyHeader>
          <EmptyContent>
            <Button variant="outline" size="sm" render={<Link to="/" />}>
              Back to Patients
            </Button>
          </EmptyContent>
        </Empty>
      ) : null}

      {validId && patient.isPending ? <PatientOverviewSkeleton /> : null}

      {validId && patient.isError && !isUnknownPatient(patient.error) ? (
        <Alert variant="destructive">
          <AlertCircle />
          <AlertTitle>Could not load Patient</AlertTitle>
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

      {validId && patient.isSuccess ? (
        <PatientOverview patient={patient.data} />
      ) : null}
    </div>
  )
}

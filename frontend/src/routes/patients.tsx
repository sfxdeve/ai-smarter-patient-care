import { useQuery } from "@tanstack/react-query"
import { AlertCircle } from "lucide-react"

import { PatientsTable } from "@/components/patients-table"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"

function PatientsTableSkeleton() {
  return (
    <div className="space-y-3" aria-busy="true" aria-label="Loading Patients">
      <div className="flex items-center justify-between gap-3">
        <Skeleton className="h-8 w-full max-w-md" />
        <Skeleton className="h-4 w-24" />
      </div>
      <div className="space-y-2 rounded-lg border p-2">
        <Skeleton className="h-9 w-full" />
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    </div>
  )
}

export function PatientsPage() {
  const patients = useQuery({
    queryKey: ["patients"],
    queryFn: api.patients,
  })

  return (
    <div className="space-y-4">
      <div>
        <h1 className="font-heading text-2xl font-semibold">Patients</h1>
        <p className="text-sm text-muted-foreground">
          Browse the demo cohort, check coverage signals (including eMAR), then
          open a Patient.
        </p>
      </div>

      {patients.isPending ? <PatientsTableSkeleton /> : null}

      {patients.isError ? (
        <Alert variant="destructive">
          <AlertCircle />
          <AlertTitle>Could not load Patients</AlertTitle>
          <AlertDescription>
            {patients.error instanceof Error
              ? patients.error.message
              : "Request failed."}
          </AlertDescription>
          <div className="col-start-2 mt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => void patients.refetch()}
            >
              Retry
            </Button>
          </div>
        </Alert>
      ) : null}

      {patients.isSuccess && patients.data.length === 0 ? (
        <Empty className="border py-12">
          <EmptyHeader>
            <EmptyTitle>No Patients available</EmptyTitle>
            <EmptyDescription>
              The API returned an empty cohort. Confirm demo data is loaded and
              try again.
            </EmptyDescription>
          </EmptyHeader>
          <Button
            variant="outline"
            size="sm"
            onClick={() => void patients.refetch()}
          >
            Retry
          </Button>
        </Empty>
      ) : null}

      {patients.isSuccess && patients.data.length > 0 ? (
        <PatientsTable patients={patients.data} />
      ) : null}
    </div>
  )
}

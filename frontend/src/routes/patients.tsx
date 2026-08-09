import { useQuery } from "@tanstack/react-query"

import {
  LoadingBlock,
  EmptyState,
  ErrorAlert,
} from "@/components/async-state"
import { PatientsTable } from "@/components/patients-table"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"

function PatientsTableSkeleton() {
  return (
    <LoadingBlock label="Loading Patients">
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
    </LoadingBlock>
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
        <ErrorAlert
          title="Could not load Patients"
          message={patients.error}
          onRetry={() => void patients.refetch()}
        />
      ) : null}

      {patients.isSuccess && patients.data.length === 0 ? (
        <EmptyState
          title="No Patients available"
          description="The API returned an empty cohort. Confirm demo data is loaded and try again."
          action={
            <Button
              variant="outline"
              size="sm"
              onClick={() => void patients.refetch()}
            >
              Retry
            </Button>
          }
        />
      ) : null}

      {patients.isSuccess && patients.data.length > 0 ? (
        <PatientsTable patients={patients.data} />
      ) : null}
    </div>
  )
}

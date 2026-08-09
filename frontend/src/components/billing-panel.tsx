import { useQuery } from "@tanstack/react-query"

import {
  LoadingBlock,
  EmptyState,
  ErrorAlert,
} from "@/components/async-state"
import { ProvenanceChip } from "@/components/provenance"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import { api, type BillingCode } from "@/lib/api"

function CodeRow({ code }: { code: BillingCode }) {
  return (
    <li className="space-y-1">
      <div className="font-mono text-xs tabular-nums">
        {code.code_type && code.code_type !== "icd_diagnosis"
          ? `${code.code_type}: ${code.code}`
          : code.code}
        {code.seq_num != null ? (
          <span className="ml-2 text-muted-foreground">seq {code.seq_num}</span>
        ) : null}
      </div>
      {code.title ? <div className="text-sm">{code.title}</div> : null}
      <ProvenanceChip provenance={code.provenance} />
    </li>
  )
}

function CodeSection({
  title,
  codes,
  emptyLabel,
}: {
  title: string
  codes: BillingCode[]
  emptyLabel: string
}) {
  return (
    <div className="space-y-2">
      <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
        {title}
      </p>
      {codes.length === 0 ? (
        <p className="text-xs text-muted-foreground">{emptyLabel}</p>
      ) : (
        <ul className="space-y-3">
          {codes.map((code) => (
            <CodeRow
              key={`${code.code_type}-${code.code}-${code.seq_num ?? ""}`}
              code={code}
            />
          ))}
        </ul>
      )}
    </div>
  )
}

export function BillingPanel({
  subjectId,
  hadmId,
}: {
  subjectId: number
  hadmId: number
}) {
  const billing = useQuery({
    queryKey: ["billing", subjectId, hadmId],
    queryFn: () => api.billing(subjectId, hadmId),
  })

  return (
    <aside aria-label="Billing Context">
      <Card
        size="sm"
        className="sticky top-4 max-h-[calc(100svh-7rem)] overflow-y-auto"
      >
        <CardHeader className="border-b">
          <CardTitle className="text-xs tracking-wide uppercase">
            Billing Context
          </CardTitle>
          <CardDescription className="text-xs">
            Untimed discharge coding — never Timeline Events on the spine.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {billing.isPending ? (
            <LoadingBlock label="Loading Billing Context">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </LoadingBlock>
          ) : null}

          {billing.isError ? (
            <ErrorAlert
              title="Could not load Billing Context"
              message={billing.error}
              onRetry={() => void billing.refetch()}
            />
          ) : null}

          {billing.isSuccess ? (
            billing.data.diagnoses.length === 0 &&
            billing.data.drg_codes.length === 0 ? (
              <EmptyState
                className="py-8"
                title="No Billing Context"
                description="This Admission has no billed ICD diagnoses or DRG codes in the demo cohort. Absence here is not a timeline gap."
              />
            ) : (
              <div className="space-y-4">
                <p className="text-xs text-muted-foreground">
                  {billing.data.notice}
                </p>
                <Separator />
                <CodeSection
                  title="Diagnoses"
                  codes={billing.data.diagnoses}
                  emptyLabel="No billed ICD diagnoses for this Admission."
                />
                <Separator />
                <CodeSection
                  title="DRG"
                  codes={billing.data.drg_codes}
                  emptyLabel="No DRG codes for this Admission."
                />
              </div>
            )
          ) : null}
        </CardContent>
      </Card>
    </aside>
  )
}

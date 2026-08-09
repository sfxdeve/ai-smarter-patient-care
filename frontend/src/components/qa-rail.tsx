import { useState } from "react"
import { useForm } from "@tanstack/react-form"
import { useMutation, useQuery } from "@tanstack/react-query"
import { ChevronDown, CircleHelp, MessageSquareText } from "lucide-react"

import { LoadingBlock, ErrorAlert } from "@/components/async-state"
import { ProvenanceChip } from "@/components/provenance"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import { api, type QaResponse } from "@/lib/api"
import { cn } from "@/lib/utils"

const HISTORY_LIMIT = 8

function kindLabel(kind: QaResponse["kind"]): string {
  if (kind === "grounded") return "Grounded"
  if (kind === "no_data") return "No data"
  return "Abstention"
}

function kindCardClass(kind: QaResponse["kind"]): string {
  if (kind === "grounded") {
    return "border-emerald-600/40 bg-emerald-50/80 dark:border-emerald-500/30 dark:bg-emerald-950/40"
  }
  if (kind === "no_data") {
    return "border-sky-600/40 bg-sky-50/80 dark:border-sky-500/30 dark:bg-sky-950/40"
  }
  return "border-amber-600/45 bg-amber-50/90 dark:border-amber-500/35 dark:bg-amber-950/40"
}

function interpreterLabel(interpreter: QaResponse["interpreter"]): string {
  if (interpreter === "keyword_rescue") return "keyword rescue"
  if (interpreter === "keyword") return "keyword"
  if (interpreter === "fake") return "fake"
  return "llm"
}

function AnswerCard({
  answer,
  defaultExpanded = true,
}: {
  answer: QaResponse
  defaultExpanded?: boolean
}) {
  const [expanded, setExpanded] = useState(defaultExpanded)
  const isAbstention = answer.kind === "abstention"
  const isNoData = answer.kind === "no_data"

  return (
    <Card size="sm" className={cn("ring-0 border", kindCardClass(answer.kind))}>
      <CardHeader className="border-b border-inherit/40 [.border-b]:pb-3">
        <div className="flex flex-wrap items-center gap-1.5">
          <Badge
            variant={isAbstention ? "secondary" : isNoData ? "outline" : "default"}
          >
            {kindLabel(answer.kind)}
          </Badge>
          <Badge variant="outline">
            interpreter: {interpreterLabel(answer.interpreter)}
          </Badge>
          {answer.interpreter === "keyword_rescue" ? (
            <Badge variant="secondary">LLM unreachable — keyword baseline</Badge>
          ) : null}
          {answer.template_id ? (
            <Badge variant="outline">template: {answer.template_id}</Badge>
          ) : null}
        </div>
        <CardTitle className="text-sm font-normal leading-snug text-foreground">
          {answer.question}
        </CardTitle>
        <CardDescription className="sr-only">
          {kindLabel(answer.kind)} answer
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div
          className={cn(
            "rounded-md border border-dashed border-foreground/15 bg-background/60 px-2.5 py-2",
            "text-sm italic text-foreground/85"
          )}
          title="Template summary — presentation chrome, not a source row"
        >
          <p className="mb-1 text-[10px] font-medium tracking-wide text-muted-foreground not-italic uppercase">
            Summary (template phrasing)
          </p>
          {answer.summary}
        </div>

        {answer.abstention_reason ? (
          <Alert>
            <CircleHelp />
            <AlertTitle>Why this abstained</AlertTitle>
            <AlertDescription>{answer.abstention_reason}</AlertDescription>
          </Alert>
        ) : null}

        {isNoData ? (
          <p className="text-sm text-muted-foreground">
            The matched template ran and returned no rows. This is not a grounded
            clinical negative — it is a no-data result.
          </p>
        ) : null}

        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="h-7 px-2 text-xs"
          onClick={() => setExpanded((v) => !v)}
          aria-expanded={expanded}
        >
          {expanded ? "Hide details" : "Show details"}
          <ChevronDown
            className={cn(
              "size-3.5 opacity-60 transition-transform",
              expanded && "rotate-180"
            )}
          />
        </Button>

        {expanded ? (
          <>
            <InspectBlock answer={answer} />
            {answer.coverage?.length ? (
              <div className="space-y-1">
                <p className="text-[10px] font-medium tracking-wide text-muted-foreground uppercase">
                  Table coverage
                </p>
                <ul className="space-y-0.5 text-xs text-muted-foreground">
                  {answer.coverage.map((c) => (
                    <li key={c.table}>
                      <span className="font-mono text-foreground/80">{c.table}</span>
                      : {c.has_rows ? "has rows" : "no rows"} (n={c.row_count})
                      {c.note ? ` — ${c.note}` : ""}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {answer.rows?.length ? (
              <div className="space-y-1.5">
                <p className="text-[10px] font-medium tracking-wide text-muted-foreground uppercase">
                  Source rows
                </p>
                <pre className="max-h-48 overflow-auto rounded-md border bg-background p-2 font-mono text-[11px] leading-relaxed not-italic">
                  {JSON.stringify(answer.rows.slice(0, 50), null, 2)}
                </pre>
              </div>
            ) : null}
            {answer.provenance?.length ? (
              <div className="space-y-1">
                <p className="text-[10px] font-medium tracking-wide text-muted-foreground uppercase">
                  Provenance
                </p>
                <ul className="space-y-1">
                  {answer.provenance.slice(0, 40).map((p, i) => (
                    <li key={`${p.table}-${p.field}-${i}`}>
                      <ProvenanceChip provenance={p} />
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </>
        ) : null}
      </CardContent>
    </Card>
  )
}

function InspectBlock({ answer }: { answer: QaResponse }) {
  const hasSlots = answer.slots && Object.keys(answer.slots).length > 0
  const hasSql = Boolean(answer.sql)
  const hasTemplate = Boolean(answer.template_id)
  if (!hasSlots && !hasSql && !hasTemplate) return null

  return (
    <Collapsible defaultOpen={false}>
      <CollapsibleTrigger
        render={
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-full justify-between px-2 text-xs"
          />
        }
      >
        <span>Inspect template · slots · SQL</span>
        <ChevronDown className="size-3.5 opacity-60 transition-transform [[data-panel-open]_&]:rotate-180" />
      </CollapsibleTrigger>
      <CollapsibleContent className="space-y-2 pt-2">
        {hasTemplate ? (
          <p className="font-mono text-xs">
            template_id: {answer.template_id}
          </p>
        ) : null}
        {hasSlots ? (
          <pre className="overflow-x-auto rounded-md border bg-background p-2 font-mono text-[11px]">
            slots: {JSON.stringify(answer.slots, null, 2)}
          </pre>
        ) : null}
        {hasSql ? (
          <pre className="overflow-x-auto rounded-md border bg-background p-2 font-mono text-[11px]">
            {answer.sql}
          </pre>
        ) : null}
      </CollapsibleContent>
    </Collapsible>
  )
}

export function QaRail({
  subjectId,
  hadmId,
  className,
}: {
  subjectId: number
  hadmId?: number | null
  className?: string
}) {
  const [history, setHistory] = useState<QaResponse[]>([])
  const scopeLabel =
    hadmId != null ? `Admission ${hadmId}` : "Patient (no Admission)"

  const examples = useQuery({
    queryKey: ["qa-examples"],
    queryFn: api.qaExamples,
    staleTime: 60_000,
  })

  const mutation = useMutation({
    mutationFn: (question: string) =>
      api.qa({
        question,
        subject_id: subjectId,
        hadm_id: hadmId ?? null,
      }),
    onSuccess: (data) => {
      setHistory((prev) => [data, ...prev].slice(0, HISTORY_LIMIT))
    },
  })

  const form = useForm({
    defaultValues: { question: "" },
    onSubmit: async ({ value }) => {
      const question = value.question.trim()
      if (!question) return
      await mutation.mutateAsync(question)
    },
  })

  const latest = history[0]
  const earlier = history.slice(1)

  return (
    <div
      className={cn(
        "flex flex-col gap-4 rounded-xl border bg-card p-4 text-card-foreground shadow-xs",
        className
      )}
    >
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <MessageSquareText className="size-4 text-muted-foreground" />
          <h2 className="font-heading text-base font-semibold">Ask the record</h2>
        </div>
        <p className="text-xs text-muted-foreground">
          Scope: {scopeLabel}. Interpreter sees schema + Query Templates + your
          question only. Summaries are fixed template phrasing — distinct from
          source rows.
        </p>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          e.stopPropagation()
          void form.handleSubmit()
        }}
        className="space-y-3"
      >
        <FieldGroup>
          <form.Field
            name="question"
            validators={{
              onSubmit: ({ value }) =>
                !value.trim() ? "Enter a question before asking." : undefined,
            }}
          >
            {(field) => {
              const invalid = field.state.meta.errors.length > 0
              return (
                <Field data-invalid={invalid || undefined}>
                  <FieldLabel htmlFor={field.name}>Question</FieldLabel>
                  <Textarea
                    id={field.name}
                    name={field.name}
                    value={field.state.value}
                    onBlur={field.handleBlur}
                    onChange={(e) => field.handleChange(e.target.value)}
                    aria-invalid={invalid || undefined}
                    placeholder={
                      hadmId != null
                        ? "e.g. How many transfers occurred during this admission?"
                        : "e.g. How many admissions does this patient have?"
                    }
                    rows={3}
                    className="min-h-20 resize-y"
                  />
                  <FieldDescription>
                    Answers are assembled from local SQL over this scope only.
                  </FieldDescription>
                  {invalid ? (
                    <FieldError
                      errors={field.state.meta.errors.map((message) =>
                        typeof message === "string" ? { message } : message
                      )}
                    />
                  ) : null}
                </Field>
              )
            }}
          </form.Field>
        </FieldGroup>

        <div className="flex flex-wrap items-center gap-2">
          <form.Subscribe selector={(s) => [s.canSubmit, s.isSubmitting] as const}>
            {([canSubmit, isSubmitting]) => (
              <Button
                type="submit"
                disabled={!canSubmit || mutation.isPending || isSubmitting}
              >
                {mutation.isPending || isSubmitting ? "Running…" : "Ask"}
              </Button>
            )}
          </form.Subscribe>
        </div>
      </form>

      <div className="space-y-2">
        <p className="text-[10px] font-medium tracking-wide text-muted-foreground uppercase">
          Example questions
        </p>
        {examples.isPending ? (
          <LoadingBlock label="Loading examples">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </LoadingBlock>
        ) : null}
        {examples.isError ? (
          <ErrorAlert
            title="Could not load examples"
            message={examples.error}
            onRetry={() => void examples.refetch()}
          />
        ) : null}
        {examples.isSuccess && examples.data.length === 0 ? (
          <p className="text-xs text-muted-foreground">
            No catalog examples available for this build.
          </p>
        ) : null}
        {examples.data?.length ? (
          <ul className="space-y-1.5">
            {examples.data.map((ex) => (
              <li key={ex.template_id}>
                <button
                  type="button"
                  className="w-full rounded-lg border bg-background px-2.5 py-2 text-left transition-colors hover:bg-muted/60"
                  title={ex.description || undefined}
                  onClick={() => {
                    form.setFieldValue("question", ex.question)
                    form.setFieldMeta("question", (prev) => ({
                      ...prev,
                      errorMap: {},
                      errorSourceMap: {},
                    }))
                  }}
                >
                  <span className="block font-mono text-[10px] text-muted-foreground">
                    {ex.template_id}
                  </span>
                  <span className="block text-xs leading-snug text-foreground">
                    {ex.question}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </div>

      {mutation.isError ? (
        <ErrorAlert
          title="Question failed"
          message={mutation.error}
          onRetry={() => {
            const q = form.state.values.question.trim()
            if (q) mutation.mutate(q)
          }}
        />
      ) : null}

      {latest ? (
        <div className="space-y-2">
          <p className="text-[10px] font-medium tracking-wide text-muted-foreground uppercase">
            Latest answer
          </p>
          <AnswerCard answer={latest} />
        </div>
      ) : !mutation.isPending && !mutation.isError ? (
        <p className="text-xs text-muted-foreground">
          Ask a question or pick an example to see a Grounded, No-data, or
          Abstention result here.
        </p>
      ) : null}

      {earlier.length > 0 ? (
        <>
          <Separator />
          <div className="space-y-2">
            <p className="text-[10px] font-medium tracking-wide text-muted-foreground uppercase">
              Session history
            </p>
            <ScrollArea className="max-h-64">
              <div className="space-y-2 pr-2">
                {earlier.map((answer, i) => (
                  <AnswerCard
                    key={`${answer.question}-${i}-${answer.template_id ?? "none"}`}
                    answer={answer}
                    defaultExpanded={false}
                  />
                ))}
              </div>
            </ScrollArea>
          </div>
        </>
      ) : null}
    </div>
  )
}

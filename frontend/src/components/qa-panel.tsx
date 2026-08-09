import { useState } from "react"
import { useMutation, useQuery } from "@tanstack/react-query"

import { ProvenanceChip } from "@/components/provenance"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { api, type QaResponse } from "@/lib/api"

function kindStyles(kind: QaResponse["kind"]) {
  if (kind === "grounded") return "border-emerald-700/30 bg-emerald-50"
  if (kind === "no_data") return "border-sky-700/30 bg-sky-50"
  return "border-amber-700/30 bg-amber-50"
}

export function QaPanel({
  subjectId,
  hadmId,
}: {
  subjectId: number
  hadmId?: number | null
}) {
  const [question, setQuestion] = useState("")
  const examples = useQuery({ queryKey: ["qa-examples"], queryFn: api.qaExamples })
  const mutation = useMutation({
    mutationFn: () =>
      api.qa({
        question,
        subject_id: subjectId,
        hadm_id: hadmId ?? null,
      }),
  })

  const answer = mutation.data

  return (
    <div className="space-y-4 rounded-lg border p-4">
      <div>
        <h3 className="font-heading text-lg font-semibold">Ask the record</h3>
        <p className="text-sm text-muted-foreground">
          The interpreter sees only schema + Query Templates + your question. Answers are assembled
          from local SQL. AI-phrased text is marked separately from source values.
        </p>
      </div>

      <Textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="e.g. How many transfers occurred during this admission?"
        rows={3}
      />
      <div className="flex flex-wrap gap-2">
        <Button
          disabled={!question.trim() || mutation.isPending}
          onClick={() => mutation.mutate()}
        >
          {mutation.isPending ? "Running…" : "Ask"}
        </Button>
        {examples.data?.slice(0, 6).map((ex) => (
          <Button
            key={ex.template_id}
            variant="outline"
            size="sm"
            onClick={() => setQuestion(ex.question)}
          >
            {ex.template_id}
          </Button>
        ))}
      </div>

      {mutation.error ? (
        <p className="text-sm text-destructive">{(mutation.error as Error).message}</p>
      ) : null}

      {answer ? (
        <div className={`space-y-3 rounded-lg border p-4 ${kindStyles(answer.kind)}`}>
          <div className="flex flex-wrap items-center gap-2">
            <Badge>{answer.kind}</Badge>
            <Badge variant="outline">interpreter: {answer.interpreter}</Badge>
            {answer.interpreter === "keyword_rescue" ? (
              <Badge variant="secondary">LLM unreachable — keyword baseline</Badge>
            ) : null}
            {answer.template_id ? (
              <Badge variant="outline">template: {answer.template_id}</Badge>
            ) : null}
          </div>
          <p className="text-sm italic text-foreground/80" title="AI-phrased summary">
            {answer.summary}
          </p>
          {answer.slots && Object.keys(answer.slots).length > 0 ? (
            <pre className="overflow-x-auto rounded bg-background/70 p-2 font-mono text-xs">
              slots: {JSON.stringify(answer.slots, null, 2)}
            </pre>
          ) : null}
          {answer.sql ? (
            <pre className="overflow-x-auto rounded bg-background/70 p-2 font-mono text-xs">
              {answer.sql}
            </pre>
          ) : null}
          {answer.coverage?.length ? (
            <div className="text-sm">
              <p className="text-xs font-medium uppercase">Table coverage</p>
              {answer.coverage.map((c) => (
                <div key={c.table}>
                  {c.table}: {c.has_rows ? "has rows" : "no rows"} (n={c.row_count})
                  {c.note ? ` — ${c.note}` : ""}
                </div>
              ))}
            </div>
          ) : null}
          {answer.rows?.length ? (
            <div className="space-y-2">
              <p className="text-xs font-medium uppercase">Source rows</p>
              <pre className="max-h-64 overflow-auto rounded bg-background/70 p-2 font-mono text-xs">
                {JSON.stringify(answer.rows.slice(0, 50), null, 2)}
              </pre>
            </div>
          ) : null}
          {answer.provenance?.length ? (
            <div className="space-y-1">
              <p className="text-xs font-medium uppercase">Provenance</p>
              {answer.provenance.slice(0, 40).map((p, i) => (
                <div key={i}>
                  <ProvenanceChip provenance={p} />
                </div>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}

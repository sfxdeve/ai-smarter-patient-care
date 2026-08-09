import { useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"

import { ProvenanceChip } from "@/components/provenance"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import {
  api,
  type IcuStayInterval,
  type TimelineEvent,
} from "@/lib/api"

const ALL_TYPES = [
  "admit_discharge",
  "transfer",
  "lab",
  "medication",
  "microbiology",
  "procedure",
  "icu_observation",
]

function eventSortKey(time: string | null | undefined): string {
  return time ?? ""
}

function EventRow({
  event,
  showUnmatchedStayBadge = false,
}: {
  event: TimelineEvent
  showUnmatchedStayBadge?: boolean
}) {
  const [open, setOpen] = useState(false)
  const stayBadge =
    showUnmatchedStayBadge && event.stay_id != null ? (
      <Badge variant="secondary">ICU Stay {event.stay_id}</Badge>
    ) : null

  if (event.band_key && event.band_events) {
    return (
      <Collapsible open={open} onOpenChange={setOpen}>
        <div className="grid gap-1 border-b py-3 md:grid-cols-[10rem_7rem_1fr]">
          <div className="font-mono text-xs text-muted-foreground">{event.time ?? "—"}</div>
          <div className="flex flex-wrap gap-1">
            <Badge variant="outline">{event.event_type}</Badge>
            {stayBadge}
          </div>
          <div className="space-y-1">
            <CollapsibleTrigger className="text-left text-sm font-medium underline-offset-4 hover:underline">
              {event.label} · {event.band_count} observations
            </CollapsibleTrigger>
            <ProvenanceChip provenance={event.provenance} />
            <CollapsibleContent className="mt-2 space-y-2 border-l pl-3">
              {event.band_events.map((child, i) => (
                <div key={`${child.time}-${i}`} className="text-sm">
                  <div className="font-mono text-xs text-muted-foreground">{child.time}</div>
                  <div>
                    {child.label}
                    {child.detail ? `: ${child.detail}` : ""}
                  </div>
                  <ProvenanceChip provenance={child.provenance} />
                </div>
              ))}
            </CollapsibleContent>
          </div>
        </div>
      </Collapsible>
    )
  }

  return (
    <div className="grid gap-1 border-b py-3 md:grid-cols-[10rem_7rem_1fr]">
      <div className="font-mono text-xs text-muted-foreground">{event.time ?? "—"}</div>
      <div className="flex flex-wrap gap-1">
        <Badge variant="outline">{event.event_type}</Badge>
        {stayBadge}
      </div>
      <div className="space-y-1">
        <div className="text-sm font-medium">
          {event.label}
          {event.detail ? (
            <span className="font-normal text-muted-foreground"> — {event.detail}</span>
          ) : null}
        </div>
        <ProvenanceChip provenance={event.provenance} />
      </div>
    </div>
  )
}

function IcuStayIntervalBlock({
  stay,
  events,
}: {
  stay: IcuStayInterval
  events: TimelineEvent[]
}) {
  const [open, setOpen] = useState(true)
  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <div className="my-2 rounded-lg border bg-muted/40">
        <div className="grid gap-1 border-b px-3 py-3 md:grid-cols-[10rem_7rem_1fr]">
          <div className="font-mono text-xs text-muted-foreground">
            {stay.intime ?? "—"}
            {stay.outtime ? (
              <>
                <br />→ {stay.outtime}
              </>
            ) : null}
          </div>
          <div>
            <Badge>ICU Stay</Badge>
          </div>
          <div className="space-y-1">
            <CollapsibleTrigger className="text-left text-sm font-medium underline-offset-4 hover:underline">
              ICU Stay {stay.stay_id}: {stay.first_careunit ?? "—"} →{" "}
              {stay.last_careunit ?? "—"} · LOS {stay.los?.toFixed(2) ?? "—"}d
              {events.length ? ` · ${events.length} events` : ""}
            </CollapsibleTrigger>
            <ProvenanceChip provenance={stay.provenance} />
          </div>
        </div>
        <CollapsibleContent>
          <div className="border-l-2 border-foreground/20 pl-3 ml-2">
            {events.length === 0 ? (
              <p className="py-3 text-xs text-muted-foreground">
                No Timeline Events associated with this ICU Stay in the current
                filter.
              </p>
            ) : (
              events.map((ev, i) => (
                <EventRow
                  key={`${ev.event_type}-${ev.time}-${i}`}
                  event={ev}
                />
              ))
            )}
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  )
}

type TimelineItem =
  | {
      kind: "event"
      time: string
      event: TimelineEvent
      unmatchedStayId: boolean
    }
  | { kind: "stay"; time: string; stay: IcuStayInterval; events: TimelineEvent[] }

function buildTimelineItems(
  events: TimelineEvent[],
  stays: IcuStayInterval[]
): TimelineItem[] {
  const stayIds = new Set(stays.map((s) => s.stay_id))
  const byStay = new Map<number, TimelineEvent[]>()
  for (const s of stays) byStay.set(s.stay_id, [])

  const root: TimelineEvent[] = []
  for (const ev of events) {
    if (ev.stay_id != null && stayIds.has(ev.stay_id)) {
      byStay.get(ev.stay_id)!.push(ev)
    } else {
      root.push(ev)
    }
  }

  for (const list of byStay.values()) {
    list.sort((a, b) => eventSortKey(a.time).localeCompare(eventSortKey(b.time)))
  }

  const items: TimelineItem[] = [
    ...root.map((event) => ({
      kind: "event" as const,
      time: eventSortKey(event.time),
      event,
      unmatchedStayId: event.stay_id != null,
    })),
    ...stays.map((stay) => ({
      kind: "stay" as const,
      time: eventSortKey(stay.intime),
      stay,
      events: byStay.get(stay.stay_id) ?? [],
    })),
  ]

  items.sort((a, b) => {
    const cmp = a.time.localeCompare(b.time)
    if (cmp !== 0) return cmp
    if (a.kind !== b.kind) return a.kind === "stay" ? -1 : 1
    return 0
  })

  return items
}

export function TimelineView({
  subjectId,
  hadmId,
}: {
  subjectId: number
  hadmId: number
}) {
  const [selected, setSelected] = useState<string[]>(ALL_TYPES)
  const [start, setStart] = useState("")
  const [end, setEnd] = useState("")
  const [applied, setApplied] = useState({ types: ALL_TYPES, start: "", end: "" })

  const query = useQuery({
    queryKey: ["timeline", subjectId, hadmId, applied],
    queryFn: () =>
      api.timeline(subjectId, hadmId, {
        event_types: applied.types.join(","),
        start: applied.start || undefined,
        end: applied.end || undefined,
      }),
  })

  const billing = useQuery({
    queryKey: ["billing", subjectId, hadmId],
    queryFn: () => api.billing(subjectId, hadmId),
  })

  const toggle = (t: string) => {
    setSelected((prev) =>
      prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]
    )
  }

  const items = useMemo(() => {
    if (!query.data) return []
    return buildTimelineItems(query.data.events, query.data.icu_stays)
  }, [query.data])

  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_20rem]">
      <div className="space-y-4">
        <div className="flex flex-wrap items-end gap-3">
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Start</label>
            <Input
              value={start}
              onChange={(e) => setStart(e.target.value)}
              placeholder="YYYY-MM-DD HH:MM:SS"
              className="w-52 font-mono text-xs"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">End</label>
            <Input
              value={end}
              onChange={(e) => setEnd(e.target.value)}
              placeholder="YYYY-MM-DD HH:MM:SS"
              className="w-52 font-mono text-xs"
            />
          </div>
          <Button
            size="sm"
            onClick={() => setApplied({ types: selected, start, end })}
          >
            Apply filters
          </Button>
        </div>
        <div className="flex flex-wrap gap-2">
          {ALL_TYPES.map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => toggle(t)}
              className={`rounded-md border px-2 py-1 text-xs ${
                selected.includes(t)
                  ? "border-foreground bg-foreground text-background"
                  : "border-border text-muted-foreground"
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        {query.isLoading ? (
          <p className="text-sm text-muted-foreground">Loading timeline…</p>
        ) : query.error ? (
          <p className="text-sm text-destructive">{(query.error as Error).message}</p>
        ) : (
          <div>
            <p className="mb-2 text-sm text-muted-foreground">
              {query.data?.events.length ?? 0} Timeline Events
              {query.data?.icu_stays.length
                ? ` · ${query.data.icu_stays.length} ICU Stay interval${query.data.icu_stays.length === 1 ? "" : "s"}`
                : ""}
            </p>
            {items.map((item, i) =>
              item.kind === "stay" ? (
                <IcuStayIntervalBlock
                  key={`stay-${item.stay.stay_id}`}
                  stay={item.stay}
                  events={item.events}
                />
              ) : (
                <EventRow
                  key={`${item.event.event_type}-${item.event.time}-${i}`}
                  event={item.event}
                  showUnmatchedStayBadge={item.unmatchedStayId}
                />
              )
            )}
          </div>
        )}
      </div>

      <aside className="space-y-3">
        <div>
          <h3 className="font-heading text-sm font-semibold tracking-wide uppercase">
            Billing Context
          </h3>
          <p className="mt-1 text-xs text-muted-foreground">
            Untimed discharge coding — never shown on the timeline.
          </p>
        </div>
        <Separator />
        {billing.isLoading ? (
          <p className="text-xs text-muted-foreground">Loading…</p>
        ) : billing.data ? (
          <div className="space-y-4 text-sm">
            <p className="text-xs text-muted-foreground">{billing.data.notice}</p>
            <div>
              <p className="mb-1 text-xs font-medium uppercase">Diagnoses</p>
              <ul className="space-y-2">
                {billing.data.diagnoses.map((d) => (
                  <li key={`${d.code}-${d.seq_num}`}>
                    <div className="font-mono text-xs">{d.code}</div>
                    <div>{d.title}</div>
                    <ProvenanceChip provenance={d.provenance} />
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="mb-1 text-xs font-medium uppercase">DRG</p>
              <ul className="space-y-2">
                {billing.data.drg_codes.map((d) => (
                  <li key={`${d.code}-${d.code_type}`}>
                    <div className="font-mono text-xs">
                      {d.code_type}: {d.code}
                    </div>
                    <div>{d.title}</div>
                    <ProvenanceChip provenance={d.provenance} />
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ) : null}
      </aside>
    </div>
  )
}

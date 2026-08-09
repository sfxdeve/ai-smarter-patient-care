import { useMemo, useRef, useState } from "react"
import { useForm } from "@tanstack/react-form"
import { useQuery } from "@tanstack/react-query"
import { useVirtualizer } from "@tanstack/react-virtual"
import { ChevronDown } from "lucide-react"

import {
  LoadingBlock,
  EmptyState,
  ErrorAlert,
} from "@/components/async-state"
import { ProvenanceChip } from "@/components/provenance"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
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
import { Input } from "@/components/ui/input"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import {
  ALL_EVENT_TYPES,
  formToSearch,
  parseTypes,
  searchToForm,
  windowError,
  type AdmissionSearch,
} from "@/lib/admission-search"
import {
  api,
  type IcuStayInterval,
  type TimelineEvent,
} from "@/lib/api"
import { cn } from "@/lib/utils"

function eventSortKey(time: string | null | undefined): string {
  return time ?? ""
}

function VirtualBandRows({ events }: { events: TimelineEvent[] }) {
  const parentRef = useRef<HTMLDivElement>(null)
  const virtualizer = useVirtualizer({
    count: events.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 64,
    overscan: 10,
  })

  return (
    <div
      ref={parentRef}
      className="mt-2 max-h-80 overflow-auto border-l pl-3"
      role="list"
      aria-label="ICU observation source rows"
    >
      <div
        className="relative w-full"
        style={{ height: `${virtualizer.getTotalSize()}px` }}
      >
        {virtualizer.getVirtualItems().map((item) => {
          const row = events[item.index]
          return (
            <div
              key={item.key}
              role="listitem"
              data-index={item.index}
              ref={virtualizer.measureElement}
              className="absolute top-0 left-0 w-full py-1.5 text-sm"
              style={{ transform: `translateY(${item.start}px)` }}
            >
              <div className="font-mono text-xs text-muted-foreground">
                {row.time ?? "—"}
              </div>
              <div>
                {row.label}
                {row.detail ? `: ${row.detail}` : ""}
              </div>
              <ProvenanceChip provenance={row.provenance} />
            </div>
          )
        })}
      </div>
    </div>
  )
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
        <div className="relative grid gap-1 border-b py-3 pl-6 md:grid-cols-[10rem_7rem_1fr]">
          <span
            className="absolute top-4 left-1 size-2 rounded-full bg-border"
            aria-hidden
          />
          <div className="font-mono text-xs text-muted-foreground">
            {event.time ?? "—"}
          </div>
          <div className="flex flex-wrap gap-1">
            <Badge variant="outline">{event.event_type}</Badge>
            {stayBadge}
          </div>
          <div className="space-y-1">
            <CollapsibleTrigger className="group flex items-center gap-1 text-left text-sm font-medium underline-offset-4 hover:underline">
              <ChevronDown
                className={cn(
                  "size-3.5 shrink-0 text-muted-foreground transition-transform",
                  open && "rotate-180"
                )}
              />
              {event.label} · {event.band_count ?? event.band_events.length}{" "}
              observations
            </CollapsibleTrigger>
            <ProvenanceChip provenance={event.provenance} />
            <CollapsibleContent>
              <VirtualBandRows events={event.band_events} />
            </CollapsibleContent>
          </div>
        </div>
      </Collapsible>
    )
  }

  return (
    <div className="relative grid gap-1 border-b py-3 pl-6 md:grid-cols-[10rem_7rem_1fr]">
      <span
        className="absolute top-4 left-1 size-2 rounded-full bg-border"
        aria-hidden
      />
      <div className="font-mono text-xs text-muted-foreground">
        {event.time ?? "—"}
      </div>
      <div className="flex flex-wrap gap-1">
        <Badge variant="outline">{event.event_type}</Badge>
        {stayBadge}
      </div>
      <div className="space-y-1">
        <div className="text-sm font-medium">
          {event.label}
          {event.detail ? (
            <span className="font-normal text-muted-foreground">
              {" "}
              — {event.detail}
            </span>
          ) : null}
        </div>
        <ProvenanceChip provenance={event.provenance} />
      </div>
    </div>
  )
}

function IcuStayBand({
  stay,
  events,
}: {
  stay: IcuStayInterval
  events: TimelineEvent[]
}) {
  const [open, setOpen] = useState(true)

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <div className="my-2 rounded-lg border border-primary/20 bg-muted/40">
        <div className="relative grid gap-1 border-b px-3 py-3 pl-6 md:grid-cols-[10rem_7rem_1fr]">
          <span
            className="absolute top-4 left-2 size-2.5 rounded-full bg-primary"
            aria-hidden
          />
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
            <CollapsibleTrigger className="group flex items-center gap-1 text-left text-sm font-medium underline-offset-4 hover:underline">
              <ChevronDown
                className={cn(
                  "size-3.5 shrink-0 text-muted-foreground transition-transform",
                  open && "rotate-180"
                )}
              />
              ICU Stay {stay.stay_id}: {stay.first_careunit ?? "—"} →{" "}
              {stay.last_careunit ?? "—"} · LOS {stay.los?.toFixed(2) ?? "—"}d
              {events.length
                ? ` · ${events.length} Timeline Event${events.length === 1 ? "" : "s"}`
                : ""}
            </CollapsibleTrigger>
            <ProvenanceChip provenance={stay.provenance} />
          </div>
        </div>
        <CollapsibleContent>
          <div className="ml-3 border-l-2 border-primary/30 pl-2">
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
  | {
      kind: "stay"
      time: string
      stay: IcuStayInterval
      events: TimelineEvent[]
    }

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

function TimelineSkeleton() {
  return <LoadingBlock label="Loading timeline" rows={6} />
}

function TimelineFilters({
  search,
  onApply,
}: {
  search: AdmissionSearch
  onApply: (next: AdmissionSearch) => void
}) {
  const initial = searchToForm(search)
  const form = useForm({
    defaultValues: {
      types: initial.types as string[],
      from: initial.from,
      to: initial.to,
    },
    onSubmit: ({ value }) => {
      const err = windowError(value.from, value.to)
      if (err) return
      if (value.types.length === 0) return
      onApply(formToSearch(value))
    },
  })

  return (
    <form
      className="space-y-4 rounded-lg border bg-card p-4"
      onSubmit={(e) => {
        e.preventDefault()
        void form.handleSubmit()
      }}
    >
      <div>
        <h2 className="font-heading text-sm font-semibold">Timeline filters</h2>
        <p className="text-xs text-muted-foreground">
          Filters live in the URL (`types`, `from`, `to`) so views stay shareable.
        </p>
      </div>

      <FieldGroup className="gap-4">
        <form.Field
          name="types"
          validators={{
            onChange: ({ value }) =>
              value.length === 0 ? "Select at least one event type." : undefined,
          }}
        >
          {(field) => {
            const invalid =
              field.state.meta.isTouched && !field.state.meta.isValid
            return (
              <Field data-invalid={invalid || undefined}>
                <FieldLabel>Event types</FieldLabel>
                <ToggleGroup
                  multiple
                  variant="outline"
                  size="sm"
                  className="flex flex-wrap"
                  value={field.state.value}
                  onValueChange={(next) => field.handleChange(next)}
                >
                  {ALL_EVENT_TYPES.map((t) => (
                    <ToggleGroupItem key={t} value={t} className="font-mono text-xs">
                      {t}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
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

        <div className="grid gap-3 sm:grid-cols-2">
          <form.Field name="from">
            {(field) => (
              <Field>
                <FieldLabel htmlFor="timeline-from">From</FieldLabel>
                <Input
                  id="timeline-from"
                  value={field.state.value}
                  onBlur={field.handleBlur}
                  onChange={(e) => field.handleChange(e.target.value)}
                  placeholder="YYYY-MM-DD HH:MM:SS"
                  className="font-mono text-xs"
                  autoComplete="off"
                />
                <FieldDescription>Optional lower bound (inclusive).</FieldDescription>
              </Field>
            )}
          </form.Field>

          <form.Field
            name="to"
            validators={{
              onChangeListenTo: ["from"],
              onChange: ({ value, fieldApi }) => {
                const from = fieldApi.form.getFieldValue("from")
                return windowError(from, value) ?? undefined
              },
            }}
          >
            {(field) => {
              const invalid =
                field.state.meta.isTouched && !field.state.meta.isValid
              return (
                <Field data-invalid={invalid || undefined}>
                  <FieldLabel htmlFor="timeline-to">To</FieldLabel>
                  <Input
                    id="timeline-to"
                    value={field.state.value}
                    onBlur={field.handleBlur}
                    onChange={(e) => field.handleChange(e.target.value)}
                    placeholder="YYYY-MM-DD HH:MM:SS"
                    className="font-mono text-xs"
                    autoComplete="off"
                    aria-invalid={invalid || undefined}
                  />
                  <FieldDescription>Optional upper bound (inclusive).</FieldDescription>
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
        </div>
      </FieldGroup>

      <form.Subscribe
        selector={(s) => [s.values.from, s.values.to, s.values.types] as const}
      >
        {([from, to, types]) => {
          const badWindow = windowError(from, to)
          return (
            <div className="flex flex-wrap items-center gap-2">
              <Button type="submit" size="sm" disabled={types.length === 0 || !!badWindow}>
                Apply filters
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => {
                  form.reset()
                  form.setFieldValue("types", [...ALL_EVENT_TYPES])
                  form.setFieldValue("from", "")
                  form.setFieldValue("to", "")
                  onApply({})
                }}
              >
                Clear
              </Button>
              {badWindow ? (
                <ErrorAlert
                  className="w-full"
                  title="Invalid time window"
                  message={badWindow}
                />
              ) : null}
            </div>
          )
        }}
      </form.Subscribe>
    </form>
  )
}

export function AdmissionTimeline({
  subjectId,
  hadmId,
  search,
  onSearchChange,
}: {
  subjectId: number
  hadmId: number
  search: AdmissionSearch
  onSearchChange: (next: AdmissionSearch) => void
}) {
  const clientWindowError = windowError(search.from ?? "", search.to ?? "")
  const selectedTypes = parseTypes(search.types)

  const query = useQuery({
    queryKey: [
      "timeline",
      subjectId,
      hadmId,
      search.types ?? "",
      search.from ?? "",
      search.to ?? "",
    ],
    queryFn: () =>
      api.timeline(subjectId, hadmId, {
        event_types:
          selectedTypes.length === ALL_EVENT_TYPES.length
            ? undefined
            : selectedTypes.join(","),
        start: search.from || undefined,
        end: search.to || undefined,
      }),
    enabled: !clientWindowError && selectedTypes.length > 0,
  })

  const items = useMemo(() => {
    if (!query.data) return []
    return buildTimelineItems(query.data.events, query.data.icu_stays)
  }, [query.data])

  return (
    <div className="space-y-6">
      <TimelineFilters
        key={`${search.types ?? ""}|${search.from ?? ""}|${search.to ?? ""}`}
        search={search}
        onApply={onSearchChange}
      />

      {clientWindowError ? (
        <ErrorAlert title="Invalid time window" message={clientWindowError} />
      ) : null}

      {!clientWindowError && selectedTypes.length === 0 ? (
        <ErrorAlert
          title="No event types selected"
          message="The URL `types` filter matches no known Timeline Event types. Choose at least one type and apply filters."
        />
      ) : null}

      {!clientWindowError &&
      selectedTypes.length > 0 &&
      query.isPending ? (
        <TimelineSkeleton />
      ) : null}

      {!clientWindowError && selectedTypes.length > 0 && query.isError ? (
        <ErrorAlert
          title="Could not load timeline"
          message={query.error}
          onRetry={() => void query.refetch()}
        />
      ) : null}

      {!clientWindowError &&
      selectedTypes.length > 0 &&
      query.isSuccess ? (
        <section className="space-y-3">
          <div>
            <h2 className="font-heading text-lg font-semibold">Timeline</h2>
            <p className="text-sm text-muted-foreground">
              {query.data.events.length} Timeline Event
              {query.data.events.length === 1 ? "" : "s"}
              {query.data.icu_stays.length
                ? ` · ${query.data.icu_stays.length} ICU Stay interval${
                    query.data.icu_stays.length === 1 ? "" : "s"
                  }`
                : ""}
            </p>
          </div>

          {items.length === 0 ? (
            <EmptyState
              title="No Timeline Events"
              description="Nothing matches the current type and time filters. Clear or widen filters to see more of this Admission."
              action={
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onSearchChange({})}
                >
                  Clear filters
                </Button>
              }
            />
          ) : (
            <div className="relative border-l border-border/80 pl-1">
              {items.map((item, i) =>
                item.kind === "stay" ? (
                  <IcuStayBand
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
        </section>
      ) : null}
    </div>
  )
}

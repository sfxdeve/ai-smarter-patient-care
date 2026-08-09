import { useMemo, useState } from "react"
import { Link } from "@tanstack/react-router"
import {
  createColumnHelper,
  createSortedRowModel,
  rowSortingFeature,
  sortFn_alphanumeric,
  sortFn_basic,
  tableFeatures,
  useTable,
} from "@tanstack/react-table"
import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react"

import { EmptyState } from "@/components/async-state"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { PatientSummary, TableCoverage } from "@/lib/api"
import {
  EMAR_TABLE,
  coverageFor as coverageInList,
  formatCoverageBadge,
  formatCoverageLabel,
} from "@/lib/coverage"
import { cn } from "@/lib/utils"

const features = tableFeatures({
  rowSortingFeature,
  sortedRowModel: createSortedRowModel(),
  sortFns: {
    alphanumeric: sortFn_alphanumeric,
    basic: sortFn_basic,
  },
})

const columnHelper = createColumnHelper<typeof features, PatientSummary>()

function coverageFor(
  patient: PatientSummary,
  table: string
): TableCoverage | undefined {
  return coverageInList(patient.coverage, table)
}

const columns = columnHelper.columns([
  columnHelper.accessor("subject_id", {
    header: "Patient ID",
    sortFn: "basic",
    cell: ({ getValue }) => {
      const subjectId = String(getValue())
      return (
        <Link
          to="/patients/$subjectId"
          params={{ subjectId }}
          className="font-medium tabular-nums underline-offset-4 after:absolute after:inset-0 hover:underline"
        >
          {subjectId}
        </Link>
      )
    },
  }),
  columnHelper.accessor("gender", {
    header: "Gender",
    sortFn: "alphanumeric",
    cell: ({ getValue }) => getValue() ?? "—",
  }),
  columnHelper.accessor("anchor_age", {
    header: "Anchor age",
    sortFn: "basic",
    cell: ({ getValue }) => {
      const age = getValue()
      return age == null ? "—" : <span className="tabular-nums">{age}</span>
    },
  }),
  columnHelper.accessor("anchor_year_group", {
    header: "Anchor year group",
    sortFn: "alphanumeric",
    cell: ({ getValue }) => getValue() ?? "—",
  }),
  columnHelper.accessor("admission_count", {
    header: "Admissions",
    sortFn: "basic",
    cell: ({ getValue }) => (
      <span className="tabular-nums">{getValue()}</span>
    ),
  }),
  columnHelper.accessor((row) => coverageFor(row, EMAR_TABLE), {
    id: EMAR_TABLE,
    header: "eMAR",
    sortFn: (rowA, rowB, columnId) => {
      const a = rowA.getValue<TableCoverage | undefined>(columnId)
      const b = rowB.getValue<TableCoverage | undefined>(columnId)
      const aRank = a?.has_rows ? (a.row_count ?? 0) + 1 : 0
      const bRank = b?.has_rows ? (b.row_count ?? 0) + 1 : 0
      return aRank === bRank ? 0 : aRank > bRank ? 1 : -1
    },
    cell: ({ getValue }) => {
      const emar = getValue()
      if (!emar) return "—"
      return (
        <Badge variant={emar.has_rows ? "secondary" : "outline"}>
          {formatCoverageBadge(emar)}
        </Badge>
      )
    },
  }),
  columnHelper.display({
    id: "coverage",
    header: "Other coverage",
    cell: ({ row }) => {
      const others = row.original.coverage.filter(
        (c) => c.table !== EMAR_TABLE && c.has_rows
      )
      if (others.length === 0) {
        return <span className="text-muted-foreground">—</span>
      }
      return (
        <div className="flex max-w-xs flex-wrap gap-1">
          {others.map((c) => (
            <Badge key={c.table} variant="outline" title={c.note ?? undefined}>
              {formatCoverageLabel(c.table)}
            </Badge>
          ))}
        </div>
      )
    },
  }),
])

function matchesFilter(patient: PatientSummary, query: string): boolean {
  const q = query.trim().toLowerCase()
  if (!q) return true
  const emar = coverageFor(patient, EMAR_TABLE)
  const haystack = [
    String(patient.subject_id),
    patient.gender ?? "",
    patient.anchor_age == null ? "" : String(patient.anchor_age),
    patient.anchor_year_group ?? "",
    String(patient.admission_count),
    emar?.has_rows ? "emar" : "no emar",
    ...patient.coverage.filter((c) => c.has_rows).map((c) => c.table),
  ]
    .join(" ")
    .toLowerCase()
  return haystack.includes(q)
}

function SortIcon({ sorted }: { sorted: false | "asc" | "desc" }) {
  if (sorted === "asc") return <ArrowUp className="size-3.5" />
  if (sorted === "desc") return <ArrowDown className="size-3.5" />
  return <ArrowUpDown className="size-3.5 opacity-40" />
}

export function PatientsTable({ patients }: { patients: PatientSummary[] }) {
  const [filter, setFilter] = useState("")

  const filtered = useMemo(
    () => patients.filter((p) => matchesFilter(p, filter)),
    [patients, filter]
  )

  const table = useTable({
    features,
    columns,
    data: filtered,
    initialState: {
      sorting: [{ id: "subject_id", desc: false }],
    },
    getRowId: (row) => String(row.subject_id),
  })

  const rows = table.getRowModel().rows

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter by Patient ID, gender, year group, coverage…"
          className="max-w-md"
          aria-label="Filter Patients"
        />
        <p className="text-sm text-muted-foreground tabular-nums">
          {filtered.length === patients.length
            ? `${patients.length} Patients`
            : `${filtered.length} of ${patients.length} Patients`}
        </p>
      </div>

      {rows.length === 0 ? (
        <EmptyState
          title="No Patients match"
          description="Clear or broaden the filter to see more of the cohort."
          action={
            <Button variant="outline" size="sm" onClick={() => setFilter("")}>
              Clear filter
            </Button>
          }
        />
      ) : (
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  const canSort = header.column.getCanSort()
                  const sorted = header.column.getIsSorted()
                  return (
                    <TableHead key={header.id}>
                      {header.isPlaceholder ? null : canSort ? (
                        <button
                          type="button"
                          className={cn(
                            "inline-flex items-center gap-1.5 rounded-md hover:text-foreground",
                            sorted && "text-foreground"
                          )}
                          onClick={header.column.getToggleSortingHandler()}
                        >
                          <table.FlexRender header={header} />
                          <SortIcon sorted={sorted} />
                        </button>
                      ) : (
                        <table.FlexRender header={header} />
                      )}
                    </TableHead>
                  )
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.id} className="relative hover:bg-muted/50">
                {row.getAllCells().map((cell) => (
                  <TableCell key={cell.id}>
                    <table.FlexRender cell={cell} />
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  )
}

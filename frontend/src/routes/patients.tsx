import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"

import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { api } from "@/lib/api"

export function PatientsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["patients"],
    queryFn: api.patients,
  })

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading patients…</p>
  if (error)
    return <p className="text-sm text-destructive">{(error as Error).message}</p>
  if (!data) return null

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-semibold">Patients</h1>
        <p className="text-sm text-muted-foreground">
          {data.length} deidentified patients from the MIMIC-IV Demo. eMAR medication coverage is
          present for 65 of 100.
        </p>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>subject_id</TableHead>
            <TableHead>Gender</TableHead>
            <TableHead>Anchor age</TableHead>
            <TableHead>Year group</TableHead>
            <TableHead>Admissions</TableHead>
            <TableHead>eMAR</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((p) => {
            const emar = p.coverage.find((c) => c.table === "emar")
            return (
              <TableRow key={p.subject_id}>
                <TableCell>
                  <Link
                    to="/patients/$subjectId"
                    params={{ subjectId: String(p.subject_id) }}
                    className="font-medium underline-offset-4 hover:underline"
                  >
                    {p.subject_id}
                  </Link>
                </TableCell>
                <TableCell>{p.gender ?? "—"}</TableCell>
                <TableCell>{p.anchor_age ?? "—"}</TableCell>
                <TableCell>{p.anchor_year_group ?? "—"}</TableCell>
                <TableCell>{p.admission_count}</TableCell>
                <TableCell>
                  <Badge variant={emar?.has_rows ? "default" : "secondary"}>
                    {emar?.has_rows ? "covered" : "no eMAR"}
                  </Badge>
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}

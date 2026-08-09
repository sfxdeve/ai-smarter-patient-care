import { Link } from "@tanstack/react-router"

export function PatientsPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="font-heading text-2xl font-semibold">Patients</h1>
        <p className="text-sm text-muted-foreground">
          Patients list shell. Full table arrives in ticket 02.
        </p>
      </div>
      <p className="text-sm text-muted-foreground">
        Try a known demo id once data is wired, e.g.{" "}
        <Link
          to="/patients/$subjectId"
          params={{ subjectId: "10000032" }}
          className="font-medium underline-offset-4 hover:underline"
        >
          Patient 10000032
        </Link>
        .
      </p>
    </div>
  )
}

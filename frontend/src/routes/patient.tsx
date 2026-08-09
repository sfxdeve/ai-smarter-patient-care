import { Link } from "@tanstack/react-router"

import { RouteBreadcrumbs } from "@/components/route-breadcrumbs"

export function PatientPage({ subjectId }: { subjectId: string }) {
  return (
    <div className="space-y-6">
      <RouteBreadcrumbs
        items={[
          { kind: "link", label: "Patients", to: "/" },
          { kind: "page", label: `Patient ${subjectId}` },
        ]}
      />
      <div>
        <h1 className="font-heading text-2xl font-semibold">
          Patient {subjectId}
        </h1>
        <p className="text-sm text-muted-foreground">
          Patient overview shell. Demographics, coverage, and Admission chapters
          arrive in ticket 03.
        </p>
      </div>
      <p className="text-sm text-muted-foreground">
        Admission route placeholder:{" "}
        <Link
          to="/patients/$subjectId/admissions/$hadmId"
          params={{ subjectId, hadmId: "example" }}
          className="font-medium underline-offset-4 hover:underline"
        >
          open sample Admission
        </Link>
        .
      </p>
    </div>
  )
}

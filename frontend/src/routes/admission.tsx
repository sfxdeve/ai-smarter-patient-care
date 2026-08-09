import { RouteBreadcrumbs } from "@/components/route-breadcrumbs"

export function AdmissionPage({
  subjectId,
  hadmId,
}: {
  subjectId: string
  hadmId: string
}) {
  return (
    <div className="space-y-6">
      <RouteBreadcrumbs
        items={[
          { kind: "link", label: "Patients", to: "/" },
          {
            kind: "link",
            label: `Patient ${subjectId}`,
            to: "/patients/$subjectId",
            params: { subjectId },
          },
          { kind: "page", label: `Admission ${hadmId}` },
        ]}
      />
      <div>
        <h1 className="font-heading text-2xl font-semibold">
          Admission {hadmId}
        </h1>
        <p className="text-sm text-muted-foreground">
          Admission shell for Patient {subjectId}. Timeline spine, ICU bands,
          filters, billing, and QA arrive in later tickets.
        </p>
      </div>
    </div>
  )
}

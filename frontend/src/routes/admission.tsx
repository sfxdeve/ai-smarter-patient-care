import { RouteBreadcrumbs } from "@/components/route-breadcrumbs"
import { WithQaRail } from "@/components/with-qa-rail"

export function AdmissionPage({
  subjectId,
  hadmId,
}: {
  subjectId: string
  hadmId: string
}) {
  const subjectIdNum = Number(subjectId)
  const hadmIdNum = Number(hadmId)
  const validIds = Number.isFinite(subjectIdNum) && Number.isFinite(hadmIdNum)

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
      {validIds ? (
        <WithQaRail subjectId={subjectIdNum} hadmId={hadmIdNum}>
          <div>
            <h1 className="font-heading text-2xl font-semibold">
              Admission {hadmId}
            </h1>
            <p className="text-sm text-muted-foreground">
              Admission shell for Patient {subjectId}. Timeline spine, ICU bands,
              filters, and billing arrive in later tickets. QA is scoped to this
              Admission.
            </p>
          </div>
        </WithQaRail>
      ) : (
        <div>
          <h1 className="font-heading text-2xl font-semibold">
            Admission {hadmId}
          </h1>
          <p className="text-sm text-muted-foreground">
            Invalid Patient or Admission identifier in the URL.
          </p>
        </div>
      )}
    </div>
  )
}

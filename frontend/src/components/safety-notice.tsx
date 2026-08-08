import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

const NOTICE =
  "Research and educational prototype only. Not for clinical use. Do not use for diagnosis, treatment, triage, or patient-specific recommendations."

export function SafetyNotice() {
  return (
    <Alert className="rounded-none border-x-0 border-t-0 border-amber-700/40 bg-amber-50 text-amber-950">
      <AlertTitle className="font-heading text-sm tracking-wide uppercase">
        Safety notice
      </AlertTitle>
      <AlertDescription className="text-sm text-amber-950/90">{NOTICE}</AlertDescription>
    </Alert>
  )
}

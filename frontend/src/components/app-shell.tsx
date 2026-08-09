import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"

import { SafetyNotice } from "@/components/safety-notice"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { api } from "@/lib/api"

export function AppShell({ children }: { children: React.ReactNode }) {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    staleTime: 60_000,
    retry: false,
  })

  return (
    <div className="min-h-svh bg-background text-foreground">
      <SafetyNotice />
      <header className="border-b">
        <div className="mx-auto flex max-w-6xl flex-wrap items-end justify-between gap-4 px-4 py-5">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <Link
                to="/"
                className="font-heading text-3xl font-semibold tracking-tight"
              >
                Chronicle
              </Link>
              <Badge variant="outline">Research only</Badge>
              {health.data ? (
                <Badge variant="secondary">
                  {health.data.patient_count} patients · {health.data.status}
                </Badge>
              ) : health.isError ? (
                <Badge variant="destructive">API offline</Badge>
              ) : null}
            </div>
            <p className="max-w-xl text-sm text-muted-foreground">
              Admission-centric timelines and grounded answers over the MIMIC-IV
              Clinical Database Demo. Patient rows never leave this machine.
            </p>
          </div>
          <nav className="flex gap-3 text-sm">
            <Link to="/" className="text-muted-foreground hover:text-foreground">
              Patients
            </Link>
          </nav>
        </div>
      </header>
      <Separator />
      <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
      <footer className="mx-auto max-w-6xl px-4 py-8 text-xs text-muted-foreground">
        MIMIC-IV Clinical Database Demo v2.2 (PhysioNet, ODbL). Timestamps are
        deidentified and date-shifted. Schema + template catalog + question may
        egress to the configured LLM; never patient rows (ADR 0001).
      </footer>
    </div>
  )
}

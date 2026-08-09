import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"

import { Badge } from "@/components/ui/badge"
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
      <header className="border-b">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-4">
          <div className="flex flex-wrap items-center gap-3">
            <Link
              to="/"
              className="font-heading text-2xl font-semibold tracking-tight"
            >
              Chronicle
            </Link>
            {health.isError ? (
              <Badge variant="destructive">API offline</Badge>
            ) : health.data ? (
              <span className="text-sm text-muted-foreground tabular-nums">
                {health.data.patient_count} patients
              </span>
            ) : null}
          </div>
          <nav className="flex gap-3 text-sm">
            <Link to="/" className="text-muted-foreground hover:text-foreground">
              Patients
            </Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8">{children}</main>
    </div>
  )
}

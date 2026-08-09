import { AlertCircle } from "lucide-react"

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"

function toMessage(value: unknown, fallback = "Request failed."): string {
  if (value instanceof Error) return value.message
  if (typeof value === "string" && value.trim()) return value
  return fallback
}

/** Destructive Alert + optional Retry — server errors and invalid user input. */
export function ErrorAlert({
  title,
  message,
  onRetry,
  actions,
  className,
}: {
  title: string
  message?: unknown
  onRetry?: () => void
  actions?: React.ReactNode
  className?: string
}) {
  return (
    <Alert variant="destructive" className={className}>
      <AlertCircle />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription>{toMessage(message)}</AlertDescription>
      {onRetry || actions ? (
        <div className="col-start-2 mt-2 flex flex-wrap gap-2">
          {onRetry ? (
            <Button variant="outline" size="sm" onClick={onRetry}>
              Retry
            </Button>
          ) : null}
          {actions}
        </div>
      ) : null}
    </Alert>
  )
}

/** Empty + optional next action. */
export function EmptyState({
  title,
  description,
  action,
  className,
}: {
  title: string
  description: React.ReactNode
  action?: React.ReactNode
  className?: string
}) {
  return (
    <Empty className={cn("border py-12", className)}>
      <EmptyHeader>
        <EmptyTitle>{title}</EmptyTitle>
        <EmptyDescription>{description}</EmptyDescription>
      </EmptyHeader>
      {action ? <EmptyContent>{action}</EmptyContent> : null}
    </Empty>
  )
}

export function LoadingBlock({
  label,
  rows = 4,
  className,
  children,
}: {
  label: string
  rows?: number
  className?: string
  children?: React.ReactNode
}) {
  return (
    <div
      className={cn("space-y-3", className)}
      aria-busy="true"
      aria-label={label}
    >
      {children ??
        Array.from({ length: rows }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
    </div>
  )
}

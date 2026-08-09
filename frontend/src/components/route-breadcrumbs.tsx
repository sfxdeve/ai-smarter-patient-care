import { Link } from "@tanstack/react-router"

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"

type Crumb =
  | {
      kind: "link"
      label: string
      to: "/" | "/patients/$subjectId" | "/patients/$subjectId/admissions/$hadmId"
      params?: { subjectId?: string; hadmId?: string }
    }
  | { kind: "page"; label: string }

export function RouteBreadcrumbs({ items }: { items: Crumb[] }) {
  return (
    <Breadcrumb>
      <BreadcrumbList>
        {items.flatMap((item, index) => {
          const nodes = []
          if (index > 0) {
            nodes.push(<BreadcrumbSeparator key={`sep-${index}`} />)
          }
          nodes.push(
            <BreadcrumbItem key={`item-${index}`}>
              {item.kind === "page" || index === items.length - 1 ? (
                <BreadcrumbPage>{item.label}</BreadcrumbPage>
              ) : (
                <BreadcrumbLink
                  render={<Link to={item.to} params={item.params} />}
                >
                  {item.label}
                </BreadcrumbLink>
              )}
            </BreadcrumbItem>
          )
          return nodes
        })}
      </BreadcrumbList>
    </Breadcrumb>
  )
}

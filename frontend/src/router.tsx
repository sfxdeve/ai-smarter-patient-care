import {
  Outlet,
  createRootRoute,
  createRoute,
  createRouter,
} from "@tanstack/react-router"

import { AppShell } from "@/components/layout"
import { PatientDetailPage } from "@/routes/patient-detail"
import { PatientsPage } from "@/routes/patients"

const rootRoute = createRootRoute({
  component: () => (
    <AppShell>
      <Outlet />
    </AppShell>
  ),
})

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: PatientsPage,
})

const patientRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/patients/$subjectId",
  component: function PatientRoute() {
    const { subjectId } = patientRoute.useParams()
    return <PatientDetailPage subjectId={Number(subjectId)} />
  },
})

const routeTree = rootRoute.addChildren([indexRoute, patientRoute])

export const router = createRouter({ routeTree })

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router
  }
}

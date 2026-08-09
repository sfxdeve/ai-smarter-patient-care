import {
  Outlet,
  createRootRoute,
  createRoute,
  createRouter,
} from "@tanstack/react-router"

import { AppShell } from "@/components/app-shell"
import { AdmissionPage } from "@/routes/admission"
import { PatientPage } from "@/routes/patient"
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
    return <PatientPage subjectId={subjectId} />
  },
})

const admissionRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/patients/$subjectId/admissions/$hadmId",
  component: function AdmissionRoute() {
    const { subjectId, hadmId } = admissionRoute.useParams()
    return <AdmissionPage subjectId={subjectId} hadmId={hadmId} />
  },
})

const routeTree = rootRoute.addChildren([
  indexRoute,
  patientRoute,
  admissionRoute,
])

export const router = createRouter({ routeTree })

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router
  }
}

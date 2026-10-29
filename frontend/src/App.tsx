/** Routes by role after login (Design 8.3). */
import type { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout, PublicLayout } from "./components/Layout";
import { Loading } from "./components/ui";
import { landing, useAuth } from "./lib/auth";
import SimilarityChecks from "./pages/academic/Similarity";
import AcademicStudents from "./pages/academic/Students";
import CompanyTeam from "./pages/company/Team";
import CompanyTrainees from "./pages/company/Trainees";
import Applicants from "./pages/company/Applicants";
import CompanyVacancies from "./pages/company/Vacancies";
import VacancyEditor from "./pages/company/VacancyEditor";
import AuditLog from "./pages/coordinator/Audit";
import Certificates from "./pages/coordinator/Certificates";
import CycleDetail from "./pages/coordinator/CycleDetail";
import Cycles from "./pages/coordinator/Cycles";
import Escalations from "./pages/coordinator/Escalations";
import Exports from "./pages/coordinator/Exports";
import Grades from "./pages/coordinator/Grades";
import Placements from "./pages/coordinator/Placements";
import CoordinatorStudents from "./pages/coordinator/Students";
import Supervisors from "./pages/coordinator/Supervisors";
import Catalog from "./pages/platform/Catalog";
import Organizations from "./pages/platform/Organizations";
import PlatformVerifications from "./pages/platform/Verifications";
import { AcceptInvite, ConfirmEmail, ForgotPassword, ResetPassword } from "./pages/public/Links";
import Login from "./pages/public/Login";
import Register from "./pages/public/Register";
import Verify from "./pages/public/Verify";
import Consent from "./pages/shared/Consent";
import Home from "./pages/shared/Home";
import Notifications from "./pages/shared/Notifications";
import PlacementReports from "./pages/shared/PlacementReports";
import ReportSlot from "./pages/shared/ReportSlot";
import Verification from "./pages/shared/Verification";
import Applications from "./pages/student/Applications";
import Feedback from "./pages/student/Feedback";
import Profile from "./pages/student/Profile";
import StudentReports from "./pages/student/Reports";
import Vacancies from "./pages/student/Vacancies";

type Role = "student" | "company_supervisor" | "academic_supervisor" | "coordinator" | "platform_admin";

/** Signed in, consent given, the right role, and verified unless the page allows a pending account. */
function Guard({ roles, unverified = false, children }: { roles?: Role[]; unverified?: boolean; children: ReactNode }) {
  const { me, ready } = useAuth();
  if (!ready) return <Loading />;
  if (!me) return <Navigate to="/login" replace />;
  if (me.consent_required) return <Navigate to="/consent" replace />;
  if (roles && !roles.includes(me.role as Role)) return <Navigate to={landing(me)} replace />;
  if (!unverified && ["pending", "rejected"].includes(me.verification_status)) {
    return <Navigate to={me.role === "student" ? "/student" : "/verification"} replace />;
  }
  return <>{children}</>;
}

function Start() {
  const { me, ready } = useAuth();
  if (!ready) return <Loading />;
  return <Navigate to={me ? landing(me) : "/login"} replace />;
}

function SignedIn({ children }: { children: ReactNode }) {
  const { me, ready } = useAuth();
  if (!ready) return <Loading />;
  return me ? <>{children}</> : <Navigate to="/login" replace />;
}

const ST: Role[] = ["student"];
const CS: Role[] = ["company_supervisor"];
const AS: Role[] = ["academic_supervisor"];
const CO: Role[] = ["coordinator"];
const PA: Role[] = ["platform_admin"];

export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/confirm/:token" element={<ConfirmEmail />} />
        <Route path="/invite/:token" element={<AcceptInvite />} />
        <Route path="/forgot" element={<ForgotPassword />} />
        <Route path="/reset/:token" element={<ResetPassword />} />
        <Route path="/consent" element={<SignedIn><Consent /></SignedIn>} />
        <Route path="/verify" element={<Verify />} />
        <Route path="/verify/:code" element={<Verify />} />
      </Route>
      <Route element={<Guard unverified><AppLayout /></Guard>}>
        <Route path="/verification" element={<Verification />} />
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/student" element={<Guard roles={ST} unverified><Home /></Guard>} />
        <Route path="/student/profile" element={<Guard roles={ST} unverified><Profile /></Guard>} />
        <Route path="/student/vacancies" element={<Guard roles={ST} unverified><Vacancies /></Guard>} />
        <Route path="/student/applications" element={<Guard roles={ST}><Applications /></Guard>} />
        <Route path="/student/reports" element={<Guard roles={ST}><StudentReports /></Guard>} />
        <Route path="/student/feedback" element={<Guard roles={ST}><Feedback /></Guard>} />
        <Route path="/company" element={<Guard roles={CS}><Home /></Guard>} />
        <Route path="/company/vacancies" element={<Guard roles={CS}><CompanyVacancies /></Guard>} />
        <Route path="/company/vacancies/new" element={<Guard roles={CS}><VacancyEditor /></Guard>} />
        <Route path="/company/vacancies/:vacancyId" element={<Guard roles={CS}><VacancyEditor /></Guard>} />
        <Route path="/company/vacancies/:vacancyId/applicants" element={<Guard roles={CS}><Applicants /></Guard>} />
        <Route path="/company/trainees" element={<Guard roles={CS}><CompanyTrainees /></Guard>} />
        <Route path="/company/team" element={<Guard roles={CS}><CompanyTeam /></Guard>} />
        <Route path="/academic" element={<Guard roles={AS}><Home /></Guard>} />
        <Route path="/academic/students" element={<Guard roles={AS}><AcademicStudents /></Guard>} />
        <Route path="/academic/grades" element={<Guard roles={AS}><Grades /></Guard>} />
        <Route path="/academic/similarity" element={<Guard roles={AS}><SimilarityChecks /></Guard>} />
        <Route path="/coordinator" element={<Guard roles={CO}><Home /></Guard>} />
        <Route path="/coordinator/students" element={<Guard roles={CO}><CoordinatorStudents /></Guard>} />
        <Route path="/coordinator/supervisors" element={<Guard roles={CO}><Supervisors /></Guard>} />
        <Route path="/coordinator/cycles" element={<Guard roles={CO}><Cycles /></Guard>} />
        <Route path="/coordinator/cycles/:cycleId" element={<Guard roles={CO}><CycleDetail /></Guard>} />
        <Route path="/coordinator/placements" element={<Guard roles={CO}><Placements /></Guard>} />
        <Route path="/coordinator/grades" element={<Guard roles={CO}><Grades /></Guard>} />
        <Route path="/coordinator/escalations" element={<Guard roles={CO}><Escalations /></Guard>} />
        <Route path="/coordinator/exports" element={<Guard roles={CO}><Exports /></Guard>} />
        <Route path="/coordinator/certificates" element={<Guard roles={CO}><Certificates /></Guard>} />
        <Route path="/coordinator/audit" element={<Guard roles={CO}><AuditLog /></Guard>} />
        <Route path="/platform" element={<Guard roles={PA}><Home /></Guard>} />
        <Route path="/platform/verifications" element={<Guard roles={PA}><PlatformVerifications /></Guard>} />
        <Route path="/platform/organizations" element={<Guard roles={PA}><Organizations /></Guard>} />
        <Route path="/platform/catalog" element={<Guard roles={PA}><Catalog /></Guard>} />
        <Route path="/platform/audit" element={<Guard roles={PA}><AuditLog /></Guard>} />
        <Route path="/placements/:placementId" element={<Guard roles={[...ST, ...CS, ...AS, ...CO]}><PlacementReports /></Guard>} />
        <Route path="/reports/:slotId" element={<Guard roles={[...ST, ...CS, ...AS, ...CO]}><ReportSlot /></Guard>} />
      </Route>
      <Route path="*" element={<Start />} />
    </Routes>
  );
}

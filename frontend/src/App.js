import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "@/App.css";
import { Toaster } from "sonner";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { ThemeProvider } from "@/context/ThemeContext";
import { I18nProvider } from "@/lib/i18n.jsx";

import Landing from "@/pages/Landing";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Subscription from "@/pages/Subscription";

import DashboardLayout from "@/layouts/DashboardLayout";
import SuperDashboard from "@/pages/super/SuperDashboard";
import Schools from "@/pages/super/Schools";
import Plans from "@/pages/super/Plans";
import SuperPayments from "@/pages/super/Payments";
import AuditLogs from "@/pages/super/AuditLogs";

import SchoolDashboard from "@/pages/school/SchoolDashboard";
import Students from "@/pages/school/Students";
import Teachers from "@/pages/school/Teachers";
import Parents from "@/pages/school/Parents";
import Classes from "@/pages/school/Classes";
import Attendance from "@/pages/school/Attendance";
import Fees from "@/pages/school/Fees";
import Exams from "@/pages/school/Exams";
import Timetable from "@/pages/school/Timetable";
import Notices from "@/pages/school/Notices";
import Settings from "@/pages/school/Settings";
import UsersPage from "@/pages/school/Users";
import Diary from "@/pages/school/Diary";
import Reminders from "@/pages/school/Reminders";
import ChangePassword from "@/pages/school/ChangePassword";
import FeeVoucher from "@/pages/school/FeeVoucher";
import ResultCard from "@/pages/school/ResultCard";
import StudentProfile from "@/pages/school/StudentProfile";
import IdCardPreview from "@/pages/school/IdCardPreview";

function Protected({ role, children }) {
  const { user, checking } = useAuth();
  if (checking) return <div className="min-h-screen grid place-items-center text-muted-foreground">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (role && !role.includes(user.role)) return <Navigate to="/" replace />;
  return children;
}

function RoleHome() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return user.role === "super_admin" ? <Navigate to="/super-admin" replace /> : <Navigate to="/app" replace />;
}

export default function App() {
  return (
    <I18nProvider>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <Toaster position="top-right" richColors />
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/home" element={<RoleHome />} />
              <Route path="/subscription" element={<Protected role={["school_admin"]}><Subscription /></Protected>} />

              {/* Super admin */}
              <Route path="/super-admin" element={<Protected role={["super_admin"]}><DashboardLayout kind="super" /></Protected>}>
                <Route index element={<SuperDashboard />} />
                <Route path="schools" element={<Schools />} />
                <Route path="plans" element={<Plans />} />
                <Route path="payments" element={<SuperPayments />} />
                <Route path="audit" element={<AuditLogs />} />
              </Route>

              {/* School */}
              <Route path="/app" element={<Protected role={["school_admin","teacher","accountant","receptionist","librarian","parent","student"]}><DashboardLayout kind="school" /></Protected>}>
                <Route index element={<SchoolDashboard />} />
                <Route path="students" element={<Students />} />
                <Route path="students/:id" element={<StudentProfile />} />
                <Route path="teachers" element={<Teachers />} />
                <Route path="parents" element={<Parents />} />
                <Route path="classes" element={<Classes />} />
                <Route path="attendance" element={<Attendance />} />
                <Route path="fees" element={<Fees />} />
                <Route path="exams" element={<Exams />} />
                <Route path="timetable" element={<Timetable />} />
                <Route path="notices" element={<Notices />} />
                <Route path="diary" element={<Diary />} />
                <Route path="reminders" element={<Reminders />} />
                <Route path="change-password" element={<ChangePassword />} />
                <Route path="users" element={<UsersPage />} />
                <Route path="settings" element={<Settings />} />
              </Route>

              {/* Standalone print routes (no sidebar) */}
              <Route path="/print/voucher/:invoiceId" element={<Protected role={["school_admin","teacher","accountant","parent","student"]}><FeeVoucher /></Protected>} />
              <Route path="/print/result-card/:examId/:studentId" element={<Protected role={["school_admin","teacher","parent","student"]}><ResultCard /></Protected>} />
              <Route path="/print/id-card/:studentId" element={<Protected role={["school_admin","teacher","receptionist","accountant","parent","student"]}><IdCardPreview /></Protected>} />

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </I18nProvider>
  );
}

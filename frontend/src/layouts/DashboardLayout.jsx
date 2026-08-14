import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { useI18n } from "@/lib/i18n.jsx";
import { useTheme } from "@/context/ThemeContext";
import { Button } from "@/components/ui/button";
import { useEffect, useState } from "react";
import api from "@/lib/api";
import {
  GraduationCap, LayoutDashboard, School, CreditCard, Wallet, ClipboardList,
  Users, UserCog, Users2, BookOpen, CalendarCheck, Receipt, GraduationCap as GradIcon,
  CalendarClock, Megaphone, Cog, LogOut, Menu, Sun, Moon, Languages, ShieldCheck, UserPlus,
  NotebookPen, MessageCircle, KeyRound, Coins, Landmark, BarChart3, UserPlus2, ShieldCheck as ShieldIcon
} from "lucide-react";

const superLinks = [
  { to: "/super-admin", end: true, icon: LayoutDashboard, key: "dashboard" },
  { to: "/super-admin/schools", icon: School, key: "schools" },
  { to: "/super-admin/plans", icon: CreditCard, key: "plans" },
  { to: "/super-admin/payments", icon: Wallet, key: "payments" },
  { to: "/super-admin/audit", icon: ClipboardList, key: "audit" },
  { to: "/super-admin/system-settings", icon: ShieldIcon, key: "systemSettings" },
];
const schoolLinks = [
  { to: "/app", end: true, icon: LayoutDashboard, key: "dashboard" },
  { to: "/app/admissions", icon: UserPlus2, key: "admissions" },
  { to: "/app/students", icon: Users, key: "students" },
  { to: "/app/teachers", icon: GradIcon, key: "teachers" },
  { to: "/app/parents", icon: Users2, key: "parents" },
  { to: "/app/classes", icon: BookOpen, key: "classes" },
  { to: "/app/attendance", icon: CalendarCheck, key: "attendance" },
  { to: "/app/fees", icon: Receipt, key: "fees" },
  { to: "/app/expenses", icon: Coins, key: "expenses" },
  { to: "/app/payroll", icon: Landmark, key: "payroll" },
  { to: "/app/exams", icon: ClipboardList, key: "exams" },
  { to: "/app/timetable", icon: CalendarClock, key: "timetable" },
  { to: "/app/diary", icon: NotebookPen, key: "diary" },
  { to: "/app/notices", icon: Megaphone, key: "notices" },
  { to: "/app/reports", icon: BarChart3, key: "reports" },
  { to: "/app/reminders", icon: MessageCircle, key: "reminders" },
  { to: "/app/users", icon: UserPlus, key: "users" },
  { to: "/app/settings", icon: Cog, key: "settings" },
  { to: "/app/change-password", icon: KeyRound, key: "changePassword" },
];

export default function DashboardLayout({ kind }) {
  const { user, logout } = useAuth();
  const { t, toggle, lang } = useI18n();
  const { theme, toggle: toggleTheme } = useTheme();
  const nav = useNavigate();
  const [open, setOpen] = useState(false);
  const [school, setSchool] = useState(null);
  const links = kind === "super" ? superLinks : schoolLinks;

  useEffect(() => {
    if (kind === "school") {
      api.get("/school/me").then((r) => setSchool(r.data)).catch(() => {});
    }
  }, [kind]);

  const isSchoolAdminOnly = user?.role === "school_admin";
  const isTeacher = user?.role === "teacher";
  const filteredLinks = links.filter((l) => {
    if (kind === "school" && !isSchoolAdminOnly) {
      if (["users","settings","reminders","expenses","payroll","admissions","reports"].includes(l.key)) {
        if (!(l.key === "admissions" && user?.role === "receptionist") && !(["expenses","payroll","reports"].includes(l.key) && user?.role === "accountant")) return false;
      }
    }
    // Parents/students see only relevant pages
    if (kind === "school" && ["parent","student"].includes(user?.role)) {
      return ["dashboard","diary","notices","fees","exams","timetable","changePassword"].includes(l.key);
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <aside className={`${open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"} rtl:translate-x-0 fixed lg:sticky top-0 h-screen w-64 border-e border-border bg-card z-30 transition-transform duration-200 flex flex-col`}>
        <div className="h-16 flex items-center gap-2 px-4 border-b border-border">
          <div className="h-9 w-9 rounded-xl bg-primary text-primary-foreground grid place-items-center">
            <GraduationCap className="h-5 w-5"/>
          </div>
          <div>
            <div className="font-display font-semibold text-sm">Skoolzoom</div>
            <div className="text-[10px] text-muted-foreground uppercase tracking-wide">{kind === "super" ? "Platform Console" : "School ERP"}</div>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto p-3 space-y-0.5">
          {filteredLinks.map((l) => (
            <NavLink
              key={l.key}
              to={l.to}
              end={l.end}
              onClick={() => setOpen(false)}
              data-testid={`nav-${l.key}`}
              className={({isActive}) => `flex items-center gap-3 px-3 h-10 rounded-md text-sm transition-colors ${isActive ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-secondary hover:text-foreground"}`}
            >
              <l.icon className="h-4 w-4" strokeWidth={1.75}/>
              <span>{t(l.key) || l.key}</span>
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-border text-[11px] text-muted-foreground">
          <div className="flex items-center gap-2 mb-1"><ShieldCheck className="h-3 w-3"/> {t("developedBy")}</div>
          <div className="ms-5">{t("contactDev")}</div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 min-w-0 flex flex-col">
        <header className="h-16 border-b border-border bg-background sticky top-0 z-20 flex items-center gap-3 px-4 sm:px-6">
          <button className="lg:hidden" onClick={()=>setOpen(!open)} data-testid="menu-toggle"><Menu className="h-5 w-5"/></button>
          <div className="flex-1">
            {kind === "school" && school?.name && (
              <div>
                <div className="text-xs text-muted-foreground">{school?.city || "—"}</div>
                <div className="font-medium text-sm">{school.name}</div>
              </div>
            )}
            {kind === "super" && <div className="font-medium text-sm">Super Admin Console</div>}
          </div>

          {/* Trial / subscription pill */}
          {kind === "school" && school && (
            <div className={`hidden sm:flex items-center gap-2 rounded-full px-3 py-1 text-xs border ${school.expired ? "border-destructive/40 bg-destructive/10 text-destructive" : school.is_trial ? "border-accent bg-accent/10 text-accent-foreground" : "border-primary/40 bg-primary/10 text-primary"}`}
                 data-testid="subscription-pill">
              {school.expired ? (
                <><span>{school.is_trial ? t("trialExpired") : t("subExpired")}</span>
                  <button onClick={()=>nav("/subscription")} className="underline">{t("renewNow")}</button></>
              ) : (
                <span>{school.days_remaining} {t("trialLeft")}</span>
              )}
            </div>
          )}

          <button onClick={toggle} data-testid="lang-toggle" className="h-9 px-3 rounded-full border border-border hover:bg-secondary text-xs flex items-center gap-1"><Languages className="h-3.5 w-3.5"/>{lang === "en" ? "اردو" : "EN"}</button>
          <button onClick={toggleTheme} data-testid="theme-toggle" className="h-9 w-9 rounded-full border border-border hover:bg-secondary grid place-items-center">{theme==="dark"?<Sun className="h-4 w-4"/>:<Moon className="h-4 w-4"/>}</button>
          <div className="hidden md:flex flex-col items-end text-xs">
            <span className="font-medium">{user?.name}</span>
            <span className="text-muted-foreground capitalize">{user?.role?.replace("_"," ")}</span>
          </div>
          <Button variant="outline" size="sm" onClick={async()=>{await logout(); nav("/login");}} data-testid="logout-btn"><LogOut className="h-4 w-4 me-2"/>{t("signOut")}</Button>
        </header>
        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          <Outlet context={{ school }}/>
        </main>
        <footer className="border-t border-border py-3 px-6 text-xs text-muted-foreground text-center" data-testid="app-footer">
          {t("developedBy")} · {t("contactDev")}
        </footer>
      </div>
    </div>
  );
}

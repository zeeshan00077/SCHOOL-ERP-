import { Link } from "react-router-dom";
import { useI18n } from "@/lib/i18n.jsx";
import { useTheme } from "@/context/ThemeContext";
import { Button } from "@/components/ui/button";
import { GraduationCap, Sun, Moon, Languages, CheckCircle2, ShieldCheck, Users, BookOpen, Wallet, Calendar, MessageSquare, BarChart3, Bus, Library, Sparkles, ArrowRight } from "lucide-react";

function Nav() {
  const { t, toggle, lang } = useI18n();
  const { theme, toggle: toggleTheme } = useTheme();
  return (
    <header className="sticky top-0 z-40 glass border-b border-border">
      <div className="max-w-7xl mx-auto flex items-center justify-between px-4 sm:px-6 py-4">
        <Link to="/" className="flex items-center gap-2" data-testid="brand-link">
          <div className="h-9 w-9 rounded-xl bg-primary text-primary-foreground grid place-items-center">
            <GraduationCap className="h-5 w-5" strokeWidth={1.75}/>
          </div>
          <span className="font-display text-xl font-semibold">{t("brand")}</span>
        </Link>
        <nav className="hidden md:flex items-center gap-6 text-sm text-muted-foreground">
          <a href="#features" className="hover:text-foreground transition-colors">{t("features")}</a>
          <a href="#modules" className="hover:text-foreground transition-colors">{t("modules")}</a>
          <a href="#pricing" className="hover:text-foreground transition-colors">{t("pricing")}</a>
          <a href="#faq" className="hover:text-foreground transition-colors">{t("faq")}</a>
        </nav>
        <div className="flex items-center gap-2">
          <button data-testid="lang-toggle" onClick={toggle} className="h-9 px-3 rounded-full border border-border hover:bg-secondary flex items-center gap-1.5 text-sm">
            <Languages className="h-4 w-4"/> {lang === "en" ? "اردو" : "EN"}
          </button>
          <button data-testid="theme-toggle" onClick={toggleTheme} className="h-9 w-9 rounded-full border border-border hover:bg-secondary grid place-items-center">
            {theme === "dark" ? <Sun className="h-4 w-4"/> : <Moon className="h-4 w-4"/>}
          </button>
          <Link to="/login"><Button variant="ghost" size="sm" data-testid="login-btn">{t("signIn")}</Button></Link>
          <Link to="/register"><Button size="sm" data-testid="cta-trial-nav" className="rounded-full">{t("startTrial")}</Button></Link>
        </div>
      </div>
    </header>
  );
}

const modules = [
  { icon: Users, label: "Students & Parents" },
  { icon: GraduationCap, label: "Teachers & HR" },
  { icon: Calendar, label: "Attendance" },
  { icon: Wallet, label: "Fees & Accounts" },
  { icon: BookOpen, label: "Exams & Results" },
  { icon: Calendar, label: "Timetable" },
  { icon: MessageSquare, label: "Notices" },
  { icon: BarChart3, label: "Reports" },
  { icon: Bus, label: "Transport" },
  { icon: Library, label: "Library" },
  { icon: ShieldCheck, label: "Roles & Audit" },
  { icon: Sparkles, label: "Multi-tenant SaaS" },
];

export default function Landing() {
  const { t } = useI18n();
  return (
    <div className="min-h-screen bg-background">
      <Nav/>

      {/* HERO */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 grid-dots opacity-70 pointer-events-none"/>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-20 lg:py-32 grid lg:grid-cols-12 gap-10 items-center relative">
          <div className="lg:col-span-7">
            <div className="inline-flex items-center gap-2 rounded-full border border-border bg-secondary px-3 py-1 text-xs mb-6">
              <span className="h-1.5 w-1.5 rounded-full bg-primary"/> Multi-tenant SaaS · Trusted by Pakistani schools
            </div>
            <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold leading-[1.05] tracking-tight">
              {t("tagline")}
            </h1>
            <p className="mt-6 text-base sm:text-lg text-muted-foreground max-w-2xl">
              {t("heroSub")}
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/register"><Button size="lg" data-testid="hero-cta-trial" className="rounded-full h-12 px-6">{t("startTrial")} <ArrowRight className="ms-2 h-4 w-4 rtl-flip"/></Button></Link>
              <Link to="/login"><Button size="lg" variant="outline" data-testid="hero-cta-demo" className="rounded-full h-12 px-6">Sign in to demo school</Button></Link>
            </div>
            <div className="mt-8 flex flex-wrap gap-6 text-sm text-muted-foreground">
              <div className="flex items-center gap-1.5"><CheckCircle2 className="h-4 w-4 text-primary"/> 7-day free trial</div>
              <div className="flex items-center gap-1.5"><CheckCircle2 className="h-4 w-4 text-primary"/> No credit card required</div>
              <div className="flex items-center gap-1.5"><CheckCircle2 className="h-4 w-4 text-primary"/> Urdu + English</div>
            </div>
          </div>
          <div className="lg:col-span-5">
            <div className="relative rounded-2xl border border-border bg-card p-4 shadow-xl">
              <div className="rounded-xl overflow-hidden ring-1 ring-border">
                <img src="https://images.unsplash.com/photo-1543269865-0a740d43b90c?crop=entropy&cs=srgb&fm=jpg&w=900&q=80" alt="Students" className="w-full h-72 object-cover"/>
              </div>
              <div className="absolute -bottom-6 -start-6 rounded-xl bg-background border border-border p-4 shadow-lg w-56">
                <div className="text-xs text-muted-foreground">Today's Collection</div>
                <div className="mt-1 font-display text-2xl font-semibold">PKR 84,500</div>
                <div className="mt-1 text-xs text-primary">▲ 12% vs yesterday</div>
              </div>
              <div className="absolute -top-6 -end-6 rounded-xl bg-background border border-border p-4 shadow-lg w-52">
                <div className="text-xs text-muted-foreground">Attendance</div>
                <div className="mt-1 font-display text-2xl font-semibold">96.2%</div>
                <div className="mt-1 text-xs text-muted-foreground">742 / 771 present</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* MODULES */}
      <section id="modules" className="py-20 border-t border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="max-w-2xl">
            <h2 className="font-display text-3xl sm:text-4xl font-bold">One platform. Every school workflow.</h2>
            <p className="mt-3 text-muted-foreground">Front desk to final results — every module is tenant-isolated, audit-logged and mobile-ready.</p>
          </div>
          <div className="mt-10 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {modules.map((m, i) => (
              <div key={i} className="card-hover rounded-xl border border-border bg-card p-5">
                <div className="h-10 w-10 rounded-lg bg-primary/10 text-primary grid place-items-center mb-3">
                  <m.icon className="h-5 w-5" strokeWidth={1.75}/>
                </div>
                <div className="font-medium">{m.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PRICING */}
      <section id="pricing" className="py-20 border-t border-border bg-secondary/40">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 text-center">
          <h2 className="font-display text-3xl sm:text-4xl font-bold">Simple, transparent pricing</h2>
          <p className="mt-3 text-muted-foreground">Start with 7 days free. Upgrade whenever your school is ready.</p>
          <div className="mt-10 grid md:grid-cols-2 gap-6 text-start">
            <div className="rounded-2xl border border-border bg-card p-8">
              <div className="text-sm text-muted-foreground">Annual School Plan</div>
              <div className="mt-3 font-display text-4xl font-bold">PKR 25,000<span className="text-base text-muted-foreground font-normal">/year</span></div>
              <ul className="mt-6 space-y-2 text-sm">
                <li className="flex gap-2"><CheckCircle2 className="h-4 w-4 text-primary mt-0.5"/> Up to 500 students</li>
                <li className="flex gap-2"><CheckCircle2 className="h-4 w-4 text-primary mt-0.5"/> Up to 100 teachers</li>
                <li className="flex gap-2"><CheckCircle2 className="h-4 w-4 text-primary mt-0.5"/> Core modules included</li>
              </ul>
              <Link to="/register"><Button className="mt-6 w-full rounded-full">Start free trial</Button></Link>
            </div>
            <div className="rounded-2xl border-2 border-primary bg-card p-8 relative">
              <span className="absolute -top-3 start-6 bg-primary text-primary-foreground text-xs px-3 py-1 rounded-full">Best for larger schools</span>
              <div className="text-sm text-muted-foreground">Enterprise Plan</div>
              <div className="mt-3 font-display text-4xl font-bold">PKR 75,000<span className="text-base text-muted-foreground font-normal">/year</span></div>
              <ul className="mt-6 space-y-2 text-sm">
                <li className="flex gap-2"><CheckCircle2 className="h-4 w-4 text-primary mt-0.5"/> Up to 5,000 students</li>
                <li className="flex gap-2"><CheckCircle2 className="h-4 w-4 text-primary mt-0.5"/> Up to 500 teachers</li>
                <li className="flex gap-2"><CheckCircle2 className="h-4 w-4 text-primary mt-0.5"/> All modules & priority support</li>
              </ul>
              <Link to="/register"><Button variant="outline" className="mt-6 w-full rounded-full">Talk to us</Button></Link>
            </div>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-border py-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
          <div>© {new Date().getFullYear()} {t("brand")} — Multi-tenant School ERP SaaS</div>
          <div data-testid="developer-branding">{t("developedBy")} · {t("contactDev")}</div>
        </div>
      </footer>
    </div>
  );
}

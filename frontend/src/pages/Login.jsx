import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { useI18n } from "@/lib/i18n.jsx";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { GraduationCap } from "lucide-react";
import { toast } from "sonner";

export default function Login() {
  const { t } = useI18n();
  const { login, apiErr } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [showDemo, setShowDemo] = useState(false);

  const submit = async (e) => {
    e.preventDefault(); setBusy(true);
    try {
      const u = await login(email, password);
      toast.success(`Welcome back, ${u.name}`);
      nav(u.role === "super_admin" ? "/super-admin" : "/app");
    } catch (err) { toast.error(apiErr(err)); }
    finally { setBusy(false); }
  };

  const quick = (e, p) => { setEmail(e); setPassword(p); };

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      <div className="hidden lg:flex bg-primary text-primary-foreground p-12 flex-col justify-between grid-dots">
        <Link to="/" className="flex items-center gap-2">
          <div className="h-10 w-10 rounded-xl bg-primary-foreground text-primary grid place-items-center">
            <GraduationCap className="h-5 w-5"/></div>
          <span className="font-display text-xl font-semibold">Skoolzoom</span>
        </Link>
        <div>
          <h2 className="font-display text-4xl font-bold leading-tight">Manage your whole school from one place.</h2>
          <p className="mt-4 opacity-80">Attendance, fees, exams, timetables, notices — beautifully integrated for Pakistani schools.</p>
        </div>
        <div className="text-xs opacity-70" data-testid="developer-branding-login">Developed by Zeeshan Computers Sheikh Fazal · 0343-0819382</div>
      </div>
      <div className="p-6 sm:p-10 flex items-center justify-center bg-background">
        <div className="w-full max-w-md">
          <h1 className="font-display text-3xl font-bold">Sign in</h1>
          <p className="text-sm text-muted-foreground mt-1">Welcome back. Enter your credentials to continue.</p>
          <form onSubmit={submit} className="mt-8 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">{t("email")}</Label>
              <Input data-testid="login-email" id="email" type="email" required value={email} onChange={(e)=>setEmail(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">{t("password")}</Label>
              <Input data-testid="login-password" id="password" type="password" required value={password} onChange={(e)=>setPassword(e.target.value)} />
            </div>
            <Button data-testid="login-submit" type="submit" disabled={busy} className="w-full h-11 rounded-md">{busy ? "Signing in…" : t("login")}</Button>
          </form>
          <div className="mt-6 rounded-lg border border-border bg-secondary/40 p-4 text-xs">
            <button type="button" onClick={()=>setShowDemo(!showDemo)} className="w-full text-start font-medium mb-2 flex items-center justify-between" data-testid="show-demo-toggle">
              <span>Development demo accounts</span>
              <span className="text-muted-foreground">{showDemo ? "Hide" : "Show"}</span>
            </button>
            {showDemo && (
              <>
              <div className="text-muted-foreground text-[11px] mb-2">These credentials are for development only. Rotate them before going to production.</div>
              <div className="grid gap-1.5">
                <button type="button" data-testid="fill-super" onClick={()=>quick("zeeshan.ali98558@gmail.com","ZeeshanAdmin@2026")} className="text-start hover:text-primary">Super Admin → zeeshan.ali98558@gmail.com</button>
                <button type="button" data-testid="fill-schoolA" onClick={()=>quick("admin@greenvalley.edu","School@123")} className="text-start hover:text-primary">School A Admin → admin@greenvalley.edu</button>
                <button type="button" data-testid="fill-schoolB" onClick={()=>quick("admin@iqra.edu","School@123")} className="text-start hover:text-primary">School B Admin → admin@iqra.edu</button>
                <button type="button" data-testid="fill-teacher" onClick={()=>quick("teacher@greenvalley.edu","Teacher@123")} className="text-start hover:text-primary">Teacher → teacher@greenvalley.edu</button>
                <button type="button" data-testid="fill-parent" onClick={()=>quick("parent@greenvalley.edu","Parent@123")} className="text-start hover:text-primary">Parent → parent@greenvalley.edu</button>
              </div>
              </>
            )}
          </div>
          <p className="text-sm text-muted-foreground mt-6">
            New school? <Link className="text-primary hover:underline" to="/register">Start your 7-day free trial</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

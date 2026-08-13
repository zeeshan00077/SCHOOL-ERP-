import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { useI18n } from "@/lib/i18n.jsx";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { GraduationCap, ArrowRight } from "lucide-react";
import { toast } from "sonner";

export default function Register() {
  const { t } = useI18n();
  const { registerSchool, apiErr } = useAuth();
  const nav = useNavigate();
  const [form, setForm] = useState({
    school_name: "", admin_name: "", admin_email: "", admin_phone: "",
    password: "", city: "", address: "",
  });
  const [busy, setBusy] = useState(false);
  const on = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault(); setBusy(true);
    try {
      await registerSchool(form);
      toast.success("School created — 7-day free trial started!");
      nav("/app");
    } catch (err) { toast.error(apiErr(err)); }
    finally { setBusy(false); }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <Link to="/" className="flex items-center gap-2">
          <div className="h-9 w-9 rounded-xl bg-primary text-primary-foreground grid place-items-center">
            <GraduationCap className="h-5 w-5"/></div>
          <span className="font-display text-xl font-semibold">Skoolzoom</span>
        </Link>
      </div>
      <div className="max-w-3xl mx-auto px-4 sm:px-6 pb-16">
        <h1 className="font-display text-3xl sm:text-4xl font-bold">Start your 7-day free trial</h1>
        <p className="text-muted-foreground mt-2">Create your school account. No credit card. Cancel anytime.</p>
        <form onSubmit={submit} className="mt-8 grid sm:grid-cols-2 gap-4 rounded-2xl border border-border bg-card p-6 sm:p-8">
          <div className="sm:col-span-2 space-y-2">
            <Label>{t("schoolName")}</Label>
            <Input data-testid="reg-school-name" required value={form.school_name} onChange={on("school_name")} />
          </div>
          <div className="space-y-2">
            <Label>{t("adminName")}</Label>
            <Input data-testid="reg-admin-name" required value={form.admin_name} onChange={on("admin_name")} />
          </div>
          <div className="space-y-2">
            <Label>{t("phone")}</Label>
            <Input data-testid="reg-phone" required value={form.admin_phone} onChange={on("admin_phone")} />
          </div>
          <div className="space-y-2">
            <Label>{t("email")}</Label>
            <Input data-testid="reg-email" type="email" required value={form.admin_email} onChange={on("admin_email")} />
          </div>
          <div className="space-y-2">
            <Label>{t("password")}</Label>
            <Input data-testid="reg-password" type="password" required minLength={6} value={form.password} onChange={on("password")} />
          </div>
          <div className="space-y-2">
            <Label>{t("city")}</Label>
            <Input data-testid="reg-city" value={form.city} onChange={on("city")} />
          </div>
          <div className="space-y-2">
            <Label>{t("address")}</Label>
            <Input data-testid="reg-address" value={form.address} onChange={on("address")} />
          </div>
          <div className="sm:col-span-2 flex items-center justify-between mt-2">
            <Link to="/login" className="text-sm text-muted-foreground hover:text-foreground">Already have an account? Sign in</Link>
            <Button data-testid="reg-submit" type="submit" disabled={busy} className="rounded-full h-11 px-6">
              {busy ? "Creating…" : "Create school & start trial"} <ArrowRight className="ms-2 h-4 w-4 rtl-flip"/>
            </Button>
          </div>
        </form>
        <p className="text-xs text-muted-foreground mt-6" data-testid="developer-branding-register">Developed by Zeeshan Computers Sheikh Fazal · 0343-0819382</p>
      </div>
    </div>
  );
}

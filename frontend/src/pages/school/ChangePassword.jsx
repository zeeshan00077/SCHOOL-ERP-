import { useState } from "react";
import api, { apiErr } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

export default function ChangePassword() {
  const [form, setForm] = useState({ current_password: "", new_password: "" });
  const [busy, setBusy] = useState(false);
  const submit = async (e) => {
    e.preventDefault(); setBusy(true);
    try { await api.post("/auth/change-password", form); toast.success("Password changed"); setForm({current_password:"", new_password:""}); }
    catch (err) { toast.error(apiErr(err)); }
    finally { setBusy(false); }
  };
  return (
    <div className="max-w-md mx-auto space-y-6" data-testid="change-pw-page">
      <h1 className="font-display text-3xl font-bold">Change password</h1>
      <form onSubmit={submit} className="rounded-xl border border-border bg-card p-6 space-y-4">
        <div className="space-y-2"><Label>Current password</Label><Input type="password" required value={form.current_password} onChange={(e)=>setForm({...form,current_password:e.target.value})} data-testid="cp-current"/></div>
        <div className="space-y-2"><Label>New password</Label><Input type="password" required minLength={6} value={form.new_password} onChange={(e)=>setForm({...form,new_password:e.target.value})} data-testid="cp-new"/></div>
        <Button type="submit" disabled={busy} className="w-full" data-testid="cp-submit">{busy ? "Saving…" : "Change password"}</Button>
      </form>
      <p className="text-xs text-muted-foreground">For production use, all seeded/demo accounts should have their passwords rotated here.</p>
    </div>
  );
}

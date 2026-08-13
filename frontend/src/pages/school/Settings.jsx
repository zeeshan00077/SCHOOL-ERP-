import { useEffect, useState } from "react";
import api, { apiErr } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
export default function Settings() {
  const [s, setS] = useState(null);
  useEffect(() => { api.get("/school/me").then(r=>setS(r.data)); }, []);
  const save = async (e) => { e.preventDefault(); try { await api.put("/school/settings", s); toast.success("Saved"); } catch(e){toast.error(apiErr(e));} };
  if (!s) return null;
  return (
    <div className="space-y-6" data-testid="settings-page">
      <h1 className="font-display text-3xl font-bold">School settings</h1>
      <form onSubmit={save} className="grid sm:grid-cols-2 gap-4 rounded-xl border border-border bg-card p-6">
        {["name","phone","email","website","principal","address","academic_session","currency","timezone","logo_url"].map(k => (
          <div key={k} className="space-y-2"><Label className="capitalize">{k.replace("_"," ")}</Label>
            <Input value={s[k] || ""} onChange={(e)=>setS({...s,[k]:e.target.value})} data-testid={`set-${k}`}/></div>
        ))}
        <div className="sm:col-span-2 space-y-2">
          <Label>Bank / payment instructions (printed on fee voucher)</Label>
          <Textarea rows={3} placeholder="e.g. Deposit at MCB Bank, Account #1234-5678, Branch Lahore..." value={s.bank_instructions || ""} onChange={(e)=>setS({...s, bank_instructions: e.target.value})} data-testid="set-bank"/>
        </div>
        <div className="sm:col-span-2"><Button type="submit" data-testid="save-settings">Save</Button></div>
      </form>
      <p className="text-xs text-muted-foreground" data-testid="settings-branding">Developed by Zeeshan Computers Sheikh Fazal · 0343-0819382</p>
    </div>
  );
}

import { useEffect, useState } from "react";
import api, { apiErr } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { ShieldCheck } from "lucide-react";

export default function SystemSettings() {
  const [s, setS] = useState(null);
  useEffect(() => { api.get("/system-settings").then(r => setS(r.data)); }, []);
  const save = async () => { try { await api.put("/system-settings", s); toast.success("System settings saved"); } catch (e) { toast.error(apiErr(e)); } };
  if (!s) return null;
  return (
    <div className="space-y-6" data-testid="sys-settings">
      <div>
        <h1 className="font-display text-3xl font-bold">System settings</h1>
        <p className="text-muted-foreground text-sm mt-1 flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-primary"/> Only editable by Super Admin. School admins cannot see or modify these values.</p>
      </div>
      <div className="rounded-xl border border-border bg-card p-6 grid sm:grid-cols-2 gap-4">
        {[
          ["developer_name","Developer name"],["developer_contact","Developer contact"],["developer_email","Developer email"],
          ["platform_name","Platform name"],["default_currency","Default currency"],["default_trial_days","Default trial days"],
        ].map(([k,l])=>(
          <div key={k} className="space-y-2"><Label>{l}</Label>
            <Input value={s[k] ?? ""} onChange={(e)=>setS({...s,[k]: k==="default_trial_days"?Number(e.target.value):e.target.value})} data-testid={`sys-${k}`}/></div>
        ))}
        <div className="sm:col-span-2 space-y-2"><Label>Footer note</Label>
          <Textarea rows={2} value={s.footer_note || ""} onChange={(e)=>setS({...s, footer_note: e.target.value})}/></div>
        <div className="sm:col-span-2"><Button onClick={save} data-testid="save-sys">Save system settings</Button></div>
      </div>
    </div>
  );
}

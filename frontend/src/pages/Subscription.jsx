import { useEffect, useState } from "react";
import api, { apiErr } from "@/lib/api";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Landmark, Smartphone, ShieldCheck, ArrowLeft } from "lucide-react";
export default function Subscription() {
  const nav = useNavigate();
  const [data, setData] = useState(null);
  const [form, setForm] = useState({ plan_id: "", method: "bank_transfer", amount: 0, reference_number: "", payment_date: new Date().toISOString().slice(0,10), proof_url: "", notes: "" });
  const load = () => api.get("/school/subscription").then(r => { setData(r.data); if (r.data.plans[0]) setForm(f=>({...f, plan_id: r.data.plans[0].id, amount: r.data.plans[0].price})); });
  useEffect(() => { load(); }, []);
  const submit = async (e) => { e.preventDefault(); try { await api.post("/school/payments", { ...form, amount: Number(form.amount) }); toast.success("Payment submitted — awaiting approval"); load(); } catch(e){toast.error(apiErr(e));} };
  if (!data) return null;
  const s = data.school;
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-5xl mx-auto p-4 sm:p-8">
        <Button variant="ghost" onClick={()=>nav("/app")} className="mb-4"><ArrowLeft className="h-4 w-4 me-2 rtl-flip"/>Back to dashboard</Button>
        <div className="rounded-2xl border border-border bg-card p-6 sm:p-8">
          <h1 className="font-display text-3xl font-bold">Subscription</h1>
          <div className="mt-4 flex flex-wrap gap-6 text-sm">
            <div><div className="text-xs text-muted-foreground uppercase">School</div><div className="font-medium">{s.name}</div></div>
            <div><div className="text-xs text-muted-foreground uppercase">Status</div><div className={`font-medium ${s.expired?"text-destructive":"text-primary"}`}>{s.subscription_status_effective}</div></div>
            <div><div className="text-xs text-muted-foreground uppercase">Expires</div><div className="font-medium">{s.subscription_expires_at?.slice(0,10) || "—"}</div></div>
            <div><div className="text-xs text-muted-foreground uppercase">Days remaining</div><div className="font-medium">{s.days_remaining}</div></div>
          </div>
        </div>
        <div className="mt-6 grid lg:grid-cols-2 gap-6">
          <form onSubmit={submit} className="rounded-2xl border border-border bg-card p-6 space-y-4">
            <div className="font-medium">Submit manual payment</div>
            <div className="space-y-2"><Label>Plan</Label>
              <Select value={form.plan_id} onValueChange={(v)=>{ const p = data.plans.find(x=>x.id===v); setForm({...form, plan_id:v, amount: p?.price || 0}); }}>
                <SelectTrigger data-testid="sub-plan"><SelectValue/></SelectTrigger>
                <SelectContent>{data.plans.map(p=><SelectItem key={p.id} value={p.id}>{p.name} — PKR {p.price.toLocaleString()}</SelectItem>)}</SelectContent></Select></div>
            <div className="space-y-2"><Label>Method</Label>
              <Select value={form.method} onValueChange={(v)=>setForm({...form,method:v})}><SelectTrigger><SelectValue/></SelectTrigger>
                <SelectContent><SelectItem value="bank_transfer">Bank Transfer</SelectItem><SelectItem value="jazzcash">JazzCash</SelectItem><SelectItem value="easypaisa">Easypaisa</SelectItem><SelectItem value="other">Other</SelectItem></SelectContent></Select></div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2"><Label>Amount</Label><Input type="number" value={form.amount} onChange={(e)=>setForm({...form,amount:e.target.value})}/></div>
              <div className="space-y-2"><Label>Date</Label><Input type="date" value={form.payment_date} onChange={(e)=>setForm({...form,payment_date:e.target.value})}/></div>
            </div>
            <div className="space-y-2"><Label>Reference / TID</Label><Input required value={form.reference_number} onChange={(e)=>setForm({...form,reference_number:e.target.value})} data-testid="sub-ref"/></div>
            <div className="space-y-2"><Label>Proof URL (optional)</Label><Input value={form.proof_url} onChange={(e)=>setForm({...form,proof_url:e.target.value})}/></div>
            <Button type="submit" className="w-full" data-testid="sub-submit">Submit for approval</Button>
          </form>
          <div className="rounded-2xl border border-border bg-card p-6 space-y-4">
            <div className="font-medium">Payment methods</div>
            <div className="rounded-lg border border-border p-4 flex items-center gap-3"><Landmark className="h-5 w-5 text-primary"/><div><div className="font-medium text-sm">Bank Transfer</div><div className="text-xs text-muted-foreground">Zeeshan Computers · MCB Bank · 1234-5678-9012-3456</div></div></div>
            <div className="rounded-lg border border-border p-4 flex items-center gap-3"><Smartphone className="h-5 w-5 text-primary"/><div><div className="font-medium text-sm">JazzCash / Easypaisa</div><div className="text-xs text-muted-foreground">0343-0819382 (Sheikh Fazal)</div></div></div>
            <div className="rounded-lg border border-border p-4 flex items-center gap-3"><ShieldCheck className="h-5 w-5 text-primary"/><div className="text-xs text-muted-foreground">Your subscription activates automatically after our team approves your payment.</div></div>
            <div className="pt-2">
              <div className="text-xs uppercase text-muted-foreground mb-2">Recent submissions</div>
              <div className="space-y-2">
                {data.payments.map(p => (
                  <div key={p.id} className="flex items-center justify-between text-sm border border-border rounded-md p-2">
                    <div><div className="font-medium">{p.reference_number}</div><div className="text-xs text-muted-foreground">PKR {p.amount.toLocaleString()} · {p.method}</div></div>
                    <span className={`text-xs px-2 py-1 rounded-full ${p.status==="approved"?"bg-primary/10 text-primary":p.status==="pending"?"bg-accent/20":"bg-destructive/10 text-destructive"}`}>{p.status}</span>
                  </div>
                ))}
                {data.payments.length === 0 && <div className="text-xs text-muted-foreground">No payments yet</div>}
              </div>
            </div>
          </div>
        </div>
        <p className="mt-8 text-xs text-muted-foreground text-center" data-testid="sub-branding">Developed by Zeeshan Computers Sheikh Fazal · 0343-0819382</p>
      </div>
    </div>
  );
}

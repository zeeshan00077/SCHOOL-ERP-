import { useEffect, useState } from "react";
import api, { apiErr } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

const empty = { name: "", price: 25000, duration_days: 365, max_students: 500, max_teachers: 100, modules: [], is_active: true };

export default function Plans() {
  const [plans, setPlans] = useState([]);
  const [form, setForm] = useState(empty);
  const load = () => api.get("/super-admin/plans").then(r => setPlans(r.data));
  useEffect(() => { load(); }, []);
  const submit = async (e) => {
    e.preventDefault();
    try {
      await api.post("/super-admin/plans", { ...form, price: Number(form.price), duration_days: Number(form.duration_days), max_students: Number(form.max_students), max_teachers: Number(form.max_teachers) });
      toast.success("Plan created"); setForm(empty); load();
    } catch (e) { toast.error(apiErr(e)); }
  };
  const del = async (id) => { await api.delete(`/super-admin/plans/${id}`); load(); };

  return (
    <div className="space-y-6" data-testid="plans-page">
      <h1 className="font-display text-3xl font-bold">Subscription Plans</h1>
      <div className="grid lg:grid-cols-3 gap-4">
        {plans.map((p) => (
          <div key={p.id} className="rounded-xl border border-border bg-card p-5">
            <div className="flex items-center justify-between">
              <div className="font-medium">{p.name}</div>
              <Button variant="ghost" size="sm" onClick={()=>del(p.id)} data-testid={`del-plan-${p.id}`}>Delete</Button>
            </div>
            <div className="mt-3 font-display text-3xl font-bold">PKR {p.price.toLocaleString()}</div>
            <div className="text-xs text-muted-foreground mt-1">{p.duration_days} days · {p.max_students} students · {p.max_teachers} teachers</div>
          </div>
        ))}
      </div>
      <form onSubmit={submit} className="rounded-xl border border-border bg-card p-6 grid sm:grid-cols-2 gap-4">
        <div className="sm:col-span-2 font-medium">Create a plan</div>
        <div className="space-y-2"><Label>Name</Label><Input required value={form.name} onChange={(e)=>setForm({...form,name:e.target.value})} data-testid="plan-name"/></div>
        <div className="space-y-2"><Label>Price (PKR)</Label><Input type="number" required value={form.price} onChange={(e)=>setForm({...form,price:e.target.value})} data-testid="plan-price"/></div>
        <div className="space-y-2"><Label>Duration (days)</Label><Input type="number" required value={form.duration_days} onChange={(e)=>setForm({...form,duration_days:e.target.value})}/></div>
        <div className="space-y-2"><Label>Max students</Label><Input type="number" value={form.max_students} onChange={(e)=>setForm({...form,max_students:e.target.value})}/></div>
        <div className="space-y-2"><Label>Max teachers</Label><Input type="number" value={form.max_teachers} onChange={(e)=>setForm({...form,max_teachers:e.target.value})}/></div>
        <div className="sm:col-span-2"><Button type="submit" data-testid="plan-submit">Create plan</Button></div>
      </form>
    </div>
  );
}

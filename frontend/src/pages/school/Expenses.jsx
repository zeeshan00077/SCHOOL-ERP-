import { useEffect, useState } from "react";
import api, { apiErr } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Plus, Check, X, Receipt } from "lucide-react";

const empty = { date: new Date().toISOString().slice(0,10), category: "Electricity", description: "", amount: 0, payment_method: "cash", paid_to: "", reference: "", notes: "" };

export default function Expenses() {
  const [items, setItems] = useState([]);
  const [cats, setCats] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(empty);
  const [filter, setFilter] = useState({ status: "", date_from: "", date_to: "" });
  const load = () => api.get("/school/expenses", { params: filter }).then(r => setItems(r.data));
  useEffect(() => { api.get("/school/expense-categories").then(r => setCats(r.data)); load(); /* eslint-disable-next-line */ }, [filter.status, filter.date_from, filter.date_to]);
  const submit = async (e) => { e.preventDefault(); try { await api.post("/school/expenses", { ...form, amount: Number(form.amount) }); toast.success("Expense created"); setOpen(false); setForm(empty); load(); } catch (err) { toast.error(apiErr(err)); } };
  const decide = async (id, action) => { try { await api.post(`/school/expenses/${id}/${action}`, { remarks: action }); toast.success(action); load(); } catch (e) { toast.error(apiErr(e)); } };
  const totals = items.reduce((a,e)=>({ total: a.total + e.amount, approved: a.approved + (e.status==="approved"?e.amount:0), pending: a.pending + (e.status==="pending"?e.amount:0)}), { total: 0, approved: 0, pending: 0 });
  return (
    <div className="space-y-6" data-testid="expenses-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="font-display text-3xl font-bold">Expenses</h1>
        <Dialog open={open} onOpenChange={setOpen}><DialogTrigger asChild><Button data-testid="new-expense"><Plus className="h-4 w-4 me-2"/>New expense</Button></DialogTrigger>
          <DialogContent className="max-w-lg"><DialogHeader><DialogTitle>New expense</DialogTitle></DialogHeader>
            <form onSubmit={submit} className="grid grid-cols-2 gap-3">
              <div className="space-y-2"><Label>Date</Label><Input type="date" value={form.date} onChange={(e)=>setForm({...form,date:e.target.value})}/></div>
              <div className="space-y-2"><Label>Category</Label>
                <Select value={form.category} onValueChange={(v)=>setForm({...form,category:v})}><SelectTrigger data-testid="exp-cat"><SelectValue/></SelectTrigger>
                  <SelectContent>{cats.map(c=><SelectItem key={c} value={c}>{c}</SelectItem>)}</SelectContent></Select></div>
              <div className="col-span-2 space-y-2"><Label>Description</Label><Input required value={form.description} onChange={(e)=>setForm({...form,description:e.target.value})} data-testid="exp-desc"/></div>
              <div className="space-y-2"><Label>Amount</Label><Input type="number" required value={form.amount} onChange={(e)=>setForm({...form,amount:e.target.value})}/></div>
              <div className="space-y-2"><Label>Method</Label>
                <Select value={form.payment_method} onValueChange={(v)=>setForm({...form,payment_method:v})}><SelectTrigger><SelectValue/></SelectTrigger>
                  <SelectContent>{["cash","bank","jazzcash","easypaisa","other"].map(m=><SelectItem key={m} value={m} className="capitalize">{m}</SelectItem>)}</SelectContent></Select></div>
              <div className="space-y-2"><Label>Paid to</Label><Input value={form.paid_to} onChange={(e)=>setForm({...form,paid_to:e.target.value})}/></div>
              <div className="space-y-2"><Label>Reference</Label><Input value={form.reference} onChange={(e)=>setForm({...form,reference:e.target.value})}/></div>
              <div className="col-span-2 space-y-2"><Label>Notes</Label><Textarea rows={2} value={form.notes} onChange={(e)=>setForm({...form,notes:e.target.value})}/></div>
              <div className="col-span-2"><Button type="submit" className="w-full" data-testid="exp-submit">Save expense</Button></div>
            </form></DialogContent></Dialog>
      </div>
      <div className="grid sm:grid-cols-3 gap-4">
        <div className="rounded-xl border border-border bg-card p-4"><div className="text-xs text-muted-foreground uppercase">Total this view</div><div className="font-display text-2xl font-bold mt-1">PKR {totals.total.toLocaleString()}</div></div>
        <div className="rounded-xl border border-border bg-card p-4"><div className="text-xs text-muted-foreground uppercase">Approved</div><div className="font-display text-2xl font-bold text-primary mt-1">PKR {totals.approved.toLocaleString()}</div></div>
        <div className="rounded-xl border border-border bg-card p-4"><div className="text-xs text-muted-foreground uppercase">Pending</div><div className="font-display text-2xl font-bold text-accent-foreground mt-1">PKR {totals.pending.toLocaleString()}</div></div>
      </div>
      <div className="flex gap-3 flex-wrap">
        <Select value={filter.status} onValueChange={(v)=>setFilter({...filter, status: v})}><SelectTrigger className="w-40"><SelectValue placeholder="All statuses"/></SelectTrigger>
          <SelectContent>{["pending","approved","rejected"].map(s=><SelectItem key={s} value={s} className="capitalize">{s}</SelectItem>)}</SelectContent></Select>
        <Input type="date" value={filter.date_from} onChange={(e)=>setFilter({...filter,date_from:e.target.value})} className="w-40"/>
        <Input type="date" value={filter.date_to} onChange={(e)=>setFilter({...filter,date_to:e.target.value})} className="w-40"/>
        <Button variant="ghost" onClick={()=>setFilter({status:"",date_from:"",date_to:""})}>Clear</Button>
      </div>
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-secondary/60 text-xs uppercase text-muted-foreground"><tr><th className="text-start px-4 py-3">Date</th><th className="text-start px-4 py-3">Category</th><th className="text-start px-4 py-3">Description</th><th className="text-start px-4 py-3">Amount</th><th className="text-start px-4 py-3">Status</th><th></th></tr></thead>
          <tbody>{items.map(e=>(
            <tr key={e.id} className="border-t border-border">
              <td className="px-4 py-2">{e.date}</td><td className="px-4 py-2">{e.category}</td>
              <td className="px-4 py-2">{e.description}<div className="text-xs text-muted-foreground">by {e.created_by_name}</div></td>
              <td className="px-4 py-2">PKR {e.amount.toLocaleString()}</td>
              <td className="px-4 py-2"><span className={`text-xs px-2 py-0.5 rounded-full ${e.status==="approved"?"bg-primary/10 text-primary":e.status==="pending"?"bg-accent/20":"bg-destructive/10 text-destructive"}`}>{e.status}</span></td>
              <td className="px-4 py-2 space-x-1">
                {e.status==="pending" && <>
                  <Button size="sm" variant="outline" onClick={()=>decide(e.id,"approve")} data-testid={`app-exp-${e.id}`}><Check className="h-4 w-4"/></Button>
                  <Button size="sm" variant="ghost" onClick={()=>decide(e.id,"reject")}><X className="h-4 w-4"/></Button>
                </>}
              </td>
            </tr>))}
            {items.length===0 && <tr><td colSpan={6} className="text-center text-muted-foreground py-8">No expenses</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

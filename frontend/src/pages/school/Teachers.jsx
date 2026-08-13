import { useEffect, useState } from "react";
import api, { apiErr } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Plus } from "lucide-react";

const empty = { name: "", email: "", phone: "", qualification: "", subject: "", department: "", salary: "", password: "" };

export default function Teachers() {
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(empty);
  const load = () => api.get("/school/teachers").then(r => setItems(r.data));
  useEffect(() => { load(); }, []);
  const submit = async (e) => {
    e.preventDefault();
    try { await api.post("/school/teachers", { ...form, salary: form.salary ? Number(form.salary) : null }); toast.success("Teacher added"); setOpen(false); setForm(empty); load(); }
    catch (err) { toast.error(apiErr(err)); }
  };
  return (
    <div className="space-y-6" data-testid="teachers-page">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-3xl font-bold">Teachers</h1>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild><Button data-testid="add-teacher"><Plus className="h-4 w-4 me-2"/>Add teacher</Button></DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader><DialogTitle>New teacher</DialogTitle></DialogHeader>
            <form onSubmit={submit} className="grid sm:grid-cols-2 gap-3">
              <div className="space-y-2"><Label>Name</Label><Input required value={form.name} onChange={(e)=>setForm({...form,name:e.target.value})} data-testid="t-name"/></div>
              <div className="space-y-2"><Label>Email</Label><Input required type="email" value={form.email} onChange={(e)=>setForm({...form,email:e.target.value})} data-testid="t-email"/></div>
              <div className="space-y-2"><Label>Phone</Label><Input value={form.phone} onChange={(e)=>setForm({...form,phone:e.target.value})}/></div>
              <div className="space-y-2"><Label>Password</Label><Input placeholder="Teacher@123" value={form.password} onChange={(e)=>setForm({...form,password:e.target.value})}/></div>
              <div className="space-y-2"><Label>Qualification</Label><Input value={form.qualification} onChange={(e)=>setForm({...form,qualification:e.target.value})}/></div>
              <div className="space-y-2"><Label>Subject</Label><Input value={form.subject} onChange={(e)=>setForm({...form,subject:e.target.value})}/></div>
              <div className="space-y-2"><Label>Department</Label><Input value={form.department} onChange={(e)=>setForm({...form,department:e.target.value})}/></div>
              <div className="space-y-2"><Label>Salary</Label><Input type="number" value={form.salary} onChange={(e)=>setForm({...form,salary:e.target.value})}/></div>
              <div className="sm:col-span-2"><Button type="submit" className="w-full" data-testid="t-submit">Save teacher</Button></div>
            </form>
          </DialogContent>
        </Dialog>
      </div>
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map(t => (
          <div key={t.id} className="rounded-xl border border-border bg-card p-5">
            <div className="font-medium">{t.name}</div>
            <div className="text-xs text-muted-foreground">{t.email}</div>
            <div className="text-sm mt-3">{t.subject} · {t.qualification}</div>
            <div className="text-xs text-muted-foreground mt-1">{t.employee_id}</div>
          </div>
        ))}
        {items.length === 0 && <div className="text-muted-foreground">No teachers yet</div>}
      </div>
    </div>
  );
}

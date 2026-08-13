import { useEffect, useState } from "react";
import api, { apiErr } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Plus, Trash2 } from "lucide-react";

const empty = { name: "", father_name: "", mother_name: "", dob: "", gender: "male", class_id: "", roll_number: "", phone: "", parent_email: "", parent_name: "" };

export default function Students() {
  const [items, setItems] = useState([]);
  const [classes, setClasses] = useState([]);
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(empty);

  const load = () => api.get("/school/students", { params: q ? { q } : {} }).then(r => setItems(r.data));
  useEffect(() => { load(); api.get("/school/classes").then(r => setClasses(r.data)); /* eslint-disable-next-line */ }, [q]);

  const submit = async (e) => {
    e.preventDefault();
    try { await api.post("/school/students", form); toast.success("Student added"); setOpen(false); setForm(empty); load(); }
    catch (err) { toast.error(apiErr(err)); }
  };
  const del = async (id) => { if (!confirm("Delete this student?")) return; await api.delete(`/school/students/${id}`); load(); };

  return (
    <div className="space-y-6" data-testid="students-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="font-display text-3xl font-bold">Students</h1>
        <div className="flex gap-2">
          <Input placeholder="Search…" value={q} onChange={(e)=>setQ(e.target.value)} className="max-w-xs" data-testid="students-search"/>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild><Button data-testid="add-student-btn"><Plus className="h-4 w-4 me-2"/>Add student</Button></DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader><DialogTitle>New student</DialogTitle></DialogHeader>
              <form onSubmit={submit} className="grid sm:grid-cols-2 gap-3">
                <div className="sm:col-span-2 space-y-2"><Label>Name</Label><Input required value={form.name} onChange={(e)=>setForm({...form,name:e.target.value})} data-testid="stu-name"/></div>
                <div className="space-y-2"><Label>Father's name</Label><Input value={form.father_name} onChange={(e)=>setForm({...form,father_name:e.target.value})}/></div>
                <div className="space-y-2"><Label>Mother's name</Label><Input value={form.mother_name} onChange={(e)=>setForm({...form,mother_name:e.target.value})}/></div>
                <div className="space-y-2"><Label>Class</Label>
                  <Select value={form.class_id} onValueChange={(v)=>setForm({...form,class_id:v})}>
                    <SelectTrigger data-testid="stu-class"><SelectValue placeholder="Choose class"/></SelectTrigger>
                    <SelectContent>{classes.map(c => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}</SelectContent>
                  </Select>
                </div>
                <div className="space-y-2"><Label>Roll number</Label><Input value={form.roll_number} onChange={(e)=>setForm({...form,roll_number:e.target.value})}/></div>
                <div className="space-y-2"><Label>Gender</Label>
                  <Select value={form.gender} onValueChange={(v)=>setForm({...form,gender:v})}>
                    <SelectTrigger><SelectValue/></SelectTrigger>
                    <SelectContent><SelectItem value="male">Male</SelectItem><SelectItem value="female">Female</SelectItem></SelectContent>
                  </Select>
                </div>
                <div className="space-y-2"><Label>DOB</Label><Input type="date" value={form.dob} onChange={(e)=>setForm({...form,dob:e.target.value})}/></div>
                <div className="space-y-2"><Label>Parent email</Label><Input type="email" value={form.parent_email} onChange={(e)=>setForm({...form,parent_email:e.target.value})}/></div>
                <div className="space-y-2"><Label>Parent name</Label><Input value={form.parent_name} onChange={(e)=>setForm({...form,parent_name:e.target.value})}/></div>
                <div className="sm:col-span-2"><Button type="submit" className="w-full" data-testid="stu-submit">Save student</Button></div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-secondary/60 text-xs uppercase text-muted-foreground"><tr>
            <th className="text-start px-4 py-3">Admission #</th><th className="text-start px-4 py-3">Name</th><th className="text-start px-4 py-3">Class</th><th className="text-start px-4 py-3">Roll</th><th className="px-4 py-3"></th>
          </tr></thead>
          <tbody>
            {items.map(s => {
              const cls = classes.find(c => c.id === s.class_id);
              return (
                <tr key={s.id} className="border-t border-border hover:bg-secondary/30">
                  <td className="px-4 py-3">{s.admission_number}</td>
                  <td className="px-4 py-3 font-medium">{s.name}</td>
                  <td className="px-4 py-3">{cls?.name || "—"}</td>
                  <td className="px-4 py-3">{s.roll_number || "—"}</td>
                  <td className="px-4 py-3 text-end"><Button size="sm" variant="ghost" onClick={()=>del(s.id)}><Trash2 className="h-4 w-4"/></Button></td>
                </tr>
              );
            })}
            {items.length === 0 && <tr><td colSpan={5} className="text-center text-muted-foreground py-10">No students yet</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

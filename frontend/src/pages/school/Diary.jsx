import { useEffect, useState } from "react";
import api, { apiErr } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Plus, Trash2, BookOpen } from "lucide-react";

const empty = { class_id: "", section_id: null, subject_id: null, date: new Date().toISOString().slice(0,10), homework: "", classwork: "", notes: "", due_date: "", attachment_url: "" };

export default function Diary() {
  const { user } = useAuth();
  const canPost = user && ["teacher","school_admin"].includes(user.role);
  const [items, setItems] = useState([]);
  const [classes, setClasses] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [filter, setFilter] = useState({ class_id: "", subject_id: "" });
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(empty);

  const load = () => {
    const params = {};
    if (filter.class_id) params.class_id = filter.class_id;
    if (filter.subject_id) params.subject_id = filter.subject_id;
    api.get("/school/diary", { params }).then(r => setItems(r.data));
  };
  useEffect(() => {
    api.get("/school/classes").then(r => setClasses(r.data));
    api.get("/school/subjects").then(r => setSubjects(r.data));
    load(); /* eslint-disable-next-line */
  }, [filter.class_id, filter.subject_id]);

  const submit = async (e) => {
    e.preventDefault();
    try {
      const payload = { ...form };
      if (!payload.subject_id) delete payload.subject_id;
      if (!payload.due_date) delete payload.due_date;
      if (!payload.section_id) delete payload.section_id;
      await api.post("/school/diary", payload);
      toast.success("Diary posted");
      setOpen(false); setForm(empty); load();
    } catch (err) { toast.error(apiErr(err)); }
  };
  const del = async (id) => { if (!confirm("Delete entry?")) return; try { await api.delete(`/school/diary/${id}`); load(); } catch (e) { toast.error(apiErr(e)); } };

  return (
    <div className="space-y-6" data-testid="diary-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-display text-3xl font-bold">Daily Diary</h1>
          <p className="text-muted-foreground text-sm mt-1">Homework, classwork and notes for every class.</p>
        </div>
        {canPost && (
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild><Button data-testid="new-diary"><Plus className="h-4 w-4 me-2"/>New entry</Button></DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader><DialogTitle>Post diary entry</DialogTitle></DialogHeader>
              <form onSubmit={submit} className="grid sm:grid-cols-2 gap-3">
                <div className="space-y-2"><Label>Class</Label>
                  <Select value={form.class_id} onValueChange={(v)=>setForm({...form,class_id:v})}>
                    <SelectTrigger data-testid="diary-class"><SelectValue placeholder="Class"/></SelectTrigger>
                    <SelectContent>{classes.map(c=><SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}</SelectContent>
                  </Select></div>
                <div className="space-y-2"><Label>Subject (optional)</Label>
                  <Select value={form.subject_id || ""} onValueChange={(v)=>setForm({...form,subject_id:v})}>
                    <SelectTrigger><SelectValue placeholder="Any"/></SelectTrigger>
                    <SelectContent>{subjects.map(s=><SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}</SelectContent>
                  </Select></div>
                <div className="space-y-2"><Label>Date</Label><Input type="date" value={form.date} onChange={(e)=>setForm({...form,date:e.target.value})}/></div>
                <div className="space-y-2"><Label>Due date (optional)</Label><Input type="date" value={form.due_date} onChange={(e)=>setForm({...form,due_date:e.target.value})}/></div>
                <div className="sm:col-span-2 space-y-2"><Label>Homework</Label><Textarea rows={2} value={form.homework} onChange={(e)=>setForm({...form,homework:e.target.value})} data-testid="diary-homework"/></div>
                <div className="sm:col-span-2 space-y-2"><Label>Classwork</Label><Textarea rows={2} value={form.classwork} onChange={(e)=>setForm({...form,classwork:e.target.value})}/></div>
                <div className="sm:col-span-2 space-y-2"><Label>Notes</Label><Textarea rows={2} value={form.notes} onChange={(e)=>setForm({...form,notes:e.target.value})}/></div>
                <div className="sm:col-span-2 space-y-2"><Label>Attachment URL (optional)</Label><Input value={form.attachment_url} onChange={(e)=>setForm({...form,attachment_url:e.target.value})}/></div>
                <div className="sm:col-span-2"><Button type="submit" className="w-full" data-testid="diary-submit">Post entry</Button></div>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>
      <div className="flex gap-3 flex-wrap">
        <Select value={filter.class_id} onValueChange={(v)=>setFilter({...filter, class_id: v})}>
          <SelectTrigger className="w-56" data-testid="diary-filter-class"><SelectValue placeholder="All classes"/></SelectTrigger>
          <SelectContent>{classes.map(c=><SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}</SelectContent>
        </Select>
        <Select value={filter.subject_id} onValueChange={(v)=>setFilter({...filter, subject_id: v})}>
          <SelectTrigger className="w-56"><SelectValue placeholder="All subjects"/></SelectTrigger>
          <SelectContent>{subjects.map(s=><SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}</SelectContent>
        </Select>
        {(filter.class_id || filter.subject_id) && <Button variant="ghost" onClick={()=>setFilter({class_id:"",subject_id:""})}>Clear</Button>}
      </div>
      <div className="space-y-3">
        {items.map(d => {
          const cls = classes.find(c => c.id === d.class_id);
          const sub = subjects.find(s => s.id === d.subject_id);
          return (
            <div key={d.id} className="rounded-xl border border-border bg-card p-5">
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground mb-2">
                    <span className="inline-flex items-center gap-1"><BookOpen className="h-3 w-3"/> {cls?.name || "—"}</span>
                    {sub && <span className="px-2 py-0.5 rounded-full bg-secondary">{sub.name}</span>}
                    <span>· {d.date}</span>
                    {d.due_date && <span className="text-accent-foreground bg-accent/20 px-2 py-0.5 rounded-full">Due {d.due_date}</span>}
                    <span className="ms-auto">by {d.author_name}</span>
                  </div>
                  {d.homework && <div className="text-sm"><span className="font-medium">Homework:</span> {d.homework}</div>}
                  {d.classwork && <div className="text-sm mt-1"><span className="font-medium">Classwork:</span> {d.classwork}</div>}
                  {d.notes && <div className="text-sm mt-1 text-muted-foreground">{d.notes}</div>}
                  {d.attachment_url && <a href={d.attachment_url} target="_blank" rel="noreferrer" className="inline-block mt-2 text-primary text-sm underline">View attachment</a>}
                </div>
                {canPost && (d.author_id === user.id || user.role === "school_admin") && (
                  <Button variant="ghost" size="sm" onClick={()=>del(d.id)}><Trash2 className="h-4 w-4"/></Button>
                )}
              </div>
            </div>
          );
        })}
        {items.length === 0 && <div className="rounded-xl border border-border bg-card p-10 text-center text-muted-foreground">No diary entries yet</div>}
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import api, { apiErr, BACKEND_URL } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Plus, Trash2, IdCard, Search, User, Camera, Download, Printer } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

const empty = {
  name: "", father_name: "", mother_name: "", dob: "", gender: "male",
  class_id: "", section_id: null, roll_number: "", phone: "", address: "",
  cnic_bform: "", admission_date: new Date().toISOString().slice(0,10),
  academic_session: "", previous_school: "", emergency_contact: "",
  photo_url: "", parent_email: "", parent_name: "", parent_phone: "",
};

function PhotoInput({ value, onChange, testId }) {
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState(value || "");
  useEffect(() => { setPreview(value || ""); }, [value]);
  const pick = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    if (f.size > 3 * 1024 * 1024) { toast.error("Photo max 3 MB"); return; }
    if (!/^image\/(jpeg|png|webp)$/.test(f.type)) { toast.error("JPG / PNG / WEBP only"); return; }
    setBusy(true);
    try {
      const fd = new FormData(); fd.append("file", f);
      const { data } = await api.post("/school/uploads/photo", fd, { headers: { "Content-Type": "multipart/form-data" } });
      onChange(data.url);
      setPreview(URL.createObjectURL(f));
      toast.success("Photo uploaded");
    } catch (err) { toast.error(apiErr(err)); }
    finally { setBusy(false); }
  };
  const url = preview.startsWith("blob:") ? preview : (preview ? `${BACKEND_URL}${preview}` : "");
  return (
    <div className="flex items-center gap-3">
      <div className="h-20 w-20 rounded-lg border border-border overflow-hidden bg-secondary grid place-items-center">
        {url ? <img src={url} alt="" className="h-20 w-20 object-cover"/> : <Camera className="h-6 w-6 text-muted-foreground"/>}
      </div>
      <label className="cursor-pointer">
        <input type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={pick} data-testid={testId}/>
        <span className="text-sm underline text-primary">{busy ? "Uploading…" : "Upload photo"}</span>
      </label>
    </div>
  );
}

export default function Students() {
  const { user } = useAuth();
  const nav = useNavigate();
  const [items, setItems] = useState([]);
  const [classes, setClasses] = useState([]);
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(empty);
  const [selected, setSelected] = useState({});
  const [bulkClass, setBulkClass] = useState("");
  const canEdit = user && ["school_admin","receptionist"].includes(user.role);

  const load = () => api.get("/school/students", { params: q ? { q } : {} }).then(r => setItems(r.data));
  useEffect(() => { load(); api.get("/school/classes").then(r => setClasses(r.data)); /* eslint-disable-next-line */ }, [q]);

  const submit = async (e) => {
    e.preventDefault();
    if (!form.photo_url) { toast.warning("Photo is recommended for admission — you can add it later."); }
    try { await api.post("/school/students", form); toast.success("Student admitted"); setOpen(false); setForm(empty); load(); }
    catch (err) { toast.error(apiErr(err)); }
  };
  const del = async (id) => { if (!confirm("Delete this student?")) return; await api.delete(`/school/students/${id}`); load(); };

  const toggle = (id) => setSelected({...selected, [id]: !selected[id]});
  const selectedIds = Object.entries(selected).filter(([,v])=>v).map(([k])=>k);
  const generateCards = async ({ ids, classId }) => {
    try {
      const { data } = await api.post("/school/id-cards/pdf", ids ? { student_ids: ids } : { class_id: classId }, { responseType: "blob" });
      const blob = new Blob([data], { type: "application/pdf" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = `id-cards-${(ids?.length || 'class')}.pdf`; a.click();
      URL.revokeObjectURL(url);
      toast.success(`PDF downloaded (${ids?.length || 'class'} cards)`);
    } catch (err) { toast.error(apiErr(err)); }
  };

  return (
    <div className="space-y-6" data-testid="students-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="font-display text-3xl font-bold">Students</h1>
        <div className="flex flex-wrap gap-2 items-center">
          <div className="relative">
            <Search className="h-4 w-4 absolute start-3 top-1/2 -translate-y-1/2 text-muted-foreground"/>
            <Input placeholder="Search name, ID, adm #, father, roll…" value={q} onChange={(e)=>setQ(e.target.value)} className="ps-9 w-80" data-testid="students-search"/>
          </div>
          {selectedIds.length > 0 && canEdit && (
            <Button variant="outline" onClick={()=>generateCards({ ids: selectedIds })} data-testid="bulk-cards-btn"><IdCard className="h-4 w-4 me-2"/>ID Cards PDF ({selectedIds.length})</Button>
          )}
          <div className="flex items-center gap-1">
            <Select value={bulkClass} onValueChange={setBulkClass}>
              <SelectTrigger className="w-40" data-testid="bulk-class-select"><SelectValue placeholder="Whole class"/></SelectTrigger>
              <SelectContent>{classes.map(c=><SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}</SelectContent>
            </Select>
            <Button variant="outline" disabled={!bulkClass} onClick={()=>generateCards({ classId: bulkClass })} data-testid="class-cards-btn"><Download className="h-4 w-4 me-2"/>Class PDF</Button>
          </div>
          {canEdit && (
            <Dialog open={open} onOpenChange={setOpen}>
              <DialogTrigger asChild><Button data-testid="add-student-btn"><Plus className="h-4 w-4 me-2"/>Admit student</Button></DialogTrigger>
              <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader><DialogTitle>New admission</DialogTitle></DialogHeader>
                <form onSubmit={submit} className="grid sm:grid-cols-2 gap-3">
                  <div className="sm:col-span-2"><Label className="mb-2 block">Photo</Label><PhotoInput value={form.photo_url} onChange={(url)=>setForm({...form, photo_url: url})} testId="stu-photo"/></div>
                  <div className="sm:col-span-2 space-y-2"><Label>Student name *</Label><Input required value={form.name} onChange={(e)=>setForm({...form,name:e.target.value})} data-testid="stu-name"/></div>
                  <div className="space-y-2"><Label>Father's name</Label><Input value={form.father_name} onChange={(e)=>setForm({...form,father_name:e.target.value})}/></div>
                  <div className="space-y-2"><Label>Mother's name</Label><Input value={form.mother_name} onChange={(e)=>setForm({...form,mother_name:e.target.value})}/></div>
                  <div className="space-y-2"><Label>Class *</Label>
                    <Select value={form.class_id} onValueChange={(v)=>setForm({...form,class_id:v})}>
                      <SelectTrigger data-testid="stu-class"><SelectValue placeholder="Choose"/></SelectTrigger>
                      <SelectContent>{classes.map(c=><SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}</SelectContent>
                    </Select></div>
                  <div className="space-y-2"><Label>Roll number</Label><Input value={form.roll_number} onChange={(e)=>setForm({...form,roll_number:e.target.value})}/></div>
                  <div className="space-y-2"><Label>Gender</Label>
                    <Select value={form.gender} onValueChange={(v)=>setForm({...form,gender:v})}><SelectTrigger><SelectValue/></SelectTrigger>
                      <SelectContent><SelectItem value="male">Male</SelectItem><SelectItem value="female">Female</SelectItem></SelectContent></Select></div>
                  <div className="space-y-2"><Label>DOB</Label><Input type="date" value={form.dob} onChange={(e)=>setForm({...form,dob:e.target.value})}/></div>
                  <div className="space-y-2"><Label>B-Form / CNIC</Label><Input value={form.cnic_bform} onChange={(e)=>setForm({...form,cnic_bform:e.target.value})}/></div>
                  <div className="space-y-2"><Label>Admission date</Label><Input type="date" value={form.admission_date} onChange={(e)=>setForm({...form,admission_date:e.target.value})}/></div>
                  <div className="space-y-2"><Label>Academic session</Label><Input placeholder="2025-2026" value={form.academic_session} onChange={(e)=>setForm({...form,academic_session:e.target.value})}/></div>
                  <div className="space-y-2"><Label>Previous school</Label><Input value={form.previous_school} onChange={(e)=>setForm({...form,previous_school:e.target.value})}/></div>
                  <div className="space-y-2"><Label>Phone</Label><Input value={form.phone} onChange={(e)=>setForm({...form,phone:e.target.value})}/></div>
                  <div className="sm:col-span-2 space-y-2"><Label>Address</Label><Textarea rows={2} value={form.address} onChange={(e)=>setForm({...form,address:e.target.value})}/></div>
                  <div className="space-y-2"><Label>Emergency contact</Label><Input value={form.emergency_contact} onChange={(e)=>setForm({...form,emergency_contact:e.target.value})}/></div>
                  <div className="space-y-2"><Label>Parent email</Label><Input type="email" value={form.parent_email} onChange={(e)=>setForm({...form,parent_email:e.target.value})}/></div>
                  <div className="space-y-2"><Label>Parent name</Label><Input value={form.parent_name} onChange={(e)=>setForm({...form,parent_name:e.target.value})}/></div>
                  <div className="space-y-2"><Label>Parent phone</Label><Input value={form.parent_phone} onChange={(e)=>setForm({...form,parent_phone:e.target.value})}/></div>
                  <div className="sm:col-span-2"><Button type="submit" className="w-full" data-testid="stu-submit">Save admission</Button></div>
                </form>
              </DialogContent>
            </Dialog>
          )}
        </div>
      </div>
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-secondary/60 text-xs uppercase text-muted-foreground"><tr>
            <th className="w-10 p-3"></th>
            <th className="text-start px-4 py-3">Photo</th>
            <th className="text-start px-4 py-3">Student ID</th>
            <th className="text-start px-4 py-3">Name</th>
            <th className="text-start px-4 py-3">Adm #</th>
            <th className="text-start px-4 py-3">Class</th>
            <th className="text-start px-4 py-3">Roll</th>
            <th className="px-4 py-3"></th>
          </tr></thead>
          <tbody>
            {items.map(s => {
              const cls = classes.find(c => c.id === s.class_id);
              const photoSrc = s.photo_url ? `${BACKEND_URL}${s.photo_url}` : null;
              return (
                <tr key={s.id} className="border-t border-border hover:bg-secondary/30">
                  <td className="p-3"><input type="checkbox" checked={!!selected[s.id]} onChange={()=>toggle(s.id)} data-testid={`stu-check-${s.id}`}/></td>
                  <td className="px-4 py-2">
                    {photoSrc ? <img src={photoSrc} alt="" className="h-9 w-9 rounded-full object-cover border border-border"/> :
                      <div className="h-9 w-9 rounded-full bg-secondary grid place-items-center text-muted-foreground"><User className="h-4 w-4"/></div>}
                  </td>
                  <td className="px-4 py-2 font-mono text-xs">{s.student_id || "—"}</td>
                  <td className="px-4 py-2 font-medium">{s.name}</td>
                  <td className="px-4 py-2 text-xs">{s.admission_number}</td>
                  <td className="px-4 py-2">{cls?.name || "—"}</td>
                  <td className="px-4 py-2">{s.roll_number || "—"}</td>
                  <td className="px-4 py-2 text-end whitespace-nowrap">
                    <Button size="sm" variant="ghost" onClick={()=>nav(`/app/students/${s.id}`)} data-testid={`view-${s.id}`}>Open</Button>
                    <Button size="sm" variant="ghost" onClick={()=>window.open(`/print/id-card/${s.id}`,"_blank")} title="ID card"><IdCard className="h-4 w-4"/></Button>
                    {canEdit && <Button size="sm" variant="ghost" onClick={()=>del(s.id)}><Trash2 className="h-4 w-4"/></Button>}
                  </td>
                </tr>
              );
            })}
            {items.length === 0 && <tr><td colSpan={8} className="text-center text-muted-foreground py-10">No students yet</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

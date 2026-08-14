import { useEffect, useState } from "react";
import api, { apiErr } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Phone, Check, ArrowRight } from "lucide-react";

export default function Admissions() {
  const [items, setItems] = useState([]);
  const [status, setStatus] = useState("");
  const [classes, setClasses] = useState([]);
  const [convertRow, setConvertRow] = useState(null);
  const [form, setForm] = useState({ class_id: "", section_id: null, roll_number: "" });
  const load = () => api.get("/school/admission-enquiries", { params: status ? { status } : {} }).then(r => setItems(r.data));
  useEffect(() => { api.get("/school/classes").then(r => setClasses(r.data)); load(); /* eslint-disable-next-line */ }, [status]);
  const setEnq = async (id, s) => { try { await api.put(`/school/admission-enquiries/${id}`, { status: s }); load(); } catch (e) { toast.error(apiErr(e)); } };
  const convert = async () => {
    try {
      const { data } = await api.post(`/school/admission-enquiries/${convertRow.id}/convert`, form);
      toast.success(`Converted → ${data.student_id}`);
      setConvertRow(null); setForm({ class_id: "", section_id: null, roll_number: "" }); load();
    } catch (e) { toast.error(apiErr(e)); }
  };
  return (
    <div className="space-y-6" data-testid="admissions-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="font-display text-3xl font-bold">Admission enquiries</h1>
        <div className="flex items-center gap-2">
          <Select value={status} onValueChange={setStatus}><SelectTrigger className="w-40"><SelectValue placeholder="All statuses"/></SelectTrigger>
            <SelectContent>{["new","contacted","follow_up","approved","rejected","converted"].map(s=><SelectItem key={s} value={s} className="capitalize">{s.replace("_"," ")}</SelectItem>)}</SelectContent></Select>
          {status && <Button variant="ghost" onClick={()=>setStatus("")}>Clear</Button>}
        </div>
      </div>
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-secondary/60 text-xs uppercase text-muted-foreground"><tr><th className="text-start px-4 py-3">Enquiry #</th><th className="text-start px-4 py-3">Student</th><th className="text-start px-4 py-3">Class</th><th className="text-start px-4 py-3">Contact</th><th className="text-start px-4 py-3">Status</th><th></th></tr></thead>
          <tbody>{items.map(e=>(
            <tr key={e.id} className="border-t border-border">
              <td className="px-4 py-2 font-mono text-xs">{e.enquiry_number}</td>
              <td className="px-4 py-2"><div className="font-medium">{e.student_name}</div><div className="text-xs text-muted-foreground">Father: {e.father_name || "—"}</div></td>
              <td className="px-4 py-2">{e.desired_class || "—"}</td>
              <td className="px-4 py-2 text-xs"><div className="flex items-center gap-1"><Phone className="h-3 w-3"/>{e.phone}</div>{e.email && <div>{e.email}</div>}</td>
              <td className="px-4 py-2"><span className="text-xs px-2 py-0.5 rounded-full bg-secondary capitalize">{e.status.replace("_"," ")}</span></td>
              <td className="px-4 py-2 space-x-1">
                {e.status !== "converted" && <>
                  <Button size="sm" variant="ghost" onClick={()=>setEnq(e.id,"contacted")} data-testid={`contact-${e.id}`}>Contact</Button>
                  <Button size="sm" variant="outline" onClick={()=>setEnq(e.id,"approved")}><Check className="h-4 w-4 me-1"/>Approve</Button>
                  <Button size="sm" onClick={()=>setConvertRow(e)} data-testid={`convert-${e.id}`}><ArrowRight className="h-4 w-4 me-1 rtl-flip"/>Convert</Button>
                </>}
              </td>
            </tr>
          ))}{items.length===0 && <tr><td colSpan={6} className="text-center text-muted-foreground py-8">No enquiries yet</td></tr>}</tbody>
        </table>
      </div>

      <Dialog open={!!convertRow} onOpenChange={(o)=>!o && setConvertRow(null)}>
        <DialogContent><DialogHeader><DialogTitle>Convert to student</DialogTitle></DialogHeader>
        {convertRow && <div className="space-y-3">
          <div className="text-sm">{convertRow.student_name} · {convertRow.phone}</div>
          <div className="space-y-2"><Label>Class</Label>
            <Select value={form.class_id} onValueChange={(v)=>setForm({...form, class_id: v})}><SelectTrigger data-testid="conv-class"><SelectValue placeholder="Choose"/></SelectTrigger>
              <SelectContent>{classes.map(c=><SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}</SelectContent></Select></div>
          <div className="space-y-2"><Label>Roll number</Label><Input value={form.roll_number} onChange={(e)=>setForm({...form, roll_number: e.target.value})}/></div>
          <Button onClick={convert} disabled={!form.class_id} className="w-full" data-testid="conv-submit">Create student</Button>
        </div>}</DialogContent>
      </Dialog>
    </div>
  );
}

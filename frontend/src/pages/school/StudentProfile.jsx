import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api, { apiErr, BACKEND_URL } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { ArrowLeft, User, IdCard, Download, Camera, Save } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function StudentProfile() {
  const { id } = useParams();
  const nav = useNavigate();
  const { user } = useAuth();
  const [s, setS] = useState(null);
  const canEdit = user && ["school_admin","receptionist"].includes(user.role);

  useEffect(() => { api.get(`/school/students/${id}`).then(r => setS(r.data)).catch(e => { toast.error(apiErr(e)); nav("/app/students"); }); }, [id, nav]);

  const changePhoto = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    if (f.size > 3*1024*1024) { toast.error("Photo max 3 MB"); return; }
    try {
      const fd = new FormData(); fd.append("file", f);
      const { data } = await api.post("/school/uploads/photo", fd, { headers: { "Content-Type": "multipart/form-data" } });
      await api.put(`/school/students/${id}/photo`, { photo_url: data.url });
      setS({ ...s, photo_url: data.url });
      toast.success("Photo updated");
    } catch (err) { toast.error(apiErr(err)); }
  };
  const save = async () => {
    try { await api.put(`/school/students/${id}`, s); toast.success("Saved"); }
    catch (err) { toast.error(apiErr(err)); }
  };
  const downloadCard = async () => {
    try {
      const { data } = await api.post("/school/id-cards/pdf", { student_ids: [id] }, { responseType: "blob" });
      const url = URL.createObjectURL(new Blob([data], { type: "application/pdf" }));
      const a = document.createElement("a"); a.href = url; a.download = `id-card-${s.student_id || s.name}.pdf`; a.click();
    } catch (err) { toast.error(apiErr(err)); }
  };
  if (!s) return null;
  const photoSrc = s.photo_url ? `${BACKEND_URL}${s.photo_url}` : null;
  return (
    <div className="space-y-6" data-testid="student-profile">
      <Button variant="ghost" onClick={()=>nav("/app/students")}><ArrowLeft className="h-4 w-4 me-2 rtl-flip"/>All students</Button>
      <div className="rounded-2xl border border-border bg-card p-6 grid md:grid-cols-3 gap-6">
        <div className="flex flex-col items-center gap-3">
          <div className="h-40 w-40 rounded-2xl overflow-hidden bg-secondary border border-border grid place-items-center">
            {photoSrc ? <img src={photoSrc} alt="" className="h-40 w-40 object-cover"/> : <User className="h-14 w-14 text-muted-foreground"/>}
          </div>
          {canEdit && (
            <label className="cursor-pointer text-sm text-primary underline">
              <input type="file" accept="image/*" className="hidden" onChange={changePhoto} data-testid="prof-photo"/>
              <span className="inline-flex items-center gap-1"><Camera className="h-4 w-4"/>Change photo</span>
            </label>
          )}
        </div>
        <div className="md:col-span-2 space-y-1">
          <h1 className="font-display text-3xl font-bold">{s.name}</h1>
          <div className="text-sm text-muted-foreground">Student ID: <span className="font-mono text-foreground">{s.student_id || "—"}</span></div>
          <div className="text-sm text-muted-foreground">Admission #: <span className="font-mono text-foreground">{s.admission_number}</span></div>
          <div className="text-sm text-muted-foreground">Status: {s.status || "active"}</div>
          <div className="flex flex-wrap gap-2 mt-4">
            <Button variant="outline" onClick={()=>window.open(`/print/id-card/${id}`, "_blank")} data-testid="open-card"><IdCard className="h-4 w-4 me-2"/>View ID card</Button>
            <Button onClick={downloadCard} data-testid="dl-card"><Download className="h-4 w-4 me-2"/>Download ID card PDF</Button>
          </div>
        </div>
      </div>
      <div className="rounded-xl border border-border bg-card p-6 grid sm:grid-cols-2 gap-3" data-testid="prof-fields">
        {[
          ["name","Name"],["father_name","Father's name"],["mother_name","Mother's name"],
          ["gender","Gender"],["dob","Date of birth"],["cnic_bform","B-Form / CNIC"],
          ["roll_number","Roll number"],["admission_date","Admission date"],
          ["academic_session","Academic session"],["previous_school","Previous school"],
          ["phone","Phone"],["emergency_contact","Emergency contact"],
        ].map(([k, lbl]) => (
          <div key={k} className="space-y-2"><Label>{lbl}</Label>
            <Input value={s[k] || ""} disabled={!canEdit} onChange={(e)=>setS({...s,[k]:e.target.value})}/></div>
        ))}
        <div className="sm:col-span-2 space-y-2"><Label>Address</Label>
          <Textarea rows={2} value={s.address || ""} disabled={!canEdit} onChange={(e)=>setS({...s, address: e.target.value})}/></div>
        {canEdit && <div className="sm:col-span-2"><Button onClick={save} data-testid="prof-save"><Save className="h-4 w-4 me-2"/>Save changes</Button></div>}
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api, { apiErr, BACKEND_URL } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Printer, Download, GraduationCap } from "lucide-react";
import { toast } from "sonner";

export default function IdCardPreview() {
  const { studentId } = useParams();
  const [d, setD] = useState(null);
  useEffect(() => { api.get(`/school/id-cards/${studentId}`).then(r => setD(r.data)).catch(e => toast.error(apiErr(e))); }, [studentId]);
  if (!d) return <div className="p-10 text-center text-muted-foreground">Loading…</div>;
  const s = d.student, sch = d.school;
  const photo = s.photo_url ? `${BACKEND_URL}${s.photo_url}` : null;

  const dlPdf = async () => {
    try {
      const { data } = await api.post("/school/id-cards/pdf", { student_ids: [studentId] }, { responseType: "blob" });
      const url = URL.createObjectURL(new Blob([data], { type: "application/pdf" }));
      const a = document.createElement("a"); a.href = url; a.download = `id-card-${s.student_id}.pdf`; a.click();
    } catch (e) { toast.error(apiErr(e)); }
  };

  return (
    <div className="min-h-screen bg-slate-100 py-8 text-slate-900">
      <div className="max-w-3xl mx-auto px-4 print:max-w-full print:px-0">
        <div className="flex items-center justify-between mb-4 print:hidden">
          <div className="text-slate-600 text-sm">ID Card — {s.name} ({s.student_id})</div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={()=>window.print()} data-testid="print-idcard"><Printer className="h-4 w-4 me-2"/>Print</Button>
            <Button onClick={dlPdf} data-testid="dl-idcard"><Download className="h-4 w-4 me-2"/>Download PDF</Button>
          </div>
        </div>

        <div className="grid sm:grid-cols-2 gap-6 print:grid-cols-2">
          {/* FRONT */}
          <div className="rounded-lg overflow-hidden border-2 border-emerald-700 bg-white text-[11px]" style={{width: "336px", height: "212px"}}>
            <div className="bg-emerald-700 text-white text-center py-1.5 px-2">
              <div className="flex items-center justify-center gap-2">
                {sch.logo_url ? <img src={sch.logo_url} className="h-6 w-6 object-contain" alt=""/> : <GraduationCap className="h-5 w-5"/>}
                <div>
                  <div className="font-bold text-[12px] leading-tight">{sch.name}</div>
                  <div className="text-[8px] uppercase tracking-widest">Student ID Card · {sch.academic_session || "—"}</div>
                </div>
              </div>
            </div>
            <div className="flex gap-2 p-2">
              <div className="w-[80px] h-[100px] border border-slate-300 rounded overflow-hidden bg-slate-100 grid place-items-center">
                {photo ? <img src={photo} className="w-full h-full object-cover" alt=""/> : <span className="text-[9px] text-slate-500">Photo</span>}
              </div>
              <table className="text-[10px] flex-1"><tbody>
                <tr><td className="text-slate-500 pe-1">Name:</td><td className="font-semibold">{s.name}</td></tr>
                <tr><td className="text-slate-500 pe-1">Student ID:</td><td className="font-mono font-semibold">{s.student_id}</td></tr>
                <tr><td className="text-slate-500 pe-1">Adm #:</td><td>{s.admission_number}</td></tr>
                <tr><td className="text-slate-500 pe-1">Class:</td><td>{s.class_name} {s.section_name}</td></tr>
                <tr><td className="text-slate-500 pe-1">Roll #:</td><td>{s.roll_number || "—"}</td></tr>
                <tr><td className="text-slate-500 pe-1">Father:</td><td>{s.father_name || "—"}</td></tr>
              </tbody></table>
            </div>
            <div className="border-t border-slate-200 text-center py-1 text-[9px] bg-slate-50">{sch.phone} · {sch.email}</div>
          </div>
          {/* BACK */}
          <div className="rounded-lg overflow-hidden border-2 border-emerald-700 bg-white text-[10px] p-3" style={{width: "336px", height: "212px"}}>
            <div className="font-bold text-[12px]">{sch.name}</div>
            <div className="text-[9px] text-slate-600 mb-2">{sch.address}</div>
            <div className="text-[9px] font-medium uppercase text-slate-500 mb-1">Contact</div>
            <div>Phone: {sch.phone}</div>
            <div className="mb-2">Email: {sch.email}</div>
            <div className="text-[9px] whitespace-pre-wrap text-slate-700 leading-snug">
              {sch.id_card_back_text || "If found, please return to the above school address."}
            </div>
            <div className="text-[8px] text-slate-400 mt-2 text-center absolute bottom-2">Developed by Zeeshan Computers Sheikh Fazal · 0343-0819382</div>
          </div>
        </div>
      </div>
    </div>
  );
}

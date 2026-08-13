import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api from "@/lib/api";
import { GraduationCap, Printer } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function ResultCard() {
  const { examId, studentId } = useParams();
  const [d, setD] = useState(null);
  useEffect(() => { api.get(`/school/results/${examId}/students/${studentId}/card`).then(r => setD(r.data)); }, [examId, studentId]);
  if (!d) return <div className="p-10 text-center text-muted-foreground">Loading result card…</div>;
  const t = d.totals;
  return (
    <div className="min-h-screen bg-slate-100 py-8 text-slate-900">
      <div className="max-w-3xl mx-auto px-4 print:max-w-full print:px-0">
        <div className="flex items-center justify-between mb-4 print:hidden">
          <div className="text-slate-600 text-sm">Result card for {d.student.name} — {d.exam.name}</div>
          <Button onClick={()=>window.print()} data-testid="print-card"><Printer className="h-4 w-4 me-2"/>Print</Button>
        </div>
        <div className="bg-white border-2 border-emerald-700 rounded-md p-6 shadow-sm print:shadow-none">
          <div className="flex items-start justify-between pb-4 border-b-2 border-emerald-700">
            <div className="flex items-center gap-3">
              {d.school.logo_url ? <img src={d.school.logo_url} alt="" className="h-16 w-16 object-contain"/> :
                <div className="h-16 w-16 rounded-lg bg-emerald-700 text-white grid place-items-center"><GraduationCap className="h-8 w-8"/></div>}
              <div>
                <div className="font-bold text-xl">{d.school.name}</div>
                <div className="text-xs">{d.school.address}</div>
                <div className="text-xs">{d.school.phone} · {d.school.email}</div>
              </div>
            </div>
            <div className="text-end">
              <div className="uppercase text-xs tracking-widest text-slate-500">Result Card</div>
              <div className="font-bold">{d.exam.name}</div>
              <div className="text-xs">Session {d.school.academic_session || "—"}</div>
              <div className="text-xs">Issued: {d.issued_on}</div>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4 mt-4 items-center">
            <div className="col-span-2 grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
              <div><span className="text-slate-500">Name:</span> <span className="font-semibold">{d.student.name}</span></div>
              <div><span className="text-slate-500">Adm #:</span> {d.student.admission_number}</div>
              <div><span className="text-slate-500">Father:</span> {d.student.father_name || "—"}</div>
              <div><span className="text-slate-500">Roll #:</span> {d.student.roll_number || "—"}</div>
              <div><span className="text-slate-500">Class:</span> {d.student.class_name}</div>
              <div><span className="text-slate-500">Section:</span> {d.student.section_name || "—"}</div>
              <div><span className="text-slate-500">Exam dates:</span> {d.exam.start_date} – {d.exam.end_date}</div>
              <div><span className="text-slate-500">Position:</span> <span className="font-bold">{t.position ? `${t.position}` : "—"}</span></div>
            </div>
            <div className="justify-self-end">
              {d.student.photo_url ? <img src={d.student.photo_url} alt="" className="h-24 w-24 object-cover rounded border border-slate-300"/> :
                <div className="h-24 w-24 rounded border-2 border-dashed border-slate-300 grid place-items-center text-slate-400 text-xs">Photo</div>}
            </div>
          </div>

          <table className="w-full text-sm mt-4 border-collapse">
            <thead className="bg-emerald-50">
              <tr>
                <th className="text-start p-2 border border-slate-200">Subject</th>
                <th className="text-end p-2 border border-slate-200">Total</th>
                <th className="text-end p-2 border border-slate-200">Obtained</th>
                <th className="text-end p-2 border border-slate-200">%</th>
                <th className="text-end p-2 border border-slate-200">Result</th>
              </tr>
            </thead>
            <tbody>
              {d.subjects.map((s, i) => (
                <tr key={i}>
                  <td className="p-2 border border-slate-200">{s.name}</td>
                  <td className="p-2 border border-slate-200 text-end">{s.total}</td>
                  <td className="p-2 border border-slate-200 text-end">{s.marks}</td>
                  <td className="p-2 border border-slate-200 text-end">{s.total ? ((s.marks/s.total)*100).toFixed(1) : 0}%</td>
                  <td className={`p-2 border border-slate-200 text-end font-medium ${s.passed ? "text-emerald-700" : "text-red-600"}`}>{s.passed ? "Pass" : "Fail"}</td>
                </tr>
              ))}
              {d.subjects.length === 0 && <tr><td colSpan={5} className="p-4 text-center text-slate-500">No marks entered</td></tr>}
              <tr className="bg-emerald-50 font-bold">
                <td className="p-2 border border-slate-200">Total</td>
                <td className="p-2 border border-slate-200 text-end">{t.total}</td>
                <td className="p-2 border border-slate-200 text-end">{t.obtained}</td>
                <td className="p-2 border border-slate-200 text-end">{t.percentage}%</td>
                <td className={`p-2 border border-slate-200 text-end ${t.passed ? "text-emerald-700" : "text-red-600"}`}>{t.passed ? `Passed · Grade ${t.grade}` : `Failed · Grade ${t.grade}`}</td>
              </tr>
            </tbody>
          </table>

          <div className="grid grid-cols-4 gap-3 mt-4 text-xs">
            <div className="border border-slate-200 rounded p-2 text-center"><div className="text-slate-500">Present</div><div className="font-bold text-lg">{d.attendance.present || 0}</div></div>
            <div className="border border-slate-200 rounded p-2 text-center"><div className="text-slate-500">Absent</div><div className="font-bold text-lg">{d.attendance.absent || 0}</div></div>
            <div className="border border-slate-200 rounded p-2 text-center"><div className="text-slate-500">Late</div><div className="font-bold text-lg">{d.attendance.late || 0}</div></div>
            <div className="border border-slate-200 rounded p-2 text-center"><div className="text-slate-500">Leave</div><div className="font-bold text-lg">{d.attendance.leave || 0}</div></div>
          </div>

          <div className="grid grid-cols-2 gap-6 mt-8 text-xs">
            <div>
              <div className="text-slate-500 uppercase">Class teacher's remarks</div>
              <div className="border-b border-slate-300 mt-6"></div>
            </div>
            <div>
              <div className="text-slate-500 uppercase">Principal's signature</div>
              <div className="border-b border-slate-300 mt-6"></div>
              <div className="mt-1 font-medium">{d.school.principal}</div>
            </div>
          </div>
          <div className="text-[10px] text-slate-400 mt-4 text-center">{d.developer.name} · {d.developer.contact}</div>
        </div>
      </div>
    </div>
  );
}

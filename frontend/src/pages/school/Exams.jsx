import { useEffect, useState } from "react";
import api, { apiErr } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";

export default function Exams() {
  const [exams, setExams] = useState([]);
  const [classes, setClasses] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [selExam, setSelExam] = useState(null);
  const [students, setStudents] = useState([]);
  const [marks, setMarks] = useState({});
  const [subject, setSubject] = useState("");
  const [results, setResults] = useState(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", class_id: "", start_date: "", end_date: "", total_marks: 100, passing_marks: 40 });

  const load = async () => {
    const [e, c, s] = await Promise.all([api.get("/school/exams"), api.get("/school/classes"), api.get("/school/subjects")]);
    setExams(e.data); setClasses(c.data); setSubjects(s.data);
  };
  useEffect(() => { load(); }, []);

  const submit = async (e) => { e.preventDefault(); try { await api.post("/school/exams", { ...form, total_marks: Number(form.total_marks), passing_marks: Number(form.passing_marks) }); toast.success("Exam created"); setOpen(false); load(); } catch(e){toast.error(apiErr(e));} };

  const pick = async (ex) => {
    setSelExam(ex); setResults(null);
    const st = await api.get("/school/students", { params: { class_id: ex.class_id } });
    setStudents(st.data);
  };

  const enter = async () => {
    if (!subject) { toast.error("Choose subject"); return; }
    try {
      await api.post("/school/marks", { exam_id: selExam.id, subject_id: subject, marks: students.map(s => ({student_id: s.id, marks_obtained: Number(marks[s.id] || 0)})) });
      toast.success("Marks saved");
    } catch(e){ toast.error(apiErr(e)); }
  };
  const viewResults = async () => { const r = await api.get(`/school/results/${selExam.id}`); setResults(r.data); };

  return (
    <div className="space-y-6" data-testid="exams-page">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-3xl font-bold">Examinations</h1>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild><Button data-testid="new-exam">New exam</Button></DialogTrigger>
          <DialogContent><DialogHeader><DialogTitle>Create exam</DialogTitle></DialogHeader>
            <form onSubmit={submit} className="space-y-3">
              <div className="space-y-2"><Label>Name</Label><Input required value={form.name} onChange={(e)=>setForm({...form,name:e.target.value})}/></div>
              <div className="space-y-2"><Label>Class</Label>
                <Select value={form.class_id} onValueChange={(v)=>setForm({...form,class_id:v})}><SelectTrigger><SelectValue placeholder="Choose"/></SelectTrigger>
                  <SelectContent>{classes.map(c=><SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}</SelectContent></Select></div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2"><Label>Start</Label><Input type="date" required value={form.start_date} onChange={(e)=>setForm({...form,start_date:e.target.value})}/></div>
                <div className="space-y-2"><Label>End</Label><Input type="date" required value={form.end_date} onChange={(e)=>setForm({...form,end_date:e.target.value})}/></div>
                <div className="space-y-2"><Label>Total</Label><Input type="number" value={form.total_marks} onChange={(e)=>setForm({...form,total_marks:e.target.value})}/></div>
                <div className="space-y-2"><Label>Pass</Label><Input type="number" value={form.passing_marks} onChange={(e)=>setForm({...form,passing_marks:e.target.value})}/></div>
              </div>
              <Button type="submit" className="w-full">Create</Button>
            </form></DialogContent>
        </Dialog>
      </div>
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {exams.map(e => {
          const cls = classes.find(c=>c.id===e.class_id);
          return (
            <button key={e.id} onClick={()=>pick(e)} className={`text-start rounded-xl border p-5 card-hover ${selExam?.id===e.id?"border-primary bg-primary/5":"border-border bg-card"}`} data-testid={`exam-${e.id}`}>
              <div className="font-medium">{e.name}</div>
              <div className="text-xs text-muted-foreground mt-1">{cls?.name} · {e.start_date} – {e.end_date}</div>
            </button>
          );
        })}
        {exams.length === 0 && <div className="text-muted-foreground">No exams yet</div>}
      </div>
      {selExam && (
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="font-medium">Marks entry — {selExam.name}</div>
            <div className="flex gap-2">
              <Select value={subject} onValueChange={setSubject}><SelectTrigger className="w-48" data-testid="marks-subject"><SelectValue placeholder="Subject"/></SelectTrigger>
                <SelectContent>{subjects.map(s=><SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}</SelectContent></Select>
              <Button onClick={enter} data-testid="save-marks">Save marks</Button>
              <Button variant="outline" onClick={viewResults} data-testid="view-results">View results</Button>
            </div>
          </div>
          <div className="mt-4 grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {students.map(s => (
              <div key={s.id} className="flex items-center gap-2">
                <div className="text-sm flex-1 truncate">{s.name}</div>
                <Input type="number" className="w-24" placeholder={`/${selExam.total_marks}`} value={marks[s.id]||""} onChange={(e)=>setMarks({...marks,[s.id]:e.target.value})}/>
              </div>
            ))}
          </div>
          {results && (
            <div className="mt-6">
              <div className="font-medium mb-2">Results</div>
              <div className="rounded-lg border border-border overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-secondary/60 text-xs uppercase"><tr><th className="text-start px-3 py-2">Pos</th><th className="text-start px-3 py-2">Student</th><th className="text-start px-3 py-2">Obt/Total</th><th className="text-start px-3 py-2">%</th><th className="text-start px-3 py-2">Grade</th></tr></thead>
                  <tbody>{results.results.map(r=>(
                    <tr key={r.student_id} className="border-t border-border"><td className="px-3 py-2">{r.position}</td><td className="px-3 py-2">{r.student_name}</td><td className="px-3 py-2">{r.obtained}/{r.total}</td><td className="px-3 py-2">{r.percentage}%</td><td className="px-3 py-2 font-medium">{r.grade}</td></tr>
                  ))}</tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

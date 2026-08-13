import { useEffect, useState } from "react";
import api, { apiErr } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

export default function Attendance() {
  const [classes, setClasses] = useState([]);
  const [cid, setCid] = useState("");
  const [date, setDate] = useState(new Date().toISOString().slice(0,10));
  const [students, setStudents] = useState([]);
  const [marks, setMarks] = useState({});
  useEffect(() => { api.get("/school/classes").then(r=>setClasses(r.data)); }, []);
  useEffect(() => { if (!cid) return; api.get("/school/students", { params: { class_id: cid } }).then(r=>setStudents(r.data)); api.get("/school/attendance", { params: { class_id: cid, date } }).then(r => {
    const m = {}; r.data.forEach(a => m[a.student_id] = a.status); setMarks(m);
  }); }, [cid, date]);
  const set = (sid, st) => setMarks({...marks, [sid]: st});
  const save = async () => {
    try { await api.post("/school/attendance", { class_id: cid, date, entries: students.map(s => ({student_id: s.id, status: marks[s.id] || "present"})) }); toast.success("Attendance saved"); }
    catch(e){ toast.error(apiErr(e)); }
  };
  return (
    <div className="space-y-6" data-testid="attendance-page">
      <h1 className="font-display text-3xl font-bold">Attendance</h1>
      <div className="flex gap-3 flex-wrap">
        <Select value={cid} onValueChange={setCid}><SelectTrigger className="w-56" data-testid="att-class"><SelectValue placeholder="Choose class"/></SelectTrigger>
          <SelectContent>{classes.map(c=><SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}</SelectContent></Select>
        <Input type="date" value={date} onChange={(e)=>setDate(e.target.value)} className="max-w-48"/>
        {cid && <Button onClick={save} data-testid="att-save">Save attendance</Button>}
      </div>
      {cid && (
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-secondary/60 text-xs uppercase text-muted-foreground"><tr><th className="text-start px-4 py-3">Roll</th><th className="text-start px-4 py-3">Name</th><th className="text-start px-4 py-3">Status</th></tr></thead>
            <tbody>
              {students.map(s => (
                <tr key={s.id} className="border-t border-border">
                  <td className="px-4 py-2">{s.roll_number || "—"}</td>
                  <td className="px-4 py-2">{s.name}</td>
                  <td className="px-4 py-2">
                    <div className="inline-flex rounded-full border border-border overflow-hidden text-xs">
                      {["present","absent","late","leave"].map(st => (
                        <button key={st} onClick={()=>set(s.id, st)} data-testid={`att-${s.id}-${st}`}
                          className={`px-3 py-1 capitalize ${marks[s.id]===st?"bg-primary text-primary-foreground":"hover:bg-secondary"}`}>{st}</button>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
              {students.length===0 && <tr><td colSpan={3} className="text-center text-muted-foreground py-10">No students</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

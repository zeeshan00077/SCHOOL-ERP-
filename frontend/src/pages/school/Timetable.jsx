import { useEffect, useState } from "react";
import api, { apiErr } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";

const days = ["mon","tue","wed","thu","fri","sat"];
const periods = [1,2,3,4,5,6,7,8];

export default function Timetable() {
  const [classes, setClasses] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [cid, setCid] = useState("");
  const [entries, setEntries] = useState([]);
  const [form, setForm] = useState({ day: "mon", period: 1, start_time: "08:00", end_time: "08:45", subject_id: "", teacher_id: "", room: "" });
  useEffect(() => { api.get("/school/classes").then(r=>setClasses(r.data)); api.get("/school/subjects").then(r=>setSubjects(r.data)); api.get("/school/teachers").then(r=>setTeachers(r.data)); }, []);
  useEffect(() => { if (cid) api.get("/school/timetable", { params: { class_id: cid } }).then(r=>setEntries(r.data)); }, [cid]);
  const add = async (e) => { e.preventDefault(); try { await api.post("/school/timetable", { ...form, class_id: cid, period: Number(form.period) }); toast.success("Added"); const r = await api.get("/school/timetable", { params: { class_id: cid } }); setEntries(r.data); } catch(e){toast.error(apiErr(e));} };
  const del = async (id) => { await api.delete(`/school/timetable/${id}`); const r = await api.get("/school/timetable", { params: { class_id: cid } }); setEntries(r.data); };
  const grid = {}; entries.forEach(e => { grid[`${e.day}:${e.period}`] = e; });
  return (
    <div className="space-y-6" data-testid="timetable-page">
      <h1 className="font-display text-3xl font-bold">Timetable</h1>
      <Select value={cid} onValueChange={setCid}><SelectTrigger className="w-56" data-testid="tt-class"><SelectValue placeholder="Choose class"/></SelectTrigger>
        <SelectContent>{classes.map(c=><SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}</SelectContent></Select>
      {cid && (
        <>
          <div className="rounded-xl border border-border bg-card overflow-x-auto">
            <table className="w-full text-sm min-w-[720px]">
              <thead className="bg-secondary/60 text-xs uppercase"><tr><th className="px-3 py-2">Period</th>{days.map(d=><th key={d} className="px-3 py-2 capitalize">{d}</th>)}</tr></thead>
              <tbody>{periods.map(p => (
                <tr key={p} className="border-t border-border">
                  <td className="px-3 py-2 font-medium">{p}</td>
                  {days.map(d => { const e = grid[`${d}:${p}`]; return (
                    <td key={d} className="px-3 py-2 align-top">{e ? (
                      <div className="text-xs">
                        <div className="font-medium">{subjects.find(s=>s.id===e.subject_id)?.name || "—"}</div>
                        <div className="text-muted-foreground">{teachers.find(t=>t.id===e.teacher_id)?.name || ""}</div>
                        <button onClick={()=>del(e.id)} className="text-destructive mt-1">Remove</button>
                      </div>) : <span className="text-muted-foreground">·</span>}</td>
                  );})}
                </tr>
              ))}</tbody>
            </table>
          </div>
          <form onSubmit={add} className="rounded-xl border border-border bg-card p-5 grid sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="space-y-1"><Label className="text-xs">Day</Label>
              <Select value={form.day} onValueChange={(v)=>setForm({...form,day:v})}><SelectTrigger><SelectValue/></SelectTrigger>
                <SelectContent>{days.map(d=><SelectItem key={d} value={d} className="capitalize">{d}</SelectItem>)}</SelectContent></Select></div>
            <div className="space-y-1"><Label className="text-xs">Period</Label><Input type="number" value={form.period} onChange={(e)=>setForm({...form,period:e.target.value})}/></div>
            <div className="space-y-1"><Label className="text-xs">Start</Label><Input type="time" value={form.start_time} onChange={(e)=>setForm({...form,start_time:e.target.value})}/></div>
            <div className="space-y-1"><Label className="text-xs">End</Label><Input type="time" value={form.end_time} onChange={(e)=>setForm({...form,end_time:e.target.value})}/></div>
            <div className="space-y-1"><Label className="text-xs">Subject</Label>
              <Select value={form.subject_id} onValueChange={(v)=>setForm({...form,subject_id:v})}><SelectTrigger><SelectValue placeholder="—"/></SelectTrigger>
                <SelectContent>{subjects.map(s=><SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}</SelectContent></Select></div>
            <div className="space-y-1"><Label className="text-xs">Teacher</Label>
              <Select value={form.teacher_id} onValueChange={(v)=>setForm({...form,teacher_id:v})}><SelectTrigger><SelectValue placeholder="—"/></SelectTrigger>
                <SelectContent>{teachers.map(t=><SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}</SelectContent></Select></div>
            <div className="sm:col-span-3 lg:col-span-6"><Button type="submit" data-testid="tt-add">Add period</Button></div>
          </form>
        </>
      )}
    </div>
  );
}

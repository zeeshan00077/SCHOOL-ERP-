import { useEffect, useState } from "react";
import api, { apiErr } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

export default function Classes() {
  const [items, setItems] = useState([]);
  const [name, setName] = useState("");
  const [sec, setSec] = useState({});
  const load = () => api.get("/school/classes").then(r => setItems(r.data));
  useEffect(() => { load(); }, []);
  const addClass = async (e) => { e.preventDefault(); try { await api.post("/school/classes", { name, order: items.length }); setName(""); load(); } catch(e){toast.error(apiErr(e));} };
  const addSection = async (cid) => { const n = sec[cid]; if(!n) return; try { await api.post("/school/sections", { class_id: cid, name: n }); setSec({...sec,[cid]:""}); load(); } catch(e){toast.error(apiErr(e));} };
  const del = async (id) => { await api.delete(`/school/classes/${id}`); load(); };
  return (
    <div className="space-y-6" data-testid="classes-page">
      <h1 className="font-display text-3xl font-bold">Classes & Sections</h1>
      <form onSubmit={addClass} className="flex gap-2 max-w-md">
        <Input placeholder="Class name (e.g. Class 9)" value={name} onChange={(e)=>setName(e.target.value)} data-testid="class-name"/>
        <Button type="submit" data-testid="add-class">Add class</Button>
      </form>
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map(c => (
          <div key={c.id} className="rounded-xl border border-border bg-card p-5">
            <div className="flex items-center justify-between">
              <div className="font-medium">{c.name}</div>
              <Button size="sm" variant="ghost" onClick={()=>del(c.id)}>Delete</Button>
            </div>
            <div className="mt-3 text-xs uppercase text-muted-foreground">Sections</div>
            <div className="flex flex-wrap gap-2 mt-2">{c.sections?.map(s => <span key={s.id} className="text-xs px-2 py-1 rounded-full bg-secondary">{s.name}</span>)}</div>
            <div className="flex gap-2 mt-3">
              <Input placeholder="Section (A)" value={sec[c.id] || ""} onChange={(e)=>setSec({...sec,[c.id]:e.target.value})}/>
              <Button size="sm" onClick={()=>addSection(c.id)}>Add</Button>
            </div>
          </div>
        ))}
        {items.length === 0 && <div className="text-muted-foreground">No classes yet</div>}
      </div>
    </div>
  );
}

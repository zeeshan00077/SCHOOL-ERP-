import { useEffect, useState } from "react";
import api, { apiErr } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
export default function Notices() {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState({ title: "", body: "", audience: "all" });
  const load = () => api.get("/school/notices").then(r=>setItems(r.data));
  useEffect(() => { load(); }, []);
  const submit = async (e) => { e.preventDefault(); try { await api.post("/school/notices", form); toast.success("Notice posted"); setForm({title:"",body:"",audience:"all"}); load(); } catch(e){toast.error(apiErr(e));} };
  const del = async (id) => { await api.delete(`/school/notices/${id}`); load(); };
  return (
    <div className="space-y-6" data-testid="notices-page">
      <h1 className="font-display text-3xl font-bold">Notices</h1>
      <form onSubmit={submit} className="rounded-xl border border-border bg-card p-5 space-y-3">
        <div className="space-y-2"><Label>Title</Label><Input required value={form.title} onChange={(e)=>setForm({...form,title:e.target.value})} data-testid="notice-title"/></div>
        <div className="space-y-2"><Label>Body</Label><Textarea required rows={3} value={form.body} onChange={(e)=>setForm({...form,body:e.target.value})} data-testid="notice-body"/></div>
        <Button type="submit" data-testid="post-notice">Post notice</Button>
      </form>
      <div className="space-y-3">{items.map(n => (
        <div key={n.id} className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="font-medium">{n.title}</div>
              <div className="text-sm text-muted-foreground mt-1">{n.body}</div>
              <div className="text-xs text-muted-foreground mt-2">by {n.created_by_name} · {n.created_at?.slice(0,16).replace("T"," ")}</div>
            </div>
            <Button variant="ghost" size="sm" onClick={()=>del(n.id)}>Delete</Button>
          </div>
        </div>
      ))}
      {items.length === 0 && <div className="text-muted-foreground">No notices</div>}</div>
    </div>
  );
}

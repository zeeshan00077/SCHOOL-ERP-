import { useEffect, useState } from "react";
import api, { apiErr } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

export default function Schools() {
  const [items, setItems] = useState([]);
  const [q, setQ] = useState("");
  const load = () => api.get("/super-admin/schools", { params: q ? { q } : {} }).then(r => setItems(r.data));
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [q]);

  const act = async (id, kind) => {
    try {
      if (kind === "extend") await api.post(`/super-admin/schools/${id}/extend`, null, { params: { days: 30 } });
      if (kind === "activate") await api.post(`/super-admin/schools/${id}/activate`);
      if (kind === "suspend") await api.post(`/super-admin/schools/${id}/suspend`);
      toast.success("Updated");
      load();
    } catch (e) { toast.error(apiErr(e)); }
  };

  return (
    <div className="space-y-6" data-testid="schools-page">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-3xl font-bold">Schools</h1>
        <Input placeholder="Search…" value={q} onChange={(e)=>setQ(e.target.value)} className="max-w-xs" data-testid="schools-search"/>
      </div>
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-secondary/60 text-muted-foreground text-xs uppercase">
            <tr>
              <th className="text-start px-4 py-3">School</th>
              <th className="text-start px-4 py-3">Admin</th>
              <th className="text-start px-4 py-3">Status</th>
              <th className="text-start px-4 py-3">Days Left</th>
              <th className="text-start px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((s) => (
              <tr key={s.id} className="border-t border-border hover:bg-secondary/30">
                <td className="px-4 py-3">
                  <div className="font-medium">{s.name}</div>
                  <div className="text-xs text-muted-foreground">{s.city}</div>
                </td>
                <td className="px-4 py-3">
                  <div>{s.admin_name}</div>
                  <div className="text-xs text-muted-foreground">{s.admin_email}</div>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${s.subscription_status_effective === "active" ? "bg-primary/10 text-primary" : s.subscription_status_effective === "trial" ? "bg-accent/20" : "bg-destructive/10 text-destructive"}`}>
                    {s.subscription_status_effective}
                  </span>
                </td>
                <td className="px-4 py-3">{s.days_remaining}</td>
                <td className="px-4 py-3 flex flex-wrap gap-2">
                  <Button size="sm" variant="outline" onClick={()=>act(s.id, "extend")} data-testid={`extend-${s.id}`}>+30d</Button>
                  <Button size="sm" variant="outline" onClick={()=>act(s.id, "activate")} data-testid={`activate-${s.id}`}>Activate</Button>
                  <Button size="sm" variant="ghost" onClick={()=>act(s.id, "suspend")} data-testid={`suspend-${s.id}`}>Suspend</Button>
                </td>
              </tr>
            ))}
            {items.length === 0 && <tr><td colSpan={5} className="text-center text-muted-foreground py-10">No schools yet</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

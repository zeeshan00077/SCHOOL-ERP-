import { useEffect, useState } from "react";
import api from "@/lib/api";

export default function AuditLogs() {
  const [items, setItems] = useState([]);
  useEffect(() => { api.get("/super-admin/audit-logs").then(r => setItems(r.data)); }, []);
  return (
    <div className="space-y-6" data-testid="audit-page">
      <h1 className="font-display text-3xl font-bold">Audit logs</h1>
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-secondary/60 text-xs uppercase text-muted-foreground">
            <tr><th className="text-start px-4 py-3">When</th><th className="text-start px-4 py-3">Actor</th><th className="text-start px-4 py-3">Action</th><th className="text-start px-4 py-3">Module</th><th className="text-start px-4 py-3">Record</th></tr>
          </thead>
          <tbody>
            {items.map(a => (
              <tr key={a.id} className="border-t border-border">
                <td className="px-4 py-3 text-xs">{a.created_at}</td>
                <td className="px-4 py-3"><div>{a.actor_email}</div><div className="text-xs text-muted-foreground capitalize">{a.actor_role}</div></td>
                <td className="px-4 py-3 capitalize">{a.action.replace(/_/g," ")}</td>
                <td className="px-4 py-3 capitalize">{a.module}</td>
                <td className="px-4 py-3 text-xs text-muted-foreground">{a.record_id}</td>
              </tr>
            ))}
            {items.length === 0 && <tr><td colSpan={5} className="text-center text-muted-foreground py-10">No audit entries</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import api from "@/lib/api";
export default function Parents() {
  const [items, setItems] = useState([]);
  useEffect(() => { api.get("/school/parents").then(r => setItems(r.data)); }, []);
  return (
    <div className="space-y-6" data-testid="parents-page">
      <h1 className="font-display text-3xl font-bold">Parents</h1>
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map(p => (
          <div key={p.id} className="rounded-xl border border-border bg-card p-5">
            <div className="font-medium">{p.name}</div>
            <div className="text-xs text-muted-foreground">{p.email}</div>
            <div className="mt-3 text-xs uppercase text-muted-foreground">Children</div>
            <ul className="mt-1 text-sm">{p.children?.map(c => <li key={c.id}>• {c.name}</li>)}</ul>
          </div>
        ))}
        {items.length === 0 && <div className="text-muted-foreground">No parents yet</div>}
      </div>
    </div>
  );
}

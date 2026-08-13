import { useEffect, useState } from "react";
import api, { apiErr } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export default function SuperPayments() {
  const [items, setItems] = useState([]);
  const load = () => api.get("/super-admin/payments").then(r => setItems(r.data));
  useEffect(() => { load(); }, []);
  const decide = async (id, action) => {
    try {
      await api.post(`/super-admin/payments/${id}/${action}`, { remarks: action === "approve" ? "Approved" : "Rejected" });
      toast.success(`Payment ${action}d`); load();
    } catch (e) { toast.error(apiErr(e)); }
  };
  return (
    <div className="space-y-6" data-testid="payments-page">
      <h1 className="font-display text-3xl font-bold">Payment approvals</h1>
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-secondary/60 text-xs uppercase text-muted-foreground">
            <tr><th className="text-start px-4 py-3">Ref</th><th className="text-start px-4 py-3">Method</th><th className="text-start px-4 py-3">Amount</th><th className="text-start px-4 py-3">Status</th><th className="text-start px-4 py-3">Actions</th></tr>
          </thead>
          <tbody>
            {items.map(p => (
              <tr key={p.id} className="border-t border-border">
                <td className="px-4 py-3">
                  <div className="font-medium">{p.reference_number}</div>
                  <div className="text-xs text-muted-foreground">{p.payment_date}</div>
                </td>
                <td className="px-4 py-3 capitalize">{p.method.replace("_"," ")}</td>
                <td className="px-4 py-3">PKR {p.amount.toLocaleString()}</td>
                <td className="px-4 py-3"><span className={`px-2 py-1 rounded-full text-xs ${p.status==="approved"?"bg-primary/10 text-primary":p.status==="pending"?"bg-accent/20":"bg-destructive/10 text-destructive"}`}>{p.status}</span></td>
                <td className="px-4 py-3 space-x-2">
                  {p.status === "pending" && <>
                    <Button size="sm" onClick={()=>decide(p.id, "approve")} data-testid={`approve-${p.id}`}>Approve</Button>
                    <Button size="sm" variant="outline" onClick={()=>decide(p.id, "reject")}>Reject</Button>
                  </>}
                </td>
              </tr>
            ))}
            {items.length === 0 && <tr><td colSpan={5} className="text-center text-muted-foreground py-10">No payments yet</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

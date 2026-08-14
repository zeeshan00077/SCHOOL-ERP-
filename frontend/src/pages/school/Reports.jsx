import { useEffect, useState } from "react";
import api, { BACKEND_URL } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Download, FileText } from "lucide-react";

function preset(kind) {
  const now = new Date();
  const iso = (d) => d.toISOString().slice(0,10);
  const start = new Date(now); const end = new Date(now);
  if (kind === "today") return { date_from: iso(now), date_to: iso(now) };
  if (kind === "week") { start.setDate(now.getDate() - now.getDay()); return { date_from: iso(start), date_to: iso(now) }; }
  if (kind === "month") { start.setDate(1); return { date_from: iso(start), date_to: iso(now) }; }
  if (kind === "prev") { start.setMonth(now.getMonth()-1, 1); end.setDate(0); return { date_from: iso(start), date_to: iso(end) }; }
  if (kind === "year") { start.setMonth(0,1); return { date_from: iso(start), date_to: iso(now) }; }
  return { date_from: iso(now), date_to: iso(now) };
}

export default function Reports() {
  const [range, setRange] = useState(preset("month"));
  const [summary, setSummary] = useState(null);
  const load = () => api.get("/school/reports/summary", { params: range }).then(r => setSummary(r.data));
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [range.date_from, range.date_to]);

  const dl = async (path, filename) => {
    const url = `${BACKEND_URL}/api${path}`;
    const res = await fetch(url, { credentials: "include", headers: { Authorization: `Bearer ${localStorage.getItem("sz_access_token") || ""}` } });
    const blob = await res.blob();
    const u = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = u; a.download = filename; a.click();
  };

  return (
    <div className="space-y-6" data-testid="reports-page">
      <div>
        <h1 className="font-display text-3xl font-bold">Reports</h1>
        <p className="text-muted-foreground text-sm mt-1">Financial summary, downloadable data extracts and printable views.</p>
      </div>
      <div className="rounded-xl border border-border bg-card p-4 flex flex-wrap gap-3 items-end">
        <div className="space-y-1"><Label className="text-xs">From</Label><Input type="date" value={range.date_from} onChange={(e)=>setRange({...range, date_from: e.target.value})} className="w-40"/></div>
        <div className="space-y-1"><Label className="text-xs">To</Label><Input type="date" value={range.date_to} onChange={(e)=>setRange({...range, date_to: e.target.value})} className="w-40"/></div>
        <div className="flex gap-1">
          {[["today","Today"],["week","This week"],["month","This month"],["prev","Previous month"],["year","This year"]].map(([k,l])=>(
            <Button key={k} variant="outline" size="sm" onClick={()=>setRange(preset(k))} data-testid={`preset-${k}`}>{l}</Button>
          ))}
        </div>
      </div>
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Stat label="Fee income" value={`PKR ${summary.fee_income.toLocaleString()}`} testid="rep-income"/>
          <Stat label="Expenses" value={`PKR ${summary.expenses_total.toLocaleString()}`}/>
          <Stat label="Net balance" value={`PKR ${summary.net_balance.toLocaleString()}`} tone={summary.net_balance >= 0 ? "primary" : "destructive"}/>
          <Stat label="Outstanding" value={`PKR ${summary.outstanding.toLocaleString()}`}/>
        </div>
      )}
      {summary && (
        <div className="grid md:grid-cols-2 gap-4">
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="font-medium mb-3">Fee by method</div>
            <div className="space-y-1 text-sm">{Object.entries(summary.fee_by_method).map(([k,v]) => (
              <div key={k} className="flex justify-between"><span className="capitalize">{k}</span><span className="font-medium">PKR {v.toLocaleString()}</span></div>
            ))}{Object.keys(summary.fee_by_method).length===0 && <div className="text-muted-foreground">No collection in range</div>}</div>
          </div>
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="font-medium mb-3">Expenses by category</div>
            <div className="space-y-1 text-sm">{Object.entries(summary.expenses_by_category).map(([k,v]) => (
              <div key={k} className="flex justify-between"><span>{k}</span><span className="font-medium">PKR {v.toLocaleString()}</span></div>
            ))}{Object.keys(summary.expenses_by_category).length===0 && <div className="text-muted-foreground">No approved expenses in range</div>}</div>
          </div>
        </div>
      )}
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="font-medium mb-3">Exports (CSV)</div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={()=>dl(`/school/reports/students.csv`, "students.csv")} data-testid="csv-students"><FileText className="h-4 w-4 me-2"/>Students CSV</Button>
          <Button variant="outline" onClick={()=>dl(`/school/reports/fee-collection.csv?date_from=${range.date_from}&date_to=${range.date_to}`, "fee-collection.csv")} data-testid="csv-fee"><Download className="h-4 w-4 me-2"/>Fee collection CSV</Button>
        </div>
      </div>
    </div>
  );
}
function Stat({ label, value, tone = "primary", testid }) {
  return (
    <div className="rounded-xl border border-border bg-card p-5" data-testid={testid}>
      <div className="text-xs text-muted-foreground uppercase tracking-wide">{label}</div>
      <div className={`mt-2 font-display text-2xl font-bold ${tone === "destructive" ? "text-destructive" : "text-foreground"}`}>{value}</div>
    </div>
  );
}

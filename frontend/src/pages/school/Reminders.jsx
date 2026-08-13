import { useEffect, useState } from "react";
import api, { apiErr } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import { AlertTriangle, MessageCircle, Send } from "lucide-react";

export default function Reminders() {
  const [cfg, setCfg] = useState(null);
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState({});
  const [logs, setLogs] = useState([]);
  const load = async () => {
    const [c, d, l] = await Promise.all([
      api.get("/school/reminders/config"),
      api.get("/school/reminders/due-soon"),
      api.get("/school/reminders/logs"),
    ]);
    setCfg(c.data); setItems(d.data.items || []); setLogs(l.data);
  };
  useEffect(() => { load(); }, []);
  if (!cfg) return null;

  const save = async () => {
    try {
      await api.put("/school/reminders/config", {
        enabled: cfg.enabled, days_before: Number(cfg.days_before), template: cfg.template, school_contact: cfg.school_contact,
      });
      toast.success("Reminder settings saved"); load();
    } catch (e) { toast.error(apiErr(e)); }
  };
  const toggleAll = () => {
    const all = items.every(i => selected[i.invoice_id]);
    const next = {};
    items.forEach(i => { next[i.invoice_id] = !all; });
    setSelected(next);
  };
  const send = async () => {
    const ids = Object.entries(selected).filter(([,v])=>v).map(([k])=>k);
    if (!ids.length) { toast.error("Choose at least one row"); return; }
    try {
      const { data } = await api.post("/school/reminders/send", { invoice_ids: ids, dry_run: !cfg.integration_configured });
      if (!data.integration_configured) toast.warning(data.integration_note);
      else toast.success(`Sent ${data.queued} reminders`);
      setSelected({}); load();
    } catch (e) { toast.error(apiErr(e)); }
  };

  return (
    <div className="space-y-6" data-testid="reminders-page">
      <div>
        <h1 className="font-display text-3xl font-bold">WhatsApp Fee Reminders</h1>
        <p className="text-muted-foreground text-sm mt-1">Nudge parents before due dates. Real WhatsApp sending is enabled only when the Business API is configured.</p>
      </div>

      {!cfg.integration_configured && (
        <div className="rounded-xl border border-accent bg-accent/10 p-4 flex items-start gap-3" data-testid="wa-not-configured">
          <AlertTriangle className="h-5 w-5 text-accent-foreground mt-0.5"/>
          <div>
            <div className="font-medium">WhatsApp integration not configured</div>
            <div className="text-sm text-muted-foreground mt-1">{cfg.integration_note}</div>
            <div className="text-xs text-muted-foreground mt-2">Reminders queued here will be sent automatically once the API is enabled by the platform.</div>
          </div>
        </div>
      )}

      <div className="rounded-xl border border-border bg-card p-5 space-y-4">
        <div className="font-medium">Reminder settings</div>
        <div className="flex items-center gap-3">
          <Switch checked={cfg.enabled} onCheckedChange={(v)=>setCfg({...cfg, enabled: v})} data-testid="wa-enabled"/>
          <Label>Enable reminders</Label>
        </div>
        <div className="grid sm:grid-cols-2 gap-3">
          <div className="space-y-2"><Label>Days before due date</Label><Input type="number" min={1} max={30} value={cfg.days_before} onChange={(e)=>setCfg({...cfg, days_before: e.target.value})} data-testid="wa-days"/></div>
          <div className="space-y-2"><Label>School contact (shown to parents)</Label><Input value={cfg.school_contact || ""} onChange={(e)=>setCfg({...cfg, school_contact: e.target.value})}/></div>
        </div>
        <div className="space-y-2">
          <Label>Message template</Label>
          <Textarea rows={3} value={cfg.template} onChange={(e)=>setCfg({...cfg, template: e.target.value})} data-testid="wa-template"/>
          <p className="text-xs text-muted-foreground">Placeholders: {"{student_name}, {due_date}, {amount}, {school_name}"}</p>
        </div>
        <Button onClick={save} data-testid="wa-save">Save settings</Button>
      </div>

      <div className="rounded-xl border border-border bg-card">
        <div className="p-4 border-b border-border flex items-center justify-between gap-3">
          <div>
            <div className="font-medium">Due soon ({items.length})</div>
            <div className="text-xs text-muted-foreground">Invoices due within {cfg.days_before} days.</div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={toggleAll}>Select all</Button>
            <Button size="sm" onClick={send} data-testid="wa-send"><Send className="h-4 w-4 me-2"/>{cfg.integration_configured ? "Send now" : "Queue reminders"}</Button>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-secondary/60 text-xs uppercase text-muted-foreground">
              <tr><th className="p-3 w-8"></th><th className="text-start p-3">Student</th><th className="text-start p-3">Parent</th><th className="text-start p-3">Amount</th><th className="text-start p-3">Due</th><th className="text-start p-3">Preview</th></tr>
            </thead>
            <tbody>
              {items.map(i => (
                <tr key={i.invoice_id} className="border-t border-border align-top">
                  <td className="p-3"><input type="checkbox" checked={!!selected[i.invoice_id]} onChange={(e)=>setSelected({...selected,[i.invoice_id]:e.target.checked})} data-testid={`wa-check-${i.invoice_id}`}/></td>
                  <td className="p-3 font-medium">{i.student_name}</td>
                  <td className="p-3">{i.parent_name || <span className="text-muted-foreground">—</span>}<div className="text-xs text-muted-foreground">{i.parent_phone || "no phone"}</div></td>
                  <td className="p-3">PKR {i.amount_due.toLocaleString()}</td>
                  <td className="p-3">{i.due_date}</td>
                  <td className="p-3 max-w-md"><div className="text-xs bg-secondary/60 rounded px-2 py-1"><MessageCircle className="h-3 w-3 inline me-1"/> {i.preview_message}</div></td>
                </tr>
              ))}
              {items.length === 0 && <tr><td colSpan={6} className="text-center text-muted-foreground py-10">Nothing due within window</td></tr>}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card">
        <div className="p-4 border-b border-border font-medium">Reminder history</div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-secondary/60 text-xs uppercase text-muted-foreground"><tr>
              <th className="text-start p-3">When</th><th className="text-start p-3">Invoice</th><th className="text-start p-3">Status</th><th className="text-start p-3">Configured?</th>
            </tr></thead>
            <tbody>{logs.map(l => (
              <tr key={l.id} className="border-t border-border">
                <td className="p-3 text-xs">{l.created_at?.slice(0,16).replace("T"," ")}</td>
                <td className="p-3 text-xs">{l.invoice_id}</td>
                <td className="p-3"><span className={`text-xs px-2 py-0.5 rounded-full ${l.status==="sent"?"bg-primary/10 text-primary":"bg-accent/20"}`}>{l.status}</span></td>
                <td className="p-3 text-xs">{l.integration_configured ? "yes" : "no"}</td>
              </tr>))}
              {logs.length === 0 && <tr><td colSpan={4} className="text-center text-muted-foreground py-6">No reminders yet</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

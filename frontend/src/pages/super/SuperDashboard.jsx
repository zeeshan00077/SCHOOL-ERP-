import { useEffect, useState } from "react";
import api from "@/lib/api";
import { School, Users, GraduationCap, DollarSign, Clock, AlertTriangle } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, BarChart, Bar, CartesianGrid } from "recharts";

const Stat = ({ icon: Icon, label, value, sub, tint = "primary", testid }) => (
  <div className="card-hover rounded-xl border border-border bg-card p-5" data-testid={testid}>
    <div className="flex items-center gap-3">
      <div className={`h-10 w-10 rounded-lg bg-${tint}/10 text-${tint} grid place-items-center`}><Icon className="h-5 w-5"/></div>
      <div className="text-xs text-muted-foreground uppercase tracking-wide">{label}</div>
    </div>
    <div className="mt-3 font-display text-3xl font-bold">{value}</div>
    {sub && <div className="mt-1 text-xs text-muted-foreground">{sub}</div>}
  </div>
);

export default function SuperDashboard() {
  const [s, setS] = useState(null);
  useEffect(() => { api.get("/super-admin/stats").then(r => setS(r.data)); }, []);
  if (!s) return <div className="text-muted-foreground">Loading…</div>;
  return (
    <div className="space-y-6" data-testid="super-dashboard">
      <div>
        <h1 className="font-display text-3xl font-bold">Platform overview</h1>
        <p className="text-muted-foreground mt-1">All schools, subscriptions and revenue at a glance.</p>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <Stat icon={School} label="Total Schools" value={s.total_schools} testid="stat-schools"/>
        <Stat icon={Users} label="Active" value={s.active_schools}/>
        <Stat icon={Clock} label="Trial" value={s.trial_schools}/>
        <Stat icon={AlertTriangle} label="Expired" value={s.expired_schools}/>
        <Stat icon={GraduationCap} label="Students" value={s.total_students}/>
        <Stat icon={DollarSign} label="Revenue (PKR)" value={s.revenue?.toLocaleString?.() ?? 0}/>
      </div>
      <div className="grid lg:grid-cols-2 gap-4">
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="font-medium mb-4">Revenue trend (last 6 months)</div>
          <div className="h-64">
            <ResponsiveContainer>
              <BarChart data={s.revenue_series}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2}/>
                <XAxis dataKey="month" fontSize={12}/><YAxis fontSize={12}/>
                <Tooltip contentStyle={{background: "hsl(var(--card))", border: "1px solid hsl(var(--border))"}}/>
                <Bar dataKey="amount" fill="hsl(var(--chart-1))" radius={[6,6,0,0]}/>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="font-medium mb-4">School status split</div>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-primary/10 text-primary">
              <div className="text-xs uppercase">Active</div>
              <div className="text-3xl font-display font-bold mt-1">{s.active_schools}</div>
            </div>
            <div className="p-4 rounded-lg bg-accent/20 text-accent-foreground">
              <div className="text-xs uppercase">Trial</div>
              <div className="text-3xl font-display font-bold mt-1">{s.trial_schools}</div>
            </div>
            <div className="p-4 rounded-lg bg-destructive/10 text-destructive">
              <div className="text-xs uppercase">Expired</div>
              <div className="text-3xl font-display font-bold mt-1">{s.expired_schools}</div>
            </div>
            <div className="p-4 rounded-lg bg-secondary">
              <div className="text-xs uppercase text-muted-foreground">Suspended</div>
              <div className="text-3xl font-display font-bold mt-1">{s.suspended_schools}</div>
            </div>
          </div>
          <div className="mt-4 text-sm text-muted-foreground">Pending payments to approve: <span className="font-medium text-foreground">{s.pending_payments}</span></div>
        </div>
      </div>
    </div>
  );
}

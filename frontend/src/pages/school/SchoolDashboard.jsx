import { useEffect, useState } from "react";
import api from "@/lib/api";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, CartesianGrid } from "recharts";
import { Users, GraduationCap, Users2, CalendarCheck, CalendarX, Receipt, AlertTriangle } from "lucide-react";
import { Link } from "react-router-dom";

const Stat = ({ icon: Icon, label, value, tint = "primary", testid }) => (
  <div className="card-hover rounded-xl border border-border bg-card p-5" data-testid={testid}>
    <div className="flex items-center gap-3">
      <div className={`h-10 w-10 rounded-lg bg-${tint}/10 text-${tint} grid place-items-center`}><Icon className="h-5 w-5"/></div>
      <div className="text-xs text-muted-foreground uppercase tracking-wide">{label}</div>
    </div>
    <div className="mt-3 font-display text-3xl font-bold">{value}</div>
  </div>
);

export default function SchoolDashboard() {
  const [d, setD] = useState(null);
  const [err, setErr] = useState(null);
  useEffect(() => {
    api.get("/school/dashboard").then(r => setD(r.data)).catch(e => setErr(e?.response?.data?.detail || "Access blocked"));
  }, []);
  if (err) return (
    <div className="max-w-lg mx-auto text-center py-20 space-y-4">
      <AlertTriangle className="h-12 w-12 mx-auto text-destructive"/>
      <h1 className="font-display text-2xl font-bold">Access restricted</h1>
      <p className="text-muted-foreground">{err}</p>
      <Link to="/subscription" className="inline-flex text-primary underline">Renew subscription</Link>
    </div>
  );
  if (!d) return <div className="text-muted-foreground">Loading…</div>;

  return (
    <div className="space-y-6" data-testid="school-dashboard">
      <div>
        <h1 className="font-display text-3xl font-bold">Good day.</h1>
        <p className="text-muted-foreground mt-1">Here's what's happening in your school today.</p>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <Stat icon={Users} label="Students" value={d.total_students}/>
        <Stat icon={GraduationCap} label="Teachers" value={d.total_teachers}/>
        <Stat icon={Users2} label="Parents" value={d.total_parents}/>
        <Stat icon={CalendarCheck} label="Present Today" value={d.present_today}/>
        <Stat icon={CalendarX} label="Absent Today" value={d.absent_today}/>
        <Stat icon={Receipt} label="Fees Today (PKR)" value={d.fee_collection_today.toLocaleString()}/>
        <Stat icon={AlertTriangle} label="Pending Fees (PKR)" value={d.pending_fees.toLocaleString()}/>
      </div>
      <div className="grid lg:grid-cols-2 gap-4">
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="font-medium mb-4">Attendance last 7 days</div>
          <div className="h-64">
            <ResponsiveContainer><LineChart data={d.attendance_trend}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2}/>
              <XAxis dataKey="date" fontSize={11}/><YAxis fontSize={11}/>
              <Tooltip contentStyle={{background: "hsl(var(--card))", border: "1px solid hsl(var(--border))"}}/>
              <Line type="monotone" dataKey="present" stroke="hsl(var(--chart-1))" strokeWidth={2}/>
            </LineChart></ResponsiveContainer>
          </div>
        </div>
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="font-medium mb-4">Fee collection (last 6 months)</div>
          <div className="h-64">
            <ResponsiveContainer><BarChart data={d.fee_series}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2}/>
              <XAxis dataKey="month" fontSize={11}/><YAxis fontSize={11}/>
              <Tooltip contentStyle={{background: "hsl(var(--card))", border: "1px solid hsl(var(--border))"}}/>
              <Bar dataKey="amount" fill="hsl(var(--chart-2))" radius={[6,6,0,0]}/>
            </BarChart></ResponsiveContainer>
          </div>
        </div>
      </div>
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="font-medium mb-3">Recent notices</div>
        <div className="space-y-3">
          {d.notices.map(n => (
            <div key={n.id} className="border border-border rounded-md p-3">
              <div className="font-medium">{n.title}</div>
              <div className="text-sm text-muted-foreground">{n.body}</div>
            </div>
          ))}
          {d.notices.length === 0 && <div className="text-muted-foreground text-sm">No notices yet</div>}
        </div>
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import api, { apiErr, BACKEND_URL } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Cog, DollarSign, FileText, Play } from "lucide-react";

export default function Payroll() {
  const [teachers, setTeachers] = useState([]);
  const [month, setMonth] = useState(new Date().toISOString().slice(0,7));
  const [run, setRun] = useState(null);
  const [salaryModal, setSalaryModal] = useState(null);
  const [pay, setPay] = useState({ method: "cash", reference: "" });
  const [payRow, setPayRow] = useState(null);

  const loadRun = () => api.get("/school/payroll", { params: { month } }).then(r => setRun(r.data[0] || null));
  useEffect(() => { api.get("/school/teachers").then(r => setTeachers(r.data)); loadRun(); /* eslint-disable-next-line */ }, [month]);

  const process = async () => { try { await api.post("/school/payroll/process", { month }); toast.success("Payroll processed"); loadRun(); } catch (e) { toast.error(apiErr(e)); } };
  const saveSalary = async () => {
    try { await api.put(`/school/employees/${salaryModal.id}/salary`, {
      basic_salary: Number(salaryModal.basic_salary || 0),
      allowances: salaryModal.allowances || [],
      deductions: salaryModal.deductions || [],
      salary_type: "monthly",
    }); toast.success("Salary saved"); setSalaryModal(null);
      const r = await api.get("/school/teachers"); setTeachers(r.data);
    } catch (e) { toast.error(apiErr(e)); }
  };
  const submitPay = async () => { try { await api.post(`/school/payroll/${run.id}/pay`, { employee_id: payRow.employee_id, method: pay.method, reference: pay.reference }); toast.success("Paid"); setPayRow(null); loadRun(); } catch (e) { toast.error(apiErr(e)); } };
  const slipUrl = (empId) => `${BACKEND_URL}/api/school/payroll/${run?.id}/slip/${empId}.pdf`;
  const dlSlip = async (empId, name) => {
    try {
      const res = await fetch(slipUrl(empId), { credentials: "include", headers: { Authorization: `Bearer ${localStorage.getItem("sz_access_token") || ""}` } });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a"); a.href = url; a.download = `salary-${month}-${name}.pdf`; a.click();
    } catch { toast.error("Download failed"); }
  };
  const addAllow = () => setSalaryModal({ ...salaryModal, allowances: [...(salaryModal.allowances || []), { name: "House", amount: 0 }] });
  const addDeduct = () => setSalaryModal({ ...salaryModal, deductions: [...(salaryModal.deductions || []), { name: "Advance", amount: 0 }] });

  return (
    <div className="space-y-6" data-testid="payroll-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="font-display text-3xl font-bold">Payroll</h1>
        <div className="flex gap-2 items-center">
          <Label>Month</Label><Input type="month" value={month} onChange={(e)=>setMonth(e.target.value)} className="w-40"/>
          <Button onClick={process} data-testid="process-payroll"><Play className="h-4 w-4 me-2"/>Process</Button>
        </div>
      </div>
      <div className="rounded-xl border border-border bg-card p-4">
        <div className="font-medium mb-2">Employees & salaries</div>
        <div className="rounded-lg border border-border overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-secondary/60 text-xs uppercase"><tr><th className="text-start p-2">Name</th><th className="text-start p-2">Designation</th><th className="text-start p-2">Basic</th><th className="text-start p-2">Configured</th><th></th></tr></thead>
            <tbody>{teachers.map(t => (
              <tr key={t.id} className="border-t border-border">
                <td className="p-2">{t.name}</td>
                <td className="p-2">{t.subject || t.department || "—"}</td>
                <td className="p-2">PKR {(t.basic_salary ?? t.salary ?? 0).toLocaleString()}</td>
                <td className="p-2 text-xs">A:{(t.allowances||[]).length} D:{(t.deductions||[]).length}</td>
                <td className="p-2 text-end"><Button size="sm" variant="outline" onClick={()=>setSalaryModal({ ...t, basic_salary: t.basic_salary ?? t.salary ?? 0, allowances: t.allowances || [], deductions: t.deductions || [] })}><Cog className="h-4 w-4 me-1"/>Salary</Button></td>
              </tr>
            ))}{teachers.length===0 && <tr><td colSpan={5} className="text-center text-muted-foreground py-6">No employees</td></tr>}</tbody>
          </table>
        </div>
      </div>
      {run && (
        <div className="rounded-xl border border-border bg-card p-4">
          <div className="flex items-center justify-between mb-2"><div className="font-medium">Payroll for {run.month}</div><div className="text-sm text-muted-foreground">Total net: <b>PKR {run.total_net.toLocaleString()}</b></div></div>
          <div className="rounded-lg border border-border overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-secondary/60 text-xs uppercase"><tr><th className="text-start p-2">Employee</th><th className="text-start p-2">Basic</th><th className="text-start p-2">Allow</th><th className="text-start p-2">Deduct</th><th className="text-start p-2">Net</th><th className="text-start p-2">Status</th><th></th></tr></thead>
              <tbody>{run.entries.map(e => (
                <tr key={e.employee_id} className="border-t border-border">
                  <td className="p-2">{e.employee_name}</td>
                  <td className="p-2">{e.basic.toLocaleString()}</td><td className="p-2">{e.allow_total.toLocaleString()}</td>
                  <td className="p-2">{e.deduct_total.toLocaleString()}</td>
                  <td className="p-2 font-medium">PKR {e.net.toLocaleString()}</td>
                  <td className="p-2"><span className={`text-xs px-2 py-0.5 rounded-full ${e.status==="paid"?"bg-primary/10 text-primary":"bg-accent/20"}`}>{e.status}</span></td>
                  <td className="p-2 space-x-1">
                    {e.status !== "paid" && <Button size="sm" variant="outline" onClick={()=>{setPayRow(e); setPay({ method: "cash", reference: "" });}}><DollarSign className="h-4 w-4"/></Button>}
                    <Button size="sm" variant="ghost" onClick={()=>dlSlip(e.employee_id, e.employee_name)} title="Download slip"><FileText className="h-4 w-4"/></Button>
                  </td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </div>
      )}

      <Dialog open={!!salaryModal} onOpenChange={(o)=>!o && setSalaryModal(null)}>
        <DialogContent className="max-w-lg">{salaryModal && <>
          <DialogHeader><DialogTitle>Salary — {salaryModal.name}</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div className="space-y-2"><Label>Basic salary</Label><Input type="number" value={salaryModal.basic_salary} onChange={(e)=>setSalaryModal({...salaryModal, basic_salary: e.target.value})}/></div>
            <div className="space-y-2"><div className="flex items-center justify-between"><Label>Allowances</Label><Button size="sm" variant="outline" onClick={addAllow}>+ Add</Button></div>
              {salaryModal.allowances.map((a,i)=>(<div key={i} className="flex gap-2"><Input value={a.name} onChange={(e)=>{const arr=[...salaryModal.allowances]; arr[i]={...a,name:e.target.value}; setSalaryModal({...salaryModal,allowances:arr});}}/><Input type="number" value={a.amount} onChange={(e)=>{const arr=[...salaryModal.allowances]; arr[i]={...a,amount:Number(e.target.value)}; setSalaryModal({...salaryModal,allowances:arr});}}/></div>))}
            </div>
            <div className="space-y-2"><div className="flex items-center justify-between"><Label>Deductions</Label><Button size="sm" variant="outline" onClick={addDeduct}>+ Add</Button></div>
              {salaryModal.deductions.map((d,i)=>(<div key={i} className="flex gap-2"><Input value={d.name} onChange={(e)=>{const arr=[...salaryModal.deductions]; arr[i]={...d,name:e.target.value}; setSalaryModal({...salaryModal,deductions:arr});}}/><Input type="number" value={d.amount} onChange={(e)=>{const arr=[...salaryModal.deductions]; arr[i]={...d,amount:Number(e.target.value)}; setSalaryModal({...salaryModal,deductions:arr});}}/></div>))}
            </div>
            <Button onClick={saveSalary} className="w-full" data-testid="save-salary">Save salary</Button>
          </div>
        </>}</DialogContent>
      </Dialog>

      <Dialog open={!!payRow} onOpenChange={(o)=>!o && setPayRow(null)}>
        <DialogContent><DialogHeader><DialogTitle>Pay salary</DialogTitle></DialogHeader>
        {payRow && <div className="space-y-3">
          <div>Employee: <b>{payRow.employee_name}</b> · Net: <b>PKR {payRow.net.toLocaleString()}</b></div>
          <div className="space-y-2"><Label>Method</Label>
            <Select value={pay.method} onValueChange={(v)=>setPay({...pay,method:v})}><SelectTrigger><SelectValue/></SelectTrigger>
              <SelectContent>{["cash","bank","jazzcash","easypaisa","other"].map(m=><SelectItem key={m} value={m} className="capitalize">{m}</SelectItem>)}</SelectContent></Select></div>
          <div className="space-y-2"><Label>Reference</Label><Input value={pay.reference} onChange={(e)=>setPay({...pay, reference: e.target.value})}/></div>
          <Button onClick={submitPay} className="w-full" data-testid="pay-submit">Mark as paid</Button>
        </div>}
        </DialogContent>
      </Dialog>
    </div>
  );
}

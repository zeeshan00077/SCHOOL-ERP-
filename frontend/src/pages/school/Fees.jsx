import { useEffect, useState } from "react";
import api, { apiErr } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";

export default function Fees() {
  const [invoices, setInvoices] = useState([]);
  const [students, setStudents] = useState([]);
  const [openInv, setOpenInv] = useState(false);
  const [openPay, setOpenPay] = useState(false);
  const [selInv, setSelInv] = useState(null);
  const [inv, setInv] = useState({ student_id: "", title: "Monthly Fee", amount: 4000, due_date: new Date().toISOString().slice(0,10), month: new Date().toISOString().slice(0,7) });
  const [pay, setPay] = useState({ amount: 0, method: "cash", reference: "" });
  const load = async () => {
    const [i, s] = await Promise.all([api.get("/school/fee-invoices"), api.get("/school/students")]);
    setInvoices(i.data); setStudents(s.data);
  };
  useEffect(() => { load(); }, []);
  const submitInv = async (e) => { e.preventDefault(); try { await api.post("/school/fee-invoices", { ...inv, amount: Number(inv.amount) }); toast.success("Invoice created"); setOpenInv(false); load(); } catch(e){toast.error(apiErr(e));} };
  const submitPay = async (e) => { e.preventDefault(); try { await api.post("/school/fee-payments", { invoice_id: selInv.id, amount: Number(pay.amount), method: pay.method, reference: pay.reference }); toast.success("Payment recorded"); setOpenPay(false); load(); } catch(e){toast.error(apiErr(e));} };

  return (
    <div className="space-y-6" data-testid="fees-page">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-3xl font-bold">Fees</h1>
        <Dialog open={openInv} onOpenChange={setOpenInv}>
          <DialogTrigger asChild><Button data-testid="new-invoice">New invoice</Button></DialogTrigger>
          <DialogContent><DialogHeader><DialogTitle>Create invoice</DialogTitle></DialogHeader>
            <form onSubmit={submitInv} className="space-y-3">
              <div className="space-y-2"><Label>Student</Label>
                <Select value={inv.student_id} onValueChange={(v)=>setInv({...inv,student_id:v})}>
                  <SelectTrigger data-testid="inv-student"><SelectValue placeholder="Choose student"/></SelectTrigger>
                  <SelectContent>{students.map(s=><SelectItem key={s.id} value={s.id}>{s.name} ({s.admission_number})</SelectItem>)}</SelectContent>
                </Select></div>
              <div className="space-y-2"><Label>Title</Label><Input value={inv.title} onChange={(e)=>setInv({...inv,title:e.target.value})}/></div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2"><Label>Amount</Label><Input type="number" value={inv.amount} onChange={(e)=>setInv({...inv,amount:e.target.value})}/></div>
                <div className="space-y-2"><Label>Due date</Label><Input type="date" value={inv.due_date} onChange={(e)=>setInv({...inv,due_date:e.target.value})}/></div>
              </div>
              <Button type="submit" className="w-full">Create</Button>
            </form></DialogContent>
        </Dialog>
      </div>
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-secondary/60 text-xs uppercase text-muted-foreground"><tr>
            <th className="text-start px-4 py-3">Student</th><th className="text-start px-4 py-3">Title</th><th className="text-start px-4 py-3">Amount</th><th className="text-start px-4 py-3">Paid</th><th className="text-start px-4 py-3">Status</th><th className="text-start px-4 py-3">Due</th><th></th>
          </tr></thead>
          <tbody>
            {invoices.map(i => (
              <tr key={i.id} className="border-t border-border">
                <td className="px-4 py-3">{i.student_name}</td>
                <td className="px-4 py-3">{i.title}</td>
                <td className="px-4 py-3">PKR {i.amount.toLocaleString()}</td>
                <td className="px-4 py-3">PKR {(i.paid_amount||0).toLocaleString()}</td>
                <td className="px-4 py-3"><span className={`px-2 py-1 rounded-full text-xs ${i.status==="paid"?"bg-primary/10 text-primary":i.status==="partial"?"bg-accent/20":"bg-secondary"}`}>{i.status}</span></td>
                <td className="px-4 py-3">{i.due_date}</td>
                <td className="px-4 py-3 space-x-2">
                  {i.status!=="paid" && <Button size="sm" variant="outline" onClick={()=>{setSelInv(i);setPay({amount:i.amount-(i.paid_amount||0), method:"cash", reference:""});setOpenPay(true);}} data-testid={`pay-${i.id}`}>Record payment</Button>}
                  <Button size="sm" variant="ghost" onClick={()=>window.open(`/print/voucher/${i.id}`, "_blank")} data-testid={`voucher-${i.id}`}>Print voucher</Button>
                </td>
              </tr>
            ))}
            {invoices.length === 0 && <tr><td colSpan={7} className="text-center text-muted-foreground py-10">No invoices yet</td></tr>}
          </tbody>
        </table>
      </div>
      <Dialog open={openPay} onOpenChange={setOpenPay}>
        <DialogContent><DialogHeader><DialogTitle>Record payment</DialogTitle></DialogHeader>
          <form onSubmit={submitPay} className="space-y-3">
            <div className="space-y-2"><Label>Amount</Label><Input type="number" value={pay.amount} onChange={(e)=>setPay({...pay,amount:e.target.value})} data-testid="pay-amount"/></div>
            <div className="space-y-2"><Label>Method</Label>
              <Select value={pay.method} onValueChange={(v)=>setPay({...pay,method:v})}><SelectTrigger><SelectValue/></SelectTrigger>
                <SelectContent><SelectItem value="cash">Cash</SelectItem><SelectItem value="bank">Bank</SelectItem><SelectItem value="jazzcash">JazzCash</SelectItem><SelectItem value="easypaisa">Easypaisa</SelectItem></SelectContent>
              </Select></div>
            <div className="space-y-2"><Label>Reference</Label><Input value={pay.reference} onChange={(e)=>setPay({...pay,reference:e.target.value})}/></div>
            <Button type="submit" className="w-full" data-testid="pay-submit">Save payment</Button>
          </form></DialogContent>
      </Dialog>
    </div>
  );
}

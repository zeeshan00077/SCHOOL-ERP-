import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api from "@/lib/api";
import { GraduationCap, Printer } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function FeeVoucher() {
  const { invoiceId } = useParams();
  const [v, setV] = useState(null);
  useEffect(() => { api.get(`/school/fee-invoices/${invoiceId}/voucher`).then(r => setV(r.data)); }, [invoiceId]);
  if (!v) return <div className="p-10 text-center text-muted-foreground">Loading voucher…</div>;

  const Copy = ({ label }) => (
    <div className="voucher-copy border border-slate-300 rounded-md p-4 mb-4 bg-white text-slate-900">
      <div className="flex items-start justify-between border-b border-slate-200 pb-3 mb-3">
        <div className="flex items-center gap-3">
          {v.school.logo_url ? <img src={v.school.logo_url} alt="" className="h-14 w-14 object-contain"/> : <div className="h-14 w-14 rounded-lg bg-emerald-700 text-white grid place-items-center"><GraduationCap className="h-7 w-7"/></div>}
          <div>
            <div className="font-bold text-lg leading-tight">{v.school.name}</div>
            <div className="text-xs">{v.school.address}</div>
            <div className="text-xs">{v.school.phone} · {v.school.email}</div>
          </div>
        </div>
        <div className="text-end text-xs">
          <div className="font-bold uppercase text-sm">Fee Voucher</div>
          <div>Copy: <span className="font-semibold">{label}</span></div>
          <div>Voucher #: <span className="font-mono">{v.voucher_no}</span></div>
          <div>Issued: {v.issue_date}</div>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
        <div><span className="text-slate-500">Student:</span> <span className="font-medium">{v.student.name}</span></div>
        <div><span className="text-slate-500">Adm #:</span> {v.student.admission_number}</div>
        <div><span className="text-slate-500">Father:</span> {v.student.father_name || "—"}</div>
        <div><span className="text-slate-500">Roll #:</span> {v.student.roll_number || "—"}</div>
        <div><span className="text-slate-500">Class:</span> {v.student.class_name}</div>
        <div><span className="text-slate-500">Section:</span> {v.student.section_name || "—"}</div>
        <div><span className="text-slate-500">Fee for:</span> {v.invoice.month || v.invoice.title}</div>
        <div><span className="text-slate-500">Due date:</span> <span className="font-medium">{v.invoice.due_date}</span></div>
      </div>
      <table className="w-full text-sm mt-4 border-collapse">
        <thead><tr className="bg-slate-100 text-start"><th className="p-2 text-start">Description</th><th className="p-2 text-end">Amount (PKR)</th></tr></thead>
        <tbody>
          <tr><td className="p-2 border-t border-slate-200">{v.invoice.title}</td><td className="p-2 border-t border-slate-200 text-end">{v.invoice.amount.toLocaleString()}</td></tr>
          {v.invoice.paid_amount > 0 && <tr><td className="p-2 border-t border-slate-200">Already paid</td><td className="p-2 border-t border-slate-200 text-end">-{v.invoice.paid_amount.toLocaleString()}</td></tr>}
          {v.previous_balance > 0 && <tr><td className="p-2 border-t border-slate-200">Previous balance</td><td className="p-2 border-t border-slate-200 text-end">{v.previous_balance.toLocaleString()}</td></tr>}
          {v.invoice.discount ? <tr><td className="p-2 border-t border-slate-200">Discount</td><td className="p-2 border-t border-slate-200 text-end">-{Number(v.invoice.discount).toLocaleString()}</td></tr> : null}
          {v.invoice.fine ? <tr><td className="p-2 border-t border-slate-200">Fine</td><td className="p-2 border-t border-slate-200 text-end">{Number(v.invoice.fine).toLocaleString()}</td></tr> : null}
          <tr className="bg-slate-100 font-bold"><td className="p-2 border-t border-slate-300">Total Payable</td><td className="p-2 border-t border-slate-300 text-end">PKR {v.total_payable.toLocaleString()}</td></tr>
        </tbody>
      </table>
      <div className="mt-3 text-xs">
        <div className="uppercase text-slate-500 font-medium">Payment instructions</div>
        <div className="whitespace-pre-wrap mt-1">{v.school.bank_instructions || "Please pay at the school office or configured bank counter before the due date."}</div>
      </div>
      <div className="mt-6 flex justify-between text-xs text-slate-500 pt-3 border-t border-slate-200">
        <div>Parent's signature<br/>_______________________</div>
        <div>Cashier's stamp<br/>_______________________</div>
      </div>
      <div className="text-[10px] text-slate-400 mt-3 text-center">{v.developer.name} · {v.developer.contact}</div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-100 py-8">
      <div className="max-w-3xl mx-auto px-4 print:max-w-full print:px-0">
        <div className="flex items-center justify-between mb-4 print:hidden">
          <div className="text-slate-600 text-sm">Voucher for {v.student.name} — {v.invoice.title}</div>
          <Button onClick={()=>window.print()} data-testid="print-voucher"><Printer className="h-4 w-4 me-2"/>Print</Button>
        </div>
        <div className="voucher-sheet bg-white p-6 rounded shadow-sm print:shadow-none print:p-0">
          <Copy label="School Copy"/>
          <Copy label="Bank Copy"/>
          <Copy label="Parent Copy"/>
        </div>
      </div>
    </div>
  );
}

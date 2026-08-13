import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api, { BACKEND_URL } from "@/lib/api";
import { GraduationCap, Printer, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export default function FeeVoucher() {
  const { invoiceId } = useParams();
  const [v, setV] = useState(null);
  useEffect(() => { api.get(`/school/fee-invoices/${invoiceId}/voucher`).then(r => setV(r.data)); }, [invoiceId]);
  if (!v) return <div className="p-10 text-center text-muted-foreground">Loading voucher…</div>;

  const dl = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/school/fee-invoices/${invoiceId}/voucher.pdf`, { credentials: "include", headers: { Authorization: `Bearer ${localStorage.getItem("sz_access_token") || ""}` } });
      if (!res.ok) throw new Error("Failed to download");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a"); a.href = url; a.download = `voucher-${v.voucher_no}.pdf`; a.click();
    } catch (e) { toast.error(String(e.message || e)); }
  };

  const Copy = ({ label }) => (
    <div className="voucher-copy border border-slate-400 border-dashed p-3 bg-white text-slate-900" style={{minHeight: "88mm"}}>
      <div className="flex items-start justify-between border-b border-slate-300 pb-2 mb-2">
        <div className="flex items-center gap-2">
          {v.school.logo_url ? <img src={v.school.logo_url} alt="" className="h-10 w-10 object-contain"/> : <div className="h-10 w-10 rounded bg-emerald-700 text-white grid place-items-center"><GraduationCap className="h-5 w-5"/></div>}
          <div className="leading-tight">
            <div className="font-bold text-sm">{v.school.name}</div>
            <div className="text-[10px]">{v.school.address}</div>
            <div className="text-[10px]">{v.school.phone} · {v.school.email}</div>
          </div>
        </div>
        <div className="text-end text-[10px]">
          <div className="font-bold uppercase text-xs">Student Fee Voucher</div>
          <div className="font-semibold">{label}</div>
          <div>Voucher #: <span className="font-mono">{v.voucher_no}</span></div>
          <div>Issued: {v.issue_date}</div>
        </div>
      </div>
      <div className="grid grid-cols-4 gap-x-2 gap-y-0.5 text-[11px]">
        <div><span className="text-slate-500">Student:</span> <b>{v.student.name}</b></div>
        <div><span className="text-slate-500">Student ID:</span> <span className="font-mono">{v.student.student_id || v.student.admission_number}</span></div>
        <div><span className="text-slate-500">Class:</span> {v.student.class_name} {v.student.section_name}</div>
        <div><span className="text-slate-500">Roll #:</span> {v.student.roll_number || "—"}</div>
        <div><span className="text-slate-500">Father:</span> {v.student.father_name || "—"}</div>
        <div><span className="text-slate-500">Fee for:</span> {v.invoice.month || v.invoice.title}</div>
        <div><span className="text-slate-500">Due date:</span> <b>{v.invoice.due_date}</b></div>
        <div><span className="text-slate-500">Status:</span> {v.invoice.status}</div>
      </div>
      <table className="w-full text-[11px] mt-2 border-collapse">
        <thead><tr className="bg-slate-100"><th className="p-1 text-start border border-slate-300">Description</th><th className="p-1 text-end border border-slate-300">Amount (PKR)</th></tr></thead>
        <tbody>
          <tr><td className="p-1 border border-slate-300">{v.invoice.title}</td><td className="p-1 border border-slate-300 text-end">{v.invoice.amount.toLocaleString()}</td></tr>
          {v.invoice.paid_amount > 0 && <tr><td className="p-1 border border-slate-300">Already paid</td><td className="p-1 border border-slate-300 text-end">-{v.invoice.paid_amount.toLocaleString()}</td></tr>}
          {v.previous_balance > 0 && <tr><td className="p-1 border border-slate-300">Previous balance</td><td className="p-1 border border-slate-300 text-end">{v.previous_balance.toLocaleString()}</td></tr>}
          <tr className="bg-slate-100 font-bold"><td className="p-1 border border-slate-300">Total Payable</td><td className="p-1 border border-slate-300 text-end">PKR {v.total_payable.toLocaleString()}</td></tr>
        </tbody>
      </table>
      <div className="text-[9px] mt-2 whitespace-pre-wrap"><b>Payment:</b> {v.school.bank_instructions || "Pay at the school office before due date."}</div>
      <div className="text-[9px] text-slate-400 text-center mt-1">Zeeshan Computers Sheikh Fazal · 0343-0819382</div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-100 py-8">
      <div className="max-w-5xl mx-auto px-4 print:max-w-full print:px-0">
        <div className="flex items-center justify-between mb-4 print:hidden">
          <div className="text-slate-600 text-sm">Voucher — {v.student.name} · {v.invoice.title}</div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={()=>window.print()} data-testid="print-voucher"><Printer className="h-4 w-4 me-2"/>Print</Button>
            <Button onClick={dl} data-testid="dl-voucher"><Download className="h-4 w-4 me-2"/>Download PDF</Button>
          </div>
        </div>
        <div className="voucher-sheet bg-white p-4 rounded shadow-sm print:shadow-none print:p-0 space-y-2">
          <Copy label="Copy 1 — Student Copy"/>
          <Copy label="Copy 2 — Parent Copy"/>
          <Copy label="Copy 3 — Bank Copy"/>
        </div>
      </div>
    </div>
  );
}

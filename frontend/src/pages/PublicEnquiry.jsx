import { useEffect, useState } from "react";
import api, { apiErr } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { GraduationCap } from "lucide-react";
import { Link } from "react-router-dom";

export default function PublicEnquiry() {
  const [schools, setSchools] = useState([]);
  const [form, setForm] = useState({ school_id: "", student_name: "", father_name: "", mother_name: "", phone: "", email: "", desired_class: "", previous_school: "", message: "" });
  const [done, setDone] = useState(null);
  useEffect(() => { api.get("/public/schools").then(r => setSchools(r.data)); }, []);
  const submit = async (e) => { e.preventDefault(); try { const { data } = await api.post("/public/admission-enquiries", form); setDone(data); toast.success("Enquiry submitted"); } catch (err) { toast.error(apiErr(err)); } };
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="max-w-4xl mx-auto flex items-center gap-2 px-6 py-4">
          <Link to="/" className="flex items-center gap-2"><div className="h-9 w-9 rounded-xl bg-primary text-primary-foreground grid place-items-center"><GraduationCap className="h-5 w-5"/></div><span className="font-display font-semibold">Skoolzoom</span></Link>
        </div>
      </header>
      <main className="max-w-2xl mx-auto px-4 sm:px-6 py-10">
        <h1 className="font-display text-3xl sm:text-4xl font-bold">Admission enquiry</h1>
        <p className="text-muted-foreground mt-2">Choose a school and share your child's details — we'll get back to you.</p>
        {done ? (
          <div className="mt-8 rounded-xl border border-primary bg-primary/10 p-6">
            <div className="font-medium">Thank you! Enquiry received.</div>
            <div className="text-sm mt-2">Reference: <span className="font-mono">{done.enquiry_number}</span></div>
            <div className="text-sm">School: {done.school_name}</div>
            <Button className="mt-4" onClick={()=>setDone(null)}>Submit another</Button>
          </div>
        ) : (
        <form onSubmit={submit} className="mt-8 grid sm:grid-cols-2 gap-4 rounded-2xl border border-border bg-card p-6">
          <div className="sm:col-span-2 space-y-2"><Label>School</Label>
            <Select value={form.school_id} onValueChange={(v)=>setForm({...form, school_id: v})}>
              <SelectTrigger data-testid="enq-school"><SelectValue placeholder="Choose a school"/></SelectTrigger>
              <SelectContent>{schools.map(s => <SelectItem key={s.id} value={s.id}>{s.name} · {s.city}</SelectItem>)}</SelectContent>
            </Select></div>
          <div className="space-y-2"><Label>Student name *</Label><Input required value={form.student_name} onChange={(e)=>setForm({...form,student_name:e.target.value})}/></div>
          <div className="space-y-2"><Label>Desired class</Label><Input value={form.desired_class} onChange={(e)=>setForm({...form,desired_class:e.target.value})}/></div>
          <div className="space-y-2"><Label>Father's name</Label><Input value={form.father_name} onChange={(e)=>setForm({...form,father_name:e.target.value})}/></div>
          <div className="space-y-2"><Label>Mother's name</Label><Input value={form.mother_name} onChange={(e)=>setForm({...form,mother_name:e.target.value})}/></div>
          <div className="space-y-2"><Label>Phone *</Label><Input required value={form.phone} onChange={(e)=>setForm({...form,phone:e.target.value})}/></div>
          <div className="space-y-2"><Label>Email</Label><Input type="email" value={form.email} onChange={(e)=>setForm({...form,email:e.target.value})}/></div>
          <div className="sm:col-span-2 space-y-2"><Label>Previous school</Label><Input value={form.previous_school} onChange={(e)=>setForm({...form,previous_school:e.target.value})}/></div>
          <div className="sm:col-span-2 space-y-2"><Label>Message</Label><Textarea rows={3} value={form.message} onChange={(e)=>setForm({...form,message:e.target.value})}/></div>
          <div className="sm:col-span-2"><Button disabled={!form.school_id} type="submit" className="w-full" data-testid="enq-submit">Submit enquiry</Button></div>
        </form>
        )}
      </main>
    </div>
  );
}

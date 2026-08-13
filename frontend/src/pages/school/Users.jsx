import { useEffect, useState } from "react";
import api, { apiErr } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";
const empty = { name: "", email: "", password: "", role: "accountant", phone: "" };
export default function UsersPage() {
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(empty);
  const load = () => api.get("/school/users").then(r=>setItems(r.data));
  useEffect(() => { load(); }, []);
  const submit = async (e) => { e.preventDefault(); try { await api.post("/school/users", form); toast.success("User created"); setOpen(false); setForm(empty); load(); } catch(e){toast.error(apiErr(e));} };
  return (
    <div className="space-y-6" data-testid="users-page">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-3xl font-bold">Users & Roles</h1>
        <Dialog open={open} onOpenChange={setOpen}><DialogTrigger asChild><Button>Add user</Button></DialogTrigger>
          <DialogContent><DialogHeader><DialogTitle>New user</DialogTitle></DialogHeader>
            <form onSubmit={submit} className="space-y-3">
              <div className="space-y-2"><Label>Name</Label><Input required value={form.name} onChange={(e)=>setForm({...form,name:e.target.value})}/></div>
              <div className="space-y-2"><Label>Email</Label><Input type="email" required value={form.email} onChange={(e)=>setForm({...form,email:e.target.value})}/></div>
              <div className="space-y-2"><Label>Password</Label><Input type="password" required value={form.password} onChange={(e)=>setForm({...form,password:e.target.value})}/></div>
              <div className="space-y-2"><Label>Role</Label>
                <Select value={form.role} onValueChange={(v)=>setForm({...form,role:v})}><SelectTrigger><SelectValue/></SelectTrigger>
                  <SelectContent>{["school_admin","teacher","accountant","receptionist","librarian","parent","student"].map(r=><SelectItem key={r} value={r} className="capitalize">{r.replace("_"," ")}</SelectItem>)}</SelectContent></Select></div>
              <Button type="submit" className="w-full">Create user</Button>
            </form></DialogContent></Dialog>
      </div>
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <table className="w-full text-sm"><thead className="bg-secondary/60 text-xs uppercase"><tr><th className="text-start px-4 py-3">Name</th><th className="text-start px-4 py-3">Email</th><th className="text-start px-4 py-3">Role</th></tr></thead>
          <tbody>{items.map(u=>(<tr key={u.id} className="border-t border-border"><td className="px-4 py-3">{u.name}</td><td className="px-4 py-3">{u.email}</td><td className="px-4 py-3 capitalize">{u.role?.replace("_"," ")}</td></tr>))}
          {items.length===0 && <tr><td colSpan={3} className="text-center text-muted-foreground py-10">No users</td></tr>}</tbody></table>
      </div>
    </div>
  );
}

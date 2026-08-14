import { useEffect, useState } from "react";
import api, { apiErr } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Plus, Trash2, Copy, ShieldCheck } from "lucide-react";

const emptyRole = { name: "", description: "", permissions: {}, active: true };

export default function CustomRoles() {
  const [catalog, setCatalog] = useState(null);
  const [roles, setRoles] = useState([]);
  const [users, setUsers] = useState([]);
  const [edit, setEdit] = useState(null);

  const load = async () => {
    const [c, r, u] = await Promise.all([
      api.get("/school/permissions/catalog"),
      api.get("/school/custom-roles"),
      api.get("/school/users"),
    ]);
    setCatalog(c.data); setRoles(r.data); setUsers(u.data);
  };
  useEffect(() => { load(); }, []);
  if (!catalog) return null;

  const modules = Object.entries(catalog.modules);
  const toggle = (mod, action) => {
    const cur = edit.permissions[mod] || [];
    const next = cur.includes(action) ? cur.filter(a => a !== action) : [...cur, action];
    setEdit({ ...edit, permissions: { ...edit.permissions, [mod]: next } });
  };
  const save = async () => {
    try {
      if (edit.id) await api.put(`/school/custom-roles/${edit.id}`, edit);
      else await api.post("/school/custom-roles", edit);
      toast.success("Role saved"); setEdit(null); load();
    } catch (e) { toast.error(apiErr(e)); }
  };
  const del = async (r) => { if (!confirm(`Delete role ${r.name}?`)) return; try { await api.delete(`/school/custom-roles/${r.id}`); load(); } catch (e) { toast.error(apiErr(e)); } };
  const duplicate = (r) => setEdit({ name: r.name + " (copy)", description: r.description, permissions: JSON.parse(JSON.stringify(r.permissions || {})), active: true });
  const assign = async (uid, rid) => { try { await api.put(`/school/users/${uid}/custom-role`, { custom_role_id: rid || null }); toast.success("Role assigned"); load(); } catch (e) { toast.error(apiErr(e)); } };

  return (
    <div className="space-y-6" data-testid="custom-roles-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-display text-3xl font-bold">Custom roles</h1>
          <p className="text-muted-foreground text-sm mt-1 flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-primary"/> Permissions are enforced server-side. Roles are scoped to this school.</p>
        </div>
        <Button onClick={()=>setEdit({...emptyRole})} data-testid="new-role"><Plus className="h-4 w-4 me-2"/>New role</Button>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {roles.map(r => (
          <div key={r.id} className="rounded-xl border border-border bg-card p-5">
            <div className="flex items-center justify-between"><div className="font-medium">{r.name}</div>
              <div className="flex gap-1">
                <Button variant="ghost" size="sm" onClick={()=>setEdit(r)}>Edit</Button>
                <Button variant="ghost" size="sm" onClick={()=>duplicate(r)}><Copy className="h-4 w-4"/></Button>
                <Button variant="ghost" size="sm" onClick={()=>del(r)}><Trash2 className="h-4 w-4"/></Button>
              </div>
            </div>
            {r.description && <div className="text-xs text-muted-foreground mt-1">{r.description}</div>}
            <div className="mt-3 text-xs text-muted-foreground">Assigned to <b className="text-foreground">{r.assigned_users}</b> users</div>
            <div className="mt-2 flex flex-wrap gap-1">{Object.keys(r.permissions || {}).map(m => (
              <span key={m} className="text-[10px] px-2 py-0.5 rounded-full bg-secondary">{m}: {(r.permissions[m]||[]).length}</span>
            ))}</div>
          </div>
        ))}
        {roles.length === 0 && <div className="text-muted-foreground">No custom roles yet</div>}
      </div>

      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="p-4 border-b border-border font-medium">Assign roles to users</div>
        <table className="w-full text-sm">
          <thead className="bg-secondary/60 text-xs uppercase"><tr><th className="text-start p-3">User</th><th className="text-start p-3">Base role</th><th className="text-start p-3">Custom role</th></tr></thead>
          <tbody>{users.map(u => (
            <tr key={u.id} className="border-t border-border">
              <td className="p-3"><div>{u.name}</div><div className="text-xs text-muted-foreground">{u.email}</div></td>
              <td className="p-3 capitalize">{u.role?.replace("_"," ")}</td>
              <td className="p-3">
                <select value={u.custom_role_id || ""} onChange={(e)=>assign(u.id, e.target.value)} className="border border-border rounded px-2 py-1 bg-background" data-testid={`assign-${u.id}`}>
                  <option value="">(none)</option>
                  {roles.map(r=><option key={r.id} value={r.id}>{r.name}</option>)}
                </select>
              </td>
            </tr>
          ))}</tbody>
        </table>
      </div>

      <Dialog open={!!edit} onOpenChange={(o)=>!o && setEdit(null)}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          {edit && <>
            <DialogHeader><DialogTitle>{edit.id ? "Edit role" : "New role"}</DialogTitle></DialogHeader>
            <div className="space-y-3">
              <div className="space-y-2"><Label>Name</Label><Input value={edit.name} onChange={(e)=>setEdit({...edit, name: e.target.value})} data-testid="role-name"/></div>
              <div className="space-y-2"><Label>Description</Label><Textarea rows={2} value={edit.description||""} onChange={(e)=>setEdit({...edit, description: e.target.value})}/></div>
              <div className="rounded-lg border border-border overflow-x-auto">
                <table className="w-full text-xs">
                  <thead className="bg-secondary/60"><tr><th className="text-start p-2">Module</th>
                    {["view","add","create","edit","delete","approve","print","export","reports","receive_payment","create_invoice","cancel","enter_marks","edit_marks","publish_result","print_result","convert","reject","process"].map(a => <th key={a} className="p-2 capitalize">{a.replace("_"," ")}</th>)}</tr></thead>
                  <tbody>{modules.map(([m, acts]) => (
                    <tr key={m} className="border-t border-border">
                      <td className="p-2 font-medium capitalize">{m}</td>
                      {["view","add","create","edit","delete","approve","print","export","reports","receive_payment","create_invoice","cancel","enter_marks","edit_marks","publish_result","print_result","convert","reject","process"].map(a => (
                        <td key={a} className="p-2 text-center">
                          {acts.includes(a) ? <input type="checkbox" checked={(edit.permissions[m] || []).includes(a)} onChange={()=>toggle(m, a)} data-testid={`perm-${m}-${a}`}/> : <span className="text-muted-foreground">—</span>}
                        </td>
                      ))}
                    </tr>
                  ))}</tbody>
                </table>
              </div>
              <Button onClick={save} disabled={!edit.name} className="w-full" data-testid="role-save">Save role</Button>
            </div>
          </>}
        </DialogContent>
      </Dialog>
    </div>
  );
}

import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import { Building2, Users, FileText, Database, Shield, AlertCircle, Trash2, Power, PowerOff } from 'lucide-react';

interface CompanyMetrics {
  id: number;
  name: string;
  created_at: string;
  is_active: boolean;
  user_count: number;
  document_count: number;
  chunk_count: number;
}

interface UserItem {
  id: number;
  email: string;
  role: string;
  is_active: boolean;
  company_name: string;
}

interface DocItem {
  id: number;
  filename: string;
  page_count: number;
  chunk_count: number;
  is_active: boolean;
  uploaded_at: string;
  company_name: string;
}

export default function SuperAdminPanel() {
  const [tab, setTab] = useState<'overview' | 'companies' | 'users' | 'documents'>('overview');
  
  const [companies, setCompanies] = useState<CompanyMetrics[]>([]);
  const [users, setUsers] = useState<UserItem[]>([]);
  const [docs, setDocs] = useState<DocItem[]>([]);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [comps, usrs, dx] = await Promise.all([
        api.getSuperAdminCompanies(),
        api.getSuperAdminUsers(),
        api.getSuperAdminDocuments()
      ]);
      setCompanies(Array.isArray(comps) ? comps : []);
      setUsers(Array.isArray(usrs) ? usrs : []);
      setDocs(Array.isArray(dx) ? dx : []);
    } catch (e: any) {
      const errDetail = e.response?.data?.detail;
      setError(typeof errDetail === 'string' ? errDetail : "Failed to load platform data");
    } finally {
      setLoading(false);
    }
  }, []);

  const onToggleUser = async (userId: number) => {
    try {
        await api.toggleSuperAdminUser(userId);
        setUsers(users.map(u => u.id === userId ? { ...u, is_active: !u.is_active } : u));
    } catch (e: any) {
        alert(e.response?.data?.detail || "Failed to toggle user");
    }
  };

  const onDeleteUser = async (userId: number) => {
    if (!confirm("Are you sure you want to delete this user globally? This cannot be undone.")) return;
    try {
        await api.deleteSuperAdminUser(userId);
        setUsers(users.filter(u => u.id !== userId));
    } catch (e: any) {
        alert(e.response?.data?.detail || "Failed to delete user");
    }
  };

  const onToggleDoc = async (docId: number) => {
    try {
        await api.toggleSuperAdminDocument(docId);
        setDocs(docs.map(d => d.id === docId ? { ...d, is_active: !d.is_active } : d));
    } catch (e: any) {
        alert(e.response?.data?.detail || "Failed to toggle document");
    }
  };

  const onDeleteDoc = async (docId: number) => {
    if (!confirm("Are you sure you want to delete this document globally?")) return;
    try {
        await api.deleteSuperAdminDocument(docId);
        setDocs(docs.filter(d => d.id !== docId));
    } catch (e: any) {
        alert(e.response?.data?.detail || "Failed to delete document");
    }
  };

  const onToggleCompany = async (companyId: number) => {
    try {
        await api.toggleSuperAdminCompany(companyId);
        // Optimistically update company and ALL users belonging to it if it was disabled
        setCompanies(companies.map(c => {
            if (c.id === companyId) {
                const newStatus = !c.is_active;
                // If we JUST disabled it, we need to update the users list too
                if (!newStatus) {
                    setUsers(users.map(u => u.company_name === c.name ? { ...u, is_active: false } : u));
                }
                return { ...c, is_active: newStatus };
            }
            return c;
        }));
    } catch (e: any) {
        alert(e.response?.data?.detail || "Failed to toggle company");
    }
  };

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Derived metrics
  const totalUsers = users.length;
  const totalDocs = docs.length;
  const totalChunks = docs.reduce((acc, doc) => acc + doc.chunk_count, 0);

  const roleBadge = (role: string) => {
    const colors: Record<string, string> = { 
        superadmin: 'bg-red-100 text-red-700 font-bold',
        admin: 'bg-purple-100 text-purple-700', 
        engineer: 'bg-blue-100 text-blue-700', 
        viewer: 'bg-gray-100 text-gray-600' 
    };
    return <span className={`px-2 py-0.5 rounded-full text-xs font-medium capitalize ${colors[role] || colors.viewer}`}>{role}</span>;
  };

  return (
    <div className="space-y-6">
      {/* Super Admin Header */}
      <div className="flex items-center space-x-3 bg-gradient-to-r from-gray-900 to-gray-800 p-6 rounded-2xl shadow-lg border border-gray-700 overflow-hidden relative">
        <div className="absolute right-0 top-0 opacity-10">
          <Shield className="w-48 h-48 -mr-10 -mt-10" />
        </div>
        <div className="bg-red-500/20 p-3 rounded-xl border border-red-500/30">
            <Shield className="w-8 h-8 text-red-400" />
        </div>
        <div className="relative z-10">
          <h2 className="text-2xl font-bold text-white tracking-tight">Platform Dashboard</h2>
          <p className="text-sm text-gray-400 font-medium mt-1">Cross-Tenant Global Administration</p>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-3 rounded-md flex items-center">
          <AlertCircle className="w-4 h-4 text-red-500 mr-2 flex-shrink-0" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex space-x-2 border-b border-gray-200">
        {[
          { id: 'overview', label: 'Overview', icon: Database },
          { id: 'companies', label: 'Companies', icon: Building2 },
          { id: 'users', label: 'Global Users', icon: Users },
          { id: 'documents', label: 'Global Documents', icon: FileText },
        ].map((item) => {
          const Icon = item.icon;
          const isActive = tab === item.id;
          return (
            <button key={item.id} onClick={() => setTab(item.id as any)}
              className={`flex items-center space-x-2 px-4 py-3 text-sm font-semibold border-b-2 transition
                ${isActive ? 'border-red-500 text-red-600' : 'border-transparent text-gray-500 hover:text-gray-700'}
              `}>
              <Icon className="w-4 h-4" /><span>{item.label}</span>
            </button>
          )
        })}
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-500">Aggregating platform data...</div>
      ) : (
        <div className="pt-2">
            
          {/* ==================== OVERVIEW TAB ==================== */}
          {tab === 'overview' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
               <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                   <div className="flex items-center justify-between mb-4">
                       <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Registered Companies</h3>
                       <Building2 className="w-5 h-5 text-indigo-500" />
                   </div>
                   <p className="text-3xl font-black text-gray-900">{companies.length}</p>
               </div>
               <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                   <div className="flex items-center justify-between mb-4">
                       <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Total Users</h3>
                       <Users className="w-5 h-5 text-blue-500" />
                   </div>
                   <p className="text-3xl font-black text-gray-900">{totalUsers}</p>
               </div>
               <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                   <div className="flex items-center justify-between mb-4">
                       <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Total Documents</h3>
                       <FileText className="w-5 h-5 text-green-500" />
                   </div>
                   <p className="text-3xl font-black text-gray-900">{totalDocs}</p>
               </div>
               <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                   <div className="flex items-center justify-between mb-4">
                       <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Vector Chunks</h3>
                       <Database className="w-5 h-5 text-purple-500" />
                   </div>
                   <p className="text-3xl font-black text-gray-900">{totalChunks.toLocaleString()}</p>
               </div>
            </div>
          )}

          {/* ==================== COMPANIES TAB ==================== */}
          {tab === 'companies' && (
             <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">ID</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Company Name</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Users</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Documents</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Chunks</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Registered</th>
                      <th className="px-4 py-3 text-right text-xs font-bold text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {companies.map(c => (
                      <tr key={c.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm text-gray-500">#{c.id}</td>
                        <td className="px-4 py-3 text-sm font-semibold text-gray-900">{c.name}</td>
                        <td className="px-4 py-3 text-sm text-gray-600 font-medium"><Users className="w-3 h-3 inline mr-1"/>{c.user_count}</td>
                        <td className="px-4 py-3 text-sm text-gray-600 font-medium"><FileText className="w-3 h-3 inline mr-1"/>{c.document_count}</td>
                        <td className="px-4 py-3 text-sm text-gray-600 font-medium">{c.chunk_count.toLocaleString()}</td>
                        <td className="px-4 py-3">
                           <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${c.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                             {c.is_active ? 'Active' : 'Suspended'}
                           </span>
                        </td>
                        <td className="px-4 py-3 text-xs text-gray-500">{new Date(c.created_at).toLocaleDateString()}</td>
                        <td className="px-4 py-3 text-right">
                            <button 
                                onClick={() => onToggleCompany(c.id)}
                                title={c.is_active ? "Suspend Company" : "Activate Company"}
                                className={`p-1.5 rounded-lg transition ${c.is_active ? 'text-amber-600 hover:bg-amber-50' : 'text-green-600 hover:bg-green-50'}`}
                            >
                                {c.is_active ? <PowerOff className="w-4 h-4" /> : <Power className="w-4 h-4" />}
                            </button>
                        </td>
                      </tr>
                    ))}
                    {companies.length === 0 && (
                      <tr><td colSpan={6} className="px-4 py-8 text-center text-sm text-gray-400">No companies found</td></tr>
                    )}
                  </tbody>
                </table>
             </div>
          )}

          {/* ==================== GLOBALS USERS TAB ==================== */}
          {tab === 'users' && (
             <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Company</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Email</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Role</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Status</th>
                      <th className="px-4 py-3 text-right text-xs font-bold text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {users.map(u => (
                      <tr key={u.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm font-semibold text-indigo-700">{u.company_name}</td>
                        <td className="px-4 py-3 text-sm text-gray-900 font-medium">{u.email}</td>
                        <td className="px-4 py-3">{roleBadge(u.role)}</td>
                        <td className="px-4 py-3">
                           <span className={`text-xs font-medium ${u.is_active ? 'text-green-600' : 'text-red-500'}`}>
                             {u.is_active ? 'Active' : 'Disabled'}
                           </span>
                        </td>
                        <td className="px-4 py-3 text-right whitespace-nowrap">
                            <div className="flex justify-end space-x-2">
                                <button 
                                    onClick={() => onToggleUser(u.id)}
                                    title={u.is_active ? "Disable User" : "Enable User"}
                                    className={`p-1.5 rounded-lg transition ${u.is_active ? 'text-amber-600 hover:bg-amber-50' : 'text-green-600 hover:bg-green-50'}`}
                                >
                                    {u.is_active ? <PowerOff className="w-4 h-4" /> : <Power className="w-4 h-4" />}
                                </button>
                                <button 
                                    onClick={() => onDeleteUser(u.id)}
                                    title="Delete User"
                                    className="p-1.5 text-red-600 hover:bg-red-50 rounded-lg transition"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
             </div>
          )}
          
          {/* ==================== GLOBAL DOCS TAB ==================== */}
          {tab === 'documents' && (
             <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Company</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Filename</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Pages</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Chunks</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Uploaded</th>
                      <th className="px-4 py-3 text-right text-xs font-bold text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {docs.map(d => (
                      <tr key={d.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm font-semibold text-indigo-700">{d.company_name}</td>
                        <td className="px-4 py-3 text-sm text-gray-900 truncate max-w-xs">{d.filename}</td>
                        <td className="px-4 py-3 text-sm text-gray-600">{d.page_count}</td>
                        <td className="px-4 py-3 text-sm text-gray-600">{d.chunk_count}</td>
                        <td className="px-4 py-3">
                           <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${d.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                             {d.is_active ? 'Active' : 'Deactive'}
                           </span>
                        </td>
                        <td className="px-4 py-3 text-xs text-gray-500">{new Date(d.uploaded_at).toLocaleDateString()}</td>
                        <td className="px-4 py-3 text-right whitespace-nowrap">
                            <div className="flex justify-end space-x-2">
                                <button 
                                    onClick={() => onToggleDoc(d.id)}
                                    title={d.is_active ? "Deactivate Document" : "Activate Document"}
                                    className={`p-1.5 rounded-lg transition ${d.is_active ? 'text-amber-600 hover:bg-amber-50' : 'text-indigo-600 hover:bg-indigo-50'}`}
                                >
                                    {d.is_active ? <PowerOff className="w-4 h-4" /> : <Power className="w-4 h-4" />}
                                </button>
                                <button 
                                    onClick={() => onDeleteDoc(d.id)}
                                    title="Delete Document"
                                    className="p-1.5 text-red-600 hover:bg-red-50 rounded-lg transition"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                         </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
             </div>
          )}

        </div>
      )}
    </div>
  );
}

import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import { Building2, Users, FileText, Database, Shield, AlertCircle } from 'lucide-react';

interface CompanyMetrics {
  id: number;
  name: string;
  created_at: string;
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
                      <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Chunks Processed</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Registered On</th>
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
                        <td className="px-4 py-3 text-xs text-gray-500">{new Date(c.created_at).toLocaleDateString()}</td>
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

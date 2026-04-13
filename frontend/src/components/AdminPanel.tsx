import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import { useAppStore } from '../store/appStore';
import { Users, FileText, Plus, Trash2, ToggleLeft, ToggleRight, AlertCircle, Upload, Shield } from 'lucide-react';

interface UserItem { email: string; role: string; is_active: boolean; }
interface DocItem { id: number; filename: string; source: string; page_count: number; chunk_count: number; is_active: boolean; uploaded_at: string; }

export default function AdminPanel() {
  const [tab, setTab] = useState<'users' | 'documents'>('users');
  const [users, setUsers] = useState<UserItem[]>([]);
  const [docs, setDocs] = useState<DocItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Create user form
  const [showForm, setShowForm] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState('viewer');
  const [newEmpId, setNewEmpId] = useState('');

  const { uploadManual, isLoading: isUploading } = useAppStore();

  const flashSuccess = (msg: string) => {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(null), 3000);
  };

  const fetchUsers = useCallback(async () => {
    try { setUsers(await api.getUsers()); } catch (e: any) { setError(e.response?.data?.detail || 'Failed to load users'); }
  }, []);

  const fetchDocs = useCallback(async () => {
    try { setDocs(await api.getDocuments()); } catch (e: any) { setError(e.response?.data?.detail || 'Failed to load documents'); }
  }, []);

  useEffect(() => {
    setLoading(true);
    setError(null);
    Promise.all([fetchUsers(), fetchDocs()]).finally(() => setLoading(false));
  }, [fetchUsers, fetchDocs]);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await api.createUser({ email: newEmail, password: newPassword, role: newRole, employee_id: newEmpId || undefined });
      flashSuccess(`User ${newEmail} created successfully!`);
      setNewEmail(''); setNewPassword(''); setNewRole('viewer'); setNewEmpId(''); setShowForm(false);
      await fetchUsers();
    } catch (err: any) { setError(err.response?.data?.detail || 'Failed to create user'); }
  };

  const handleToggleUser = async (email: string) => {
    try { await api.toggleUser(email); await fetchUsers(); } catch (e: any) { setError(e.response?.data?.detail || 'Toggle failed'); }
  };

  const handleDeleteUser = async (email: string) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    try { await api.deleteUser(email); flashSuccess('User deleted.'); await fetchUsers(); } catch (e: any) { setError(e.response?.data?.detail || 'Delete failed'); }
  };

  const handleToggleDoc = async (docId: number) => {
    try { await api.toggleDocument(docId); await fetchDocs(); } catch (e: any) { setError(e.response?.data?.detail || 'Toggle failed'); }
  };

  const handleDeleteDoc = async (docId: number) => {
    if (!confirm('Are you sure you want to delete this document permanently?')) return;
    try {
        await api.deleteDocument(docId);
        flashSuccess('Document deleted successfully.');
        await fetchDocs();
    } catch (e: any) {
        setError(e.response?.data?.detail || 'Delete failed');
    }
  };

  const roleBadge = (role: string) => {
    const colors: Record<string, string> = { admin: 'bg-purple-100 text-purple-700', engineer: 'bg-blue-100 text-blue-700', viewer: 'bg-gray-100 text-gray-600' };
    return <span className={`px-2 py-0.5 rounded-full text-xs font-medium capitalize ${colors[role] || colors.viewer}`}>{role}</span>;
  };

  return (
    <div className="space-y-6">
      {/* Admin Header */}
      <div className="flex items-center space-x-3">
        <div className="bg-purple-600 p-2 rounded-lg"><Shield className="w-5 h-5 text-white" /></div>
        <div>
          <h2 className="text-lg font-bold text-gray-900">Admin Panel</h2>
          <p className="text-xs text-gray-500">Manage users and documents</p>
        </div>
      </div>

      {/* Feedback Messages */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-3 rounded-md flex items-center">
          <AlertCircle className="w-4 h-4 text-red-500 mr-2 flex-shrink-0" />
          <p className="text-sm text-red-700">{error}</p>
          <button className="ml-auto text-red-400 hover:text-red-600" onClick={() => setError(null)}>×</button>
        </div>
      )}
      {successMsg && (
        <div className="bg-green-50 border-l-4 border-green-500 p-3 rounded-md">
          <p className="text-sm text-green-700">✅ {successMsg}</p>
        </div>
      )}

      {/* Sub-Tab Navigation */}
      <div className="flex space-x-2 border-b border-gray-200">
        <button onClick={() => setTab('users')} className={`flex items-center space-x-2 px-4 py-2.5 text-sm font-medium border-b-2 transition ${tab === 'users' ? 'border-purple-600 text-purple-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
          <Users className="w-4 h-4" /><span>Users</span>
        </button>
        <button onClick={() => setTab('documents')} className={`flex items-center space-x-2 px-4 py-2.5 text-sm font-medium border-b-2 transition ${tab === 'documents' ? 'border-purple-600 text-purple-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
          <FileText className="w-4 h-4" /><span>Documents</span>
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : tab === 'users' ? (
        /* ==================== USERS TAB ==================== */
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-500">{users.length} user(s) registered</p>
            <button onClick={() => setShowForm(!showForm)} className="flex items-center space-x-1 bg-purple-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-purple-700 transition">
              <Plus className="w-4 h-4" /><span>{showForm ? 'Cancel' : 'Create User'}</span>
            </button>
          </div>

          {showForm && (
            <form onSubmit={handleCreateUser} className="bg-gray-50 p-4 rounded-xl border border-gray-200 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <input type="email" required placeholder="Email" value={newEmail} onChange={e => setNewEmail(e.target.value)} className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-purple-500 focus:border-purple-500 bg-white" />
                <input type="password" required placeholder="Password" value={newPassword} onChange={e => setNewPassword(e.target.value)} className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-purple-500 focus:border-purple-500 bg-white" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <select value={newRole} onChange={e => setNewRole(e.target.value)} className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-purple-500 focus:border-purple-500 bg-white">
                  <option value="viewer">Viewer</option>
                  <option value="engineer">Engineer</option>
                </select>
                <input type="text" placeholder="Employee ID (optional)" value={newEmpId} onChange={e => setNewEmpId(e.target.value)} className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-purple-500 focus:border-purple-500 bg-white" />
              </div>
              <button type="submit" className="bg-purple-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-purple-700 transition w-full">Create User</button>
            </form>
          )}

          {/* Users Table */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map(u => (
                  <tr key={u.email} className={!u.is_active ? 'opacity-50 bg-gray-50' : ''}>
                    <td className="px-4 py-3 text-sm text-gray-900">{u.email}</td>
                    <td className="px-4 py-3">{roleBadge(u.role)}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-medium ${u.is_active ? 'text-green-600' : 'text-red-500'}`}>
                        {u.is_active ? 'Active' : 'Disabled'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right space-x-2">
                      <button onClick={() => handleToggleUser(u.email)} className="text-gray-400 hover:text-blue-600 transition" title={u.is_active ? 'Disable' : 'Enable'}>
                        {u.is_active ? <ToggleRight className="w-5 h-5 inline text-green-500" /> : <ToggleLeft className="w-5 h-5 inline" />}
                      </button>
                      <button onClick={() => handleDeleteUser(u.email)} className="text-gray-400 hover:text-red-600 transition" title="Delete">
                        <Trash2 className="w-4 h-4 inline" />
                      </button>
                    </td>
                  </tr>
                ))}
                {users.length === 0 && (
                  <tr><td colSpan={4} className="px-4 py-8 text-center text-sm text-gray-400">No users found</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* ==================== DOCUMENTS TAB ==================== */
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-500">{docs.length} document(s) ingested</p>
            <div>
              <button
                onClick={() => document.getElementById('admin-pdf-upload')?.click()}
                disabled={isUploading}
                className="flex items-center space-x-1 bg-purple-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-purple-700 transition disabled:bg-gray-400"
              >
                <Upload className="w-4 h-4" /><span>{isUploading ? 'Uploading...' : 'Upload PDF'}</span>
              </button>
              <input
                type="file" id="admin-pdf-upload" accept=".pdf" className="hidden"
                onChange={async (e) => {
                  if (e.target.files?.[0]) {
                    await uploadManual(e.target.files[0]);
                    e.target.value = '';
                    await fetchDocs();
                  }
                }}
              />
            </div>
          </div>

          {/* Documents Table */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Filename</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Pages</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Chunks</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Uploaded</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {docs.map(d => (
                  <tr key={d.filename} className={!d.is_active ? 'opacity-50 bg-gray-50' : ''}>
                    <td className="px-4 py-3 text-sm text-gray-900 max-w-[200px] truncate" title={d.filename}>{d.filename}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{d.page_count}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{d.chunk_count}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${d.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {d.is_active ? 'Active' : 'Deactive'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500">{new Date(d.uploaded_at).toLocaleDateString()}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex justify-end space-x-2">
                        <button onClick={() => handleToggleDoc(d.id)} className="text-gray-400 hover:text-blue-600 transition" title={d.is_active ? 'Deactivate' : 'Activate'}>
                            {d.is_active ? <ToggleRight className="w-5 h-5 inline text-green-500" /> : <ToggleLeft className="w-5 h-5 inline" />}
                        </button>
                        <button onClick={() => handleDeleteDoc(d.id)} className="text-gray-400 hover:text-red-600 transition" title="Delete Permanent">
                            <Trash2 className="w-4 h-4 inline" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {docs.length === 0 && (
                  <tr><td colSpan={6} className="px-4 py-8 text-center text-sm text-gray-400">No documents ingested yet</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

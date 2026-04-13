import React, { useState, useEffect, Component, ErrorInfo, ReactNode } from 'react';
import UploadSection from './components/UploadSection';
import AnalysisResult from './components/AnalysisResult';
import HistoryView from './components/HistoryView';
import AdminPanel from './components/AdminPanel';
import SuperAdminPanel from './components/SuperAdminPanel';
import ChatWidget from './components/ChatWidget';
import { Settings, LogOut, User as UserIcon, RefreshCw, AlertOctagon } from 'lucide-react';
import { useAuthStore } from './store/authStore';
import LoginPage from './components/LoginPage';

// --- Error Boundary Component ---
interface EBProps { children: ReactNode; }
interface EBState { hasError: boolean; error: Error | null; }

class ErrorBoundary extends Component<EBProps, EBState> {
  constructor(props: EBProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): EBState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("UI CRASH CAPTURED:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
          <div className="max-w-xl w-full bg-white rounded-3xl shadow-2xl overflow-hidden border border-red-100 animate-in fade-in zoom-in duration-300">
             <div className="bg-red-600 p-8 flex flex-col items-center text-white">
                <div className="bg-white/20 p-4 rounded-full mb-4">
                   <AlertOctagon size={48} />
                </div>
                <h1 className="text-2xl font-black tracking-tight">System Interface Error</h1>
                <p className="text-red-100 mt-2 text-center text-sm opacity-90">
                  The AI generated a response that the interface couldn't render. 
                  This has been logged and we're ready to recover.
                </p>
             </div>
             
             <div className="p-8">
               <div className="bg-slate-900 rounded-xl p-5 mb-8">
                  <p className="text-pink-400 font-mono text-[11px] mb-2 uppercase tracking-widest font-bold">Error Stack Trace</p>
                  <pre className="text-slate-300 font-mono text-[10px] overflow-auto max-h-40 leading-relaxed thin-scrollbar">
                    {this.state.error?.toString()}\n{this.state.error?.stack}
                  </pre>
               </div>

               <div className="flex flex-col gap-3">
                  <button 
                    onClick={() => window.location.reload()}
                    className="w-full py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-2xl font-bold flex items-center justify-center gap-2 transition-all active:scale-95 shadow-lg shadow-blue-200"
                  >
                    <RefreshCw size={20} className="animate-spin-slow" />
                    Restart Application
                  </button>
                  <button 
                    onClick={() => {
                        localStorage.clear();
                        window.location.href = '/';
                    }}
                    className="w-full py-3 text-slate-500 hover:text-slate-800 font-medium text-sm transition-colors"
                  >
                    Reset System State & Logout
                  </button>
               </div>
             </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  const [view, setView] = useState<'analyze' | 'history' | 'admin' | 'superadmin'>('analyze');
  const { isAuthenticated, user, logout, hydrate } = useAuthStore();
  
  const isSuperAdmin = user?.role === 'superadmin';
  const isAdmin = user?.role === 'admin';
  const isViewer = user?.role === 'viewer';

  // Hydrate session
  useEffect(() => {
    hydrate();
  }, [hydrate]);

  // View state switching logic
  useEffect(() => {
    if (isAuthenticated) {
        if (isSuperAdmin) {
            if (view !== 'superadmin' && view !== 'analyze' && view !== 'history') {
                setView('superadmin');
            }
        } else if (isViewer) {
            if (view !== 'history') {
                setView('history');
            }
        } else if (view === 'superadmin') {
            setView('analyze');
        }
    }
  }, [isAuthenticated, isSuperAdmin, isViewer, view]);


  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <ErrorBoundary>
        <div className="min-h-screen bg-gray-50">
          {/* Header */}
          <header className="bg-white shadow-sm sticky top-0 z-10">
            <div className="max-w-7xl mx-auto px-4 py-4 flex flex-col sm:flex-row justify-between items-center space-y-4 sm:space-y-0">
               <div className="flex items-center space-x-3">
                  <div className="bg-blue-600 p-2 rounded-lg">
                     <Settings className="text-white w-6 h-6" />
                  </div>
                  <div>
                    <h1 className="text-xl font-bold text-gray-900">IndustriFix AI</h1>
                    <p className="text-xs text-gray-500">Multi-Modal RAG Maintenance System</p>
                  </div>
               </div>
               <div className="flex items-center space-x-6">
                  <span className="hidden md:inline-flex text-sm bg-green-100 text-green-700 px-3 py-1 rounded-full font-medium">
                    System Operational
                  </span>
                  
                  <div className="flex items-center space-x-4 border-l pl-6 border-gray-200">
                     <div className="flex flex-col text-right">
                        <span className="text-sm font-semibold text-gray-800">{user?.email}</span>
                        <span className="text-xs text-gray-500 capitalize flex items-center justify-end">
                          <UserIcon className="w-3 h-3 mr-1" />
                          {user?.role} Role{user?.company_name ? ` · ${user.company_name}` : ''}
                        </span>
                     </div>
                     <button 
                      onClick={logout}
                      className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-full transition"
                      title="Sign out"
                     >
                       <LogOut className="w-5 h-5" />
                     </button>
                  </div>
               </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="max-w-7xl mx-auto px-4 py-8">
            {isSuperAdmin ? (
                <div id="super-admin-content">
                    <SuperAdminPanel />
                </div>
            ) : (
                <div className="grid lg:grid-cols-12 gap-8">
                    {/* Left Column: Navigation & Upload */}
                    <div className="lg:col-span-4 space-y-6">
                       <div className={`grid ${isAdmin ? 'grid-cols-3' : isViewer ? 'grid-cols-1' : 'grid-cols-2'} gap-4`}>
                          {!isViewer && (
                            <button 
                              onClick={() => setView('analyze')}
                              className={`p-4 rounded-xl text-center transition ${view === 'analyze' ? 'bg-blue-600 text-white shadow-lg' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
                            >
                               <div className="font-semibold">Analyze</div>
                            </button>
                          )}
                          <button 
                            onClick={() => setView('history')}
                            className={`p-4 rounded-xl text-center transition ${view === 'history' ? 'bg-blue-600 text-white shadow-lg' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
                          >
                             <div className="font-semibold">History</div>
                          </button>
                          {isAdmin && (
                            <button 
                              onClick={() => setView('admin')}
                              className={`p-4 rounded-xl text-center transition ${view === 'admin' ? 'bg-purple-600 text-white shadow-lg' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
                            >
                               <div className="font-semibold">Admin</div>
                            </button>
                          )}
                       </div>

                       {view === 'analyze' && (
                           <UploadSection />
                       )}
                    </div>

                    {/* Right Column: Results */}
                    <div className="lg:col-span-8">
                       {view === 'analyze' && <AnalysisResult />}
                       {view === 'history' && <HistoryView />}
                       {view === 'admin' && isAdmin && <AdminPanel />}
                       {view === 'superadmin' && <div className="p-12 text-center text-gray-500">Super Admin View Active</div>}
                    </div>
                </div>
            )}
          </main>

          <ChatWidget />
        </div>
    </ErrorBoundary>
  );
}


export default App;

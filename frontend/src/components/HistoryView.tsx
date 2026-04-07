import React, { useEffect } from 'react';
import { useAppStore } from '../store/appStore';
import { Clock, DollarSign } from 'lucide-react';

const HistoryView: React.FC = () => {
    const { history, fetchHistory, isLoading } = useAppStore();
    const [selectedLog, setSelectedLog] = React.useState<any | null>(null);

    useEffect(() => {
        fetchHistory();
    }, []);

    if (isLoading && history.length === 0) return <div className="p-8 text-center">Loading history...</div>;

    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-800">Repair Log History</h2>
            
            <div className="grid gap-6">
                {history.map((log: any) => (
                    <div key={log.id} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition">
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <h3 className="text-xl font-bold text-gray-800">{log.machine_part}</h3>
                                <p className="text-sm text-gray-500">{new Date(log.timestamp).toLocaleString()}</p>
                            </div>
                            <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                                {log.failure_type}
                            </span>
                        </div>

                         {/* User Query Display */}
                         {log.query_text ? (
                            <div className="mb-4 bg-gray-50 p-3 rounded-lg border border-gray-100">
                                <span className="text-xs font-bold text-gray-500 uppercase tracking-wide">User Note</span>
                                <p className="text-sm text-gray-700 mt-1 italic">"{log.query_text}"</p>
                            </div>
                        ) : (
                            <div className="mb-4 bg-blue-50 p-3 rounded-lg border border-blue-100">
                                <span className="text-xs font-bold text-blue-600 uppercase tracking-wide">Auto-Diagnosis</span>
                                <p className="text-sm text-blue-800 mt-1">
                                    Identified failure: {log.failure_type}
                                </p>
                            </div>
                        )}

                        <div className="grid md:grid-cols-2 gap-4 mb-4">
                            <div className="flex items-center text-gray-600">
                                <Clock className="w-4 h-4 mr-2" />
                                <span>AI Time: {log.estimated_time_minutes} mins</span>
                            </div>
                            <div className="flex items-center text-green-600 font-medium">
                                <DollarSign className="w-4 h-4 mr-2" />
                                <span>Saved: ${log.savings_usd}</span>
                            </div>
                        </div>

                        <div className="flex justify-between items-end">
                             <div className="text-sm text-gray-500">
                                {log.repair_steps ? `${log.repair_steps.length} steps recorded` : 'No steps'} 
                             </div>
                             <button 
                                onClick={() => setSelectedLog(log)}
                                className="text-blue-600 font-medium hover:text-blue-800 hover:underline"
                             >
                                 View Full Guide &rarr;
                             </button>
                        </div>
                    </div>
                ))}
            </div>
            
            {history.length === 0 && !isLoading && (
                <div className="text-center text-gray-500 py-12">
                    No repair history found. Analyze a machine to get started!
                </div>
            )}

            {/* Detail Modal */}
            {selectedLog && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl animate-fade-in relative">
                        <button 
                            onClick={() => setSelectedLog(null)}
                            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
                        >
                            ✕
                        </button>
                        
                        <div className="p-6">
                            <h2 className="text-2xl font-bold text-gray-900 mb-1">{selectedLog.machine_part}</h2>
                            <p className="text-gray-500 mb-6">{selectedLog.failure_type}</p>
                            
                            {selectedLog.query_text ? (
                                <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                                    <h4 className="text-sm font-bold text-gray-700 uppercase mb-2">Original Note</h4>
                                    <p className="text-gray-600 italic">"{selectedLog.query_text}"</p>
                                </div>
                            ) : (
                                <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-100">
                                    <h4 className="text-sm font-bold text-blue-700 uppercase mb-2">Auto-Diagnosis</h4>
                                    <p className="text-blue-800">
                                        No user description provided. AI automatically identified the issue as: <strong>{selectedLog.failure_type}</strong>.
                                    </p>
                                </div>
                            )}

                             <div className="mb-6">
                                <h3 className="font-bold text-lg mb-3 flex items-center">
                                    Tools Required
                                </h3>
                                <div className="flex flex-wrap gap-2">
                                    {selectedLog.tools_required && selectedLog.tools_required.map((tool: string, i: number) => (
                                        <span key={i} className="bg-gray-100 text-gray-700 px-3 py-1 rounded-md text-sm border">
                                            {tool}
                                        </span>
                                    ))}
                                </div>
                            </div>

                            <div>
                                <h3 className="font-bold text-lg mb-3">Repair Steps</h3>
                                <ol className="space-y-4">
                                    {selectedLog.repair_steps && selectedLog.repair_steps.map((step: string, i: number) => (
                                        <li key={i} className="flex items-start">
                                            <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-bold mr-3 mt-0.5">
                                                {i + 1}
                                            </span>
                                            <span className="text-gray-700">{step}</span>
                                        </li>
                                    ))}
                                </ol>
                            </div>
                            
                            <div className="mt-8 pt-6 border-t flex justify-end">
                                <button 
                                    onClick={() => setSelectedLog(null)}
                                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
                                >
                                    Close
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default HistoryView;

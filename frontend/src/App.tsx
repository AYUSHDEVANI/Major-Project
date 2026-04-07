import React, { useState } from 'react';
import UploadSection from './components/UploadSection';
import AnalysisResult from './components/AnalysisResult';
import HistoryView from './components/HistoryView';
import { Settings } from 'lucide-react';

function App() {
  const [view, setView] = useState<'analyze' | 'history'>('analyze');
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
           <div className="flex items-center space-x-3">
              <div className="bg-blue-600 p-2 rounded-lg">
                 <Settings className="text-white w-6 h-6" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">IndustriFix AI</h1>
                <p className="text-xs text-gray-500">Multi-Modal RAG Maintenance System</p>
              </div>
           </div>
           <div>
              <span className="text-sm bg-green-100 text-green-700 px-3 py-1 rounded-full font-medium">
                System Operational
              </span>
           </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8 grid lg:grid-cols-12 gap-8">
        {/* Left Column: Navigation & Upload */}
        <div className="lg:col-span-4 space-y-6">
           {/* Navigation Cards */}
           <div className="grid grid-cols-2 gap-4">
              <button 
                onClick={() => setView('analyze')}
                className={`p-4 rounded-xl text-center transition ${view === 'analyze' ? 'bg-blue-600 text-white shadow-lg' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
              >
                 <div className="font-semibold">Analyze</div>
              </button>
              <button 
                onClick={() => setView('history')}
                className={`p-4 rounded-xl text-center transition ${view === 'history' ? 'bg-blue-600 text-white shadow-lg' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
              >
                 <div className="font-semibold">History</div>
              </button>
           </div>

           {view === 'analyze' && (
               <>
                <UploadSection />
                
                <div className="bg-white p-6 rounded-xl shadow-md">
                    <h3 className="font-semibold text-gray-700 mb-3">Knowledge Base</h3>
                    <p className="text-sm text-gray-500 mb-4">
                        Upload manual PDFs to train the RAG system with new machine data.
                    </p>
                    <button 
                        onClick={() => document.getElementById('manual-upload')?.click()}
                        className="w-full border border-gray-300 py-2 rounded-lg text-gray-600 hover:bg-gray-50 transition"
                    >
                        Upload New Manual
                    </button>
                    <input 
                        type="file" 
                        id="manual-upload" 
                        accept=".pdf"
                        className="hidden"
                        onChange={async (e) => {
                            if (e.target.files?.[0]) {
                              alert("To upload manuals, please use the Swagger UI at http://localhost:8000/docs for full ingestion feedback.");
                            }
                        }}
                    />
                </div>
               </>
           )}
        </div>

        {/* Right Column: Results */}
        <div className="lg:col-span-8">
           {view === 'analyze' ? <AnalysisResult /> : <HistoryView />}
        </div>
      </main>
    </div>
  );
}

export default App;

import React from 'react';
import { useAppStore } from '../store/appStore';
import { AlertTriangle, Wrench, Clock, DollarSign, CheckCircle } from 'lucide-react';

const AnalysisResult: React.FC = () => {
    const { analysisResult, isLoading, error, currentStep } = useAppStore();

    // Checklist State
    const [checkedSteps, setCheckedSteps] = React.useState<boolean[]>([]);

    React.useEffect(() => {
        if (analysisResult?.analysis_result?.repair_steps) {
            setCheckedSteps(new Array(analysisResult.analysis_result.repair_steps.length).fill(false));
        }
    }, [analysisResult]);

    const getStepMessage = (step: string | null) => {
        switch (step) {
            case 'starting': return 'Initializing LangGraph AI Engine...';
            case 'retrieve': return 'Retrieving related technical manuals from Qdrant...';
            case 'generate': return 'Generating structured repair instructions with Gemini...';
            case 'safety': return 'Injecting industrial safety protocols and hazards...';
            case 'roi': return 'Calculating AI Time-Savings & Return on Investment...';
            case 'erp': return 'Simulating ticket creation in SAP ERP System...';
            default: return 'Processing machine data... Please wait.';
        }
    };

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center p-12 mt-6 bg-white rounded-xl shadow-sm border border-blue-100">
                <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-6"></div>
                <h3 className="text-xl font-bold text-gray-800 mb-2">Analyzing Equipment</h3>
                <p className="text-blue-600 font-medium animate-pulse text-center">{getStepMessage(currentStep)}</p>
            </div>
        );
    }
    if (error) return <div className="text-center p-8 text-red-500 bg-red-50 rounded-lg">{error}</div>;
    if (!analysisResult) return <div className="text-center p-8 text-gray-400">Upload a machine image to begin analysis.</div>;

    const { analysis_result, safety_warnings = [], roi_data = {} as any } = analysisResult;
    
    // Safety check: if analysis_result is missing, don't crash the whole UI
    if (!analysis_result || !analysis_result.machine_part) {
        return <div className="text-center p-8 text-yellow-600 bg-yellow-50 rounded-lg border border-yellow-200">
            ⚠️ Analysis found, but result format is incomplete. Please retry or check logs.
        </div>;
    }

    const toggleStep = (index: number) => {
        const newChecked = [...checkedSteps];
        newChecked[index] = !newChecked[index];
        setCheckedSteps(newChecked);
    };

    const progress = checkedSteps.length > 0 ? Math.round((checkedSteps.filter(Boolean).length / checkedSteps.length) * 100) : 0;


    return (
        <div className="space-y-6 animate-fade-in">
            {/* Safety Warnings */}
            {safety_warnings.length > 0 && (
                <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-r-lg">
                    <h3 className="text-red-700 font-bold flex items-center mb-2">
                        <AlertTriangle className="mr-2" size={20} /> Safety First!
                    </h3>
                    <ul className="list-disc list-inside text-red-600 space-y-1">
                        {safety_warnings.map((warning, idx) => (
                            <li key={idx}>{warning}</li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Diagnosis */}
            <div className="bg-white p-6 rounded-xl shadow-md">
                <h2 className="text-2xl font-bold text-gray-800 mb-4">{String(analysis_result.machine_part || 'Unknown Part')}</h2>
                <div className="flex items-center text-gray-600 mb-6">
                    <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium mr-4">
                        {String(analysis_result.failure_type || 'Unknown Failure')}
                    </span>
                    <span className="flex items-center mr-4">
                        <Clock className="w-4 h-4 mr-1" /> {analysis_result.estimated_time_minutes || 0} mins
                    </span>
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                    <div>
                        <h3 className="font-semibold text-lg mb-3 flex items-center text-gray-700">
                            <Wrench className="mr-2 w-5 h-5" /> Required Tools
                        </h3>
                        <div className="flex flex-wrap gap-2">
                            {(Array.isArray(analysis_result.tools_required) ? analysis_result.tools_required : []).map((tool, i) => (
                                <span key={i} className="bg-gray-100 text-gray-700 px-3 py-1 rounded-md text-sm border">
                                    {String(tool)}
                                </span>
                            ))}
                        </div>
                    </div>

                    <div>
                         <div className="flex justify-between items-center mb-3">
                             <h3 className="font-semibold text-lg flex items-center text-gray-700">
                                <CheckCircle className="mr-2 w-5 h-5 text-green-600" /> Repair Checklist
                            </h3>
                            <span className="text-sm font-medium text-green-600 bg-green-50 px-2 py-1 rounded">
                                {progress}% Done
                            </span>
                        </div>
                        
                        <div className="h-2 w-full bg-gray-100 rounded-full mb-4 overflow-hidden">
                            <div 
                                className="h-full bg-green-500 transition-all duration-500"
                                style={{ width: `${progress}%` }}
                            />
                        </div>

                        <ul className="space-y-3">
                             {(Array.isArray(analysis_result.repair_steps) ? analysis_result.repair_steps : []).map((step, i) => (
                                <li 
                                    key={i} 
                                    className={`flex items-start p-3 rounded-lg border transition-all cursor-pointer ${
                                        checkedSteps[i] 
                                        ? 'bg-green-50 border-green-200 opacity-75' 
                                        : 'bg-white border-gray-100 hover:border-blue-200'
                                    }`}
                                    onClick={() => toggleStep(i)}
                                >
                                    <div className={`mt-0.5 mr-3 w-5 h-5 rounded border flex items-center justify-center flex-shrink-0 transition-colors ${
                                        checkedSteps[i] ? 'bg-green-500 border-green-500' : 'border-gray-300 bg-white'
                                    }`}>
                                        {checkedSteps[i] && <CheckCircle className="w-3.5 h-3.5 text-white" />}
                                    </div>
                                    <span className={`text-sm ${checkedSteps[i] ? 'text-gray-500 line-through' : 'text-gray-700'}`}>
                                        {String(step)}
                                    </span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            </div>

            {/* ROI Data */}
            <div className="bg-green-50 p-6 rounded-xl border border-green-100">
                 <h3 className="text-green-800 font-bold flex items-center mb-4 text-lg">
                    <DollarSign className="mr-2" /> Cost Efficiency Analysis
                </h3>
                <div className="grid grid-cols-3 gap-4 text-center">
                    <div className="bg-white p-3 rounded-lg shadow-sm">
                        <div className="text-sm text-gray-500">Traditional Time</div>
                        <div className="font-bold text-gray-800">{roi_data?.traditional_time_minutes || 0} mins</div>
                    </div>
                    <div className="bg-white p-3 rounded-lg shadow-sm">
                        <div className="text-sm text-gray-500">AI-Assisted Time</div>
                        <div className="font-bold text-blue-600">{roi_data?.ai_time_minutes || 0} mins</div>
                    </div>
                     <div className="bg-white p-3 rounded-lg shadow-sm border-l-4 border-green-500">
                        <div className="text-sm text-gray-500">Est. Savings</div>
                        <div className="font-bold text-green-600 text-xl">${roi_data?.savings_usd || 0}</div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AnalysisResult;

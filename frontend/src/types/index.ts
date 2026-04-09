export interface AgentState {
    image_path: string;
    query_text?: string;
    history_id?: number;
    retrieved_docs: RetrievedDoc[];
    analysis_result: AnalysisResult;
    safety_warnings: string[];
    roi_data: RoiData;
    erp_result?: ErpResult;
}

export interface RetrievedDoc {
    text: string;
    score: number;
    page?: number;
    source?: string;
    machine_type?: string;
}

export interface AnalysisResult {
    machine_part: string;
    failure_type: string;
    repair_steps: string[];
    tools_required: string[];
    estimated_time_minutes: number;
}

export interface RoiData {
    traditional_time_minutes: number;
    ai_time_minutes: number;
    savings_usd: number;
}

export interface ErpResult {
    ticket_id: string;
    status: string;
    system: string;
}


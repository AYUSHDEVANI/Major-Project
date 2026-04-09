from typing import TypedDict, List, Dict, Optional, Any

class AgentState(TypedDict):
    image_path: str
    query_text: Optional[str]
    company_id: Optional[int]
    retrieved_docs: List[Dict]
    analysis_result: Dict[str, Any]
    safety_warnings: List[str]
    roi_data: Dict[str, float]
    history_id: Optional[int]
    erp_result: Dict[str, Any]



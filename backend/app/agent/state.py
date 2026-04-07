from typing import TypedDict, List, Dict, Optional, Any

class AgentState(TypedDict):
    image_path: str
    query_text: Optional[str]
    retrieved_docs: List[Dict]
    analysis_result: Dict[str, Any]
    safety_warnings: List[str]
    roi_data: Dict[str, float]

from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.nodes import retrieve_node, generate_node, safety_node, roi_node, erp_node

def build_agent_graph():
    workflow = StateGraph(AgentState)
    
    # Nodes
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("generate", generate_node)
    workflow.add_node("safety", safety_node)
    workflow.add_node("roi", roi_node)
    workflow.add_node("erp", erp_node)
    
    # Edges
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", "safety")
    workflow.add_edge("safety", "roi")
    workflow.add_edge("roi", "erp")
    workflow.add_edge("erp", END)
    
    return workflow.compile()

agent_app = build_agent_graph()

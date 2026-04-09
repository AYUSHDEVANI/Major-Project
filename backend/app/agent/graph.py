from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.agent.state import AgentState
from app.agent.nodes import retrieve_node, generate_node, safety_node, roi_node, erp_node

# Additional fallback node definition (inline for simplicity, could be in nodes.py)
async def escalate_node(state: AgentState):
    print("--- ESCALATING TO HUMAN ---")
    return {"erp_result": {"status": "Escalated", "reason": "System unable to proceed automatically."}}

# Conditional Edge 1: Did retrieval find anything?
def check_retrieval(state: AgentState):
    if not state.get("retrieved_docs"):
        print("Conditional: No docs found, escalating.")
        return "escalate"
    return "generate"

# Conditional Edge 2: Is the generated plan safe/complete? (Simulation of checking)
def validate_repair(state: AgentState):
    analysis = state.get("analysis_result", {})
    # Very basic simulation: if LLM failed and returned the default error
    if "Analysis Failed" in analysis.get("failure_type", ""):
        print("Conditional: Analysis failed, escalating.")
        return "escalate"
    return "safety"

def build_agent_graph():
    workflow = StateGraph(AgentState)
    
    # Nodes
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("generate", generate_node)
    workflow.add_node("safety", safety_node)
    workflow.add_node("roi", roi_node)
    workflow.add_node("erp", erp_node)
    workflow.add_node("escalate", escalate_node)
    
    # Edges
    workflow.set_entry_point("retrieve")
    
    # After retrieval, branch conditionally
    workflow.add_conditional_edges(
        "retrieve",
        check_retrieval,
        {
            "generate": "generate",
            "escalate": "escalate"
        }
    )
    
    # After generation, validate the output
    workflow.add_conditional_edges(
        "generate",
        validate_repair,
        {
            "safety": "safety",
            "escalate": "escalate"
        }
    )
    
    # Main path continues
    workflow.add_edge("safety", "roi")
    workflow.add_edge("roi", "erp")
    
    # Terminate after terminal nodes
    workflow.add_edge("erp", END)
    workflow.add_edge("escalate", END)
    
    # Intialize memory checkpointer for Human-In-The-Loop
    memory = MemorySaver()
    
    # Compile with checkpointer and breakpoint
    return workflow.compile(
        checkpointer=memory,
        interrupt_before=["erp"] # Halt before creating SAP ticket
    )

agent_app = build_agent_graph()


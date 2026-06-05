from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.state import AgentState
from app.agents.nodes.planner import generate_plan as planner_node
from app.agents.nodes.retriever import retriever_node as retrieve_node
from app.agents.nodes.responder import generate_node

workflow = StateGraph(AgentState)

workflow.add_node("planner", planner_node)
workflow.add_node("retriever", retrieve_node)
workflow.add_node("responder", generate_node)


def route_planner_node(state: AgentState):
    plan = state["current_query"]
    if plan == "CONVERSATIONAL":
        return "responder"
    else:
        return "retriever"


workflow.set_entry_point("planner")

workflow.add_conditional_edges(
    "planner", route_planner_node, ["retriever", "responder"]
)
workflow.add_edge("retriever", "responder")
workflow.add_edge("responder", END)

checkpointer = MemorySaver()
rag_agent = workflow.compile(checkpointer=checkpointer)

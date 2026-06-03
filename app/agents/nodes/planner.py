from langchain_groq import ChatGroq
from app.agents.state import AgentState
from app.config import settings
import logfire


llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,  
    model=settings.GROQ_MODEL,
    temperature=0,   
)

def generate_plan(state: AgentState) -> dict:
    """
    The Planner determines if a search is needed based on the ENTIRE conversation.
    """

    history='' 
    for msg in state["message"][:-1]:
        role= "User" if msg['role'] == "user" else "Agent"
        history += f"{role}: {msg['content']}\n"
    
    user_message = state["message"][-1]["content"] if state["message"] else ""
    
    prompt = f"""
        You are an intelligent Assistant Planner. 
    Analyze the conversation history and the latest user message.
    CONVERSATION HISTORY:
    
    {history}
    
    LATEST USER MESSAGE:
    {user_message}
    
    Task:
    1. If the latest message is a greeting (hi, hello) or a question that can be answered using ONLY the conversation history above (e.g., "what is my name"), respond with 'CONVERSATIONAL'.
    2. If it is a technical question about Kubernetes, Intel, or Networking that requires fresh documentation, output a refined search query.
    
    Output ONLY 'CONVERSATIONAL' or the search query.
    
    """
    
    with logfire.span('Planning Decision'):
        
        decision = llm.invoke(prompt).content.strip()
        logfire.log("Intent Identified", decision=decision)
    if decision == "CONVERSATIONAL":
        return {
            "current_query":'CONVERSATIONAL',
            "plan": ["Intent: CONVERSATIONAL", "Retrieval: 'Skipped'"],
            "status":"ready_for_answering"
        }

        
    return {
        "current_query": decision,
        "plan": [f"Intent: SEARCH", f"Retrieval: '{decision}'"],
        "status":"ready_for_retrieval"
    }

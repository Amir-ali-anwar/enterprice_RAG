import logfire
from langchain_groq import ChatGroq

from app.agents.state import AgentState
from app.config import settings

llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_MODEL,
    temperature=0.1,
    max_retries=2,
)


def generate_node(state: AgentState):
    """
    Synthesizes a response using both Documentation Context AND Conversation History.
    """
    query = state["current_query"]
    logfire.info("Generating Response", query=query)

    history_str = ""

    for msg in state['messages'][-1]:
        role = "User" if msg['role'] == "user" else "Assistant"
        history_str += f"{role} : {msg['content']}\n"

    user_msg = state['messages'][-1]['content'] if state['messages'] else ''

    if query == "CONVERSATIONAL":
        logfire.info("Generating conversational response using memory.")

        prompt = f"""
        You are a friendly and helpful Enterprise AI Assistant.
        Answer the user's latest message using the CONVERSATION HISTORY below.
        
        CONVERSATION HISTORY:
        {history_str}
        
        LATEST MESSAGE:
        "{user_msg}"
        """
    else:
        logfire.info("Generating technical RAG response.")

        max_context_chars = 25000
        full_context = ""

        # Using documents (plural) as defined in AgentState
        documents = state.get("documents") or []
        for doc in documents:
            if len(full_context) + len(doc) < max_context_chars:
                full_context += doc + "\n\n"
            else:
                logfire.warning("Context truncated to fit Groq TPM limits.")
                break

        prompt = f"""
        You are a Senior Technical Architect. 
        Answer the question using the TECHNICAL CONTEXT provided. 
        
        TECHNICAL CONTEXT:
        {full_context}
        
        CONVERSATION HISTORY:
        {history_str}
        
        USER QUESTION:
        "{user_msg}"
        """

    try:
        with logfire.span("Generating response with Groq LLM"):
            response = llm.invoke(prompt)

        return {
            "messages": [{"role": "assistant", "content": response.content}],
            "status": "Response Generated",
        }
    except Exception as e:
        logfire.error("Error generating response with Groq LLM: {error}", error=e)
        return {"messages": [{"role": "assistant", "content": "I apologize, but I encountered an error while generating the response. Please try again."}], 
                "status": "Error"
        }
          

        
        
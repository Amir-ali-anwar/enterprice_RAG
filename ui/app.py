import os 
import streamlit as st
import requests 
import time
import uuid
import logfire
from dotenv import load_dotenv

env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env"))

load_dotenv(env_path)

try:
    token = os.getenv("LOGFIRE_TOKEN")
    if not token:
        print('ERROR: Token not found')
    
    logfire.configure(token=token)
    LOGFIRE_STATUS = "Connected & Tracing"

except Exception as e:
    print(f"Logfire Init Error in UI: {e}")
    LOGFIRE_STATUS = f"Error: {str(e)}"



st.set_page_config(
    page_title="Enterprise RAG",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)
    
AI_AVATAR = "🤖"
USER_AVATAR = "👤"

# --- SESSION MANAGEMENT ---

if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    logfire.info("New session created", session_id=st.session_state.session_id)

if 'messages' not in st.session_state:
    st.session_state.messages = []   


# --- SIDEBAR ---

with st.sidebar:
    st.title("Enterprise RAG")
    st.markdown("---")
    st.success(f"Logfire: {LOGFIRE_STATUS}")
    st.info(f'Memory ID: {st.session_state.session_id[:8]}')

    if st.button("Clear History"):
        logfire.warn(f"🗑️ Memory Wipe Triggered for session: {st.session_state.session_id}")
        st.session_state.messages = []
        st.rerun() 

# --- MAIN CHAT ---
st.title("🤖 Enterprise Agentic Assistant")

# Custom CSS styling for premium look & feel
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Sidebar styled element */
    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Render existing chat messages
for message in st.session_state.messages:
    avatar = AI_AVATAR if message["role"] == "assistant" else USER_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Chat Input

if prompt := st.chat_input("Ask a technical question about enterprise documents..."):

# START TRACE: User Interaction
    
    with logfire.span("💬 User Chat Interaction", user_query=prompt, session_id=st.session_state.session_id):
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar=AI_AVATAR):
            with st.status("Thinking...", expanded=True) as status:

                try:

                    with logfire.span("📡 Calling RAG Backend"):
                        base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
                        url = f"{base_url}/query"
                        payload = {"query": prompt, "thread_id": st.session_state.session_id}
                        response = requests.post(url, json=payload, timeout=50)
                        data= response.json()

                    # show reasoning steps from backend

                    steps = data.get('thought_process',[])
                    for step in steps:
                        st.write(f"⚙️ {step}")

                    status.update(label="✅ Answer Synthesized", state="complete", expanded=False)

                    # --- SHOW SOURCES (NESTED EXPANDABLES) ---

                    sources = data.get('sources',[])

                    if sources:
                        with st.expander("📚 Sources"):
                            for i,src in enumerate(sources):
                                 # Create a preview title for each chunk
                                 preview = src[:100].replace("\n", " ") + "..."
                                 with st.expander(f"chunk {i+1}:{preview}"):
                                    st.info(src)
                except Exception as e:
                    logfire.error(f"❌ UI-Backend Connection Failed: {e}")
                    status.update(label="❌ Connection Failed", state="error")
                    st.error("Backend Connection Failed ")
                    st.stop()


        # Final placeholder                    

        answer_placeholder = st.empty()
        full_answer = data.get("answer", "No Response")
        print('answer', full_answer)
        curr_text=''

        for char in full_answer:
            curr_text += char
            answer_placeholder.markdown(curr_text)
            time.sleep(0.02)
        answer_placeholder.markdown(full_answer)
        st.session_state.messages.append({"role": "assistant", "content": full_answer})
        logfire.info("✅ Answer displayed to user", 
                      user_query=prompt, 
                      session_id=st.session_state.session_id,
                      answer=full_answer[:500])

                                    


                
                        
                
            
            
        




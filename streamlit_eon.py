import streamlit as st
import hashlib
import ollama
import requests
from memory_manager import EONMemoryManager
from personality import Personality

st.set_page_config(page_title="EON AI Assistant", layout="wide", initial_sidebar_state="expanded")
# ----- Custom CSS for a modern/3D look with subtle 3D animations -----
custom_css = """
<style>
/* Sidebar styling */
.sidebar .sidebar-content {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 8px;
}

/* Chat message styling with slight 3D effect */
.chat-message {
    padding: 0.75rem;
    margin-bottom: 0.75rem;
    border-radius: 8px;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
}
.chat-message.you {
    background-color: grey;
}
.chat-message.eon {
    background-color: black;
}

/* Expander styling */
div.stExpander > div > div > div {
    background-color: #ffffff;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 0.5rem;
}

/* Button animations */
.stButton > button {
    transition: all 0.3s ease;
}
.stButton > button:hover {
    transform: scale(1.05);
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ----- Helper Functions -----
def generate_memory_title(user_message):
    """Generate a title from the first user message."""
    return user_message[:50] + "..." if len(user_message) > 50 else user_message

def formulate_response(memories, user_input, personality_traits):
    if memories:
        combined_memory = " ".join(memories)
        prompt = (
            f"Personality traits: {personality_traits}\n"
            f"Based on what I remember: {combined_memory}\n"
            f"Now, in response to your query: {user_input}"
        )
    else:
        prompt = f"Personality traits: {personality_traits}\nUser: {user_input}"
    try:
        response = ollama.chat(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]
    except Exception as e:
        return f"Error obtaining response: {e}"

def perform_search(query):
    """Simulated search function using DuckDuckGo Instant Answer API."""
    try:
        url = "https://www.google.com/"
        params = {"q": query, "format": "json"}
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            data = res.json()
            abstract = data.get("Abstract", "No results found.")
            return abstract
        else:
            return "Search error."
    except Exception as e:
        return f"Search error: {e}"

# ----- Main App -----
def main():
    st.title("EON AI Assistant 🤖")
    
    # ----- Sidebar: Settings & Tools -----
    st.sidebar.header("Settings & Tools")
    
    # Personality Tone
    personality_tone = st.sidebar.selectbox("Select Personality Tone", ["Bro", "Professional", "Casual"])
    
    # Personality Option (Reasoning Intensity)
    reasoning_intensity = st.sidebar.slider("Reasoning Intensity", min_value=0, max_value=10, value=5)
    
    # New Chat Button
    if st.sidebar.button("🆕 New Chat"):
        st.session_state.chat_history = []
        st.session_state.response_history = []
        st.session_state.saved_conversations = {}
        st.success("New chat created!")
        st.rerun()
    
    # Search Functionality
    st.sidebar.markdown("### Internet Search")
    search_query = st.sidebar.text_input("Search the web:")
    if st.sidebar.button("Search") and search_query:
        search_results = perform_search(search_query)
        st.sidebar.markdown(f"**Results:** {search_results}")
    
    # Memory Viewer in Sidebar (Saved Conversations)
    st.sidebar.markdown("### Saved Conversations")
    memory_manager = EONMemoryManager(db_path="adaptive_memory/eon_memory.json")
    conversation_log = memory_manager.memory.get("conversation_log", [])
    if conversation_log:
        for idx, entry in enumerate(conversation_log, start=1):
            title = generate_memory_title(entry.get("user", "Conversation"))
            with st.sidebar.expander(f"Conversation {idx}: {title}"):
                st.markdown(f"**You:** {entry.get('user', '')}")
                st.markdown(f"**EON:** {entry.get('eon', '')}")
    else:
        st.sidebar.write("No saved conversations yet.")
    
    st.sidebar.markdown("### Effects & Animations")
    use_animations = st.sidebar.checkbox("Enable Animations", value=True)
    
    # ----- Main Chat and Detailed Response Area -----
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "response_history" not in st.session_state:
        st.session_state.response_history = []
    if "saved_conversations" not in st.session_state:
        st.session_state.saved_conversations = {}
    
    # Initialize Personality (using local traits file)
    personality = Personality(personality_file="memory/traits.json")
    
    # Create two tabs: Chat and Detailed Response
    chat_tab, response_tab = st.tabs(["Chat", "Detailed Response"])
    
    with chat_tab:
        st.header("💬 Chat Interface")
        user_input = st.text_input("You:", key="chat_input")
        if st.button("Send") and user_input:
            with st.spinner("Generating response..."):
                # Retrieve memories and personality traits
                memories = memory_manager.retrieve_memory(user_input, top_k=3)
                traits = personality.get_traits()
                if personality_tone == "Bro":
                    traits_str = ", ".join([k for k, v in traits.items() if v])
                elif personality_tone == "Professional":
                    traits_str = "professional, analytical, courteous"
                else:
                    traits_str = "casual, friendly"
                
                # Incorporate reasoning intensity into traits description
                traits_str += f" (reasoning intensity: {reasoning_intensity})"
                
                # Generate response from EON
                response = formulate_response(memories, user_input, traits_str)
                
                st.session_state.chat_history.append(("You", user_input))
                st.session_state.chat_history.append(("EON", response))
                st.session_state.response_history.append(response)
                
                # Save conversation as a new conversation block
                memory_id = "memory_" + hashlib.sha256(user_input.encode()).hexdigest()
                if memory_id not in st.session_state.saved_conversations:
                    st.session_state.saved_conversations[memory_id] = []
                st.session_state.saved_conversations[memory_id].append(("You", user_input))
                st.session_state.saved_conversations[memory_id].append(("EON", response))
                
                memory_manager.add_memory(user_input, memory_id)
                memory_manager.summarize_memory_if_needed()
                
                if use_animations:
                    st.balloons()
                if hasattr(st, "rerun"):
                    st.rerun()
        st.subheader("Conversation")
        for speaker, message in st.session_state.chat_history:
            css_class = "you" if speaker == "You" else "eon"
            st.markdown(f"<div class='chat-message {css_class}'><strong>{speaker}:</strong> {message}</div>", unsafe_allow_html=True)
    
    with response_tab:
        st.header("📜 Detailed EON Response")
        if st.session_state.response_history:
            last_response = st.session_state.response_history[-1]
            st.markdown(f"**Latest Response:**\n\n{last_response}")
        else:
            st.write("No detailed responses yet.")

if __name__ == "__main__":
    main()

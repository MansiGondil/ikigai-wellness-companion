import streamlit as st
from backend import wellness_chat, generate_meme_image, reset_attack_memory

# ================================
# 🌿 Page Configuration
# ================================
st.set_page_config(
    page_title="Mental Wellness Companion",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================================
# 🎨 Custom CSS – Removes ALL White Space
# ================================
st.markdown("""
<style>

html, body, .stApp {
    padding: 0 !important;
    margin: 0 !important;
    background-color: #B4E2EB !important;
}

/* Remove blank padding at top */
.main > div:first-child {
    padding-top: 0 !important;
    margin-top: -35px !important;
}

/* Remove excessive padding between elements */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
}

/* Reduce spacing after divider */
hr {
    margin-top: 0.5rem !important;
    margin-bottom: 0.5rem !important;
}

/* Chat container */
.chat-container {
    display: flex;
    flex-direction: column;
    background-color: transparent;
    padding: 0;
    max-height: 480px;
    overflow-y: auto;
    border-radius: 12px;
    margin-top: 0 !important;
}

/* User bubble */
.chat-bubble-user {
    align-self: flex-end;
    background-color: #00974C;
    padding: 12px 16px;
    border-radius: 15px;
    margin: 6px 0;
    max-width: 80%;
    font-size: 16px;
    color: #e8f5e9;
}

/* Bot bubble */
.chat-bubble-bot {
    align-self: flex-start;
    background-color: #00974C;
    padding: 12px 16px;
    border-radius: 15px;
    margin: 6px 0;
    max-width: 80%;
    font-size: 16px;
    color: #e8f5e9;
}

/* Remove extra spacing around Markdown blocks */
div[data-testid="stMarkdownContainer"] {
    margin-top: 0 !important;
    margin-bottom: 0.5rem !important;
}

/* Reduce spacing around text inputs */
div[data-testid="stVerticalBlock"] > div {
    gap: 0.5rem !important;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background-color: #5D696F !important;
    color: #ffffff !important;
}
section[data-testid="stSidebar"] .css-1d391kg,
div[data-testid="stSidebar"] {
    background-color: transparent !important;
}
section[data-testid="stSidebar"] .stSidebarHeader, 
section[data-testid="stSidebar"] h1, 
section[data-testid="stSidebar"] h2, 
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] a {
    color: #ffffff !important;
}


</style>
""", unsafe_allow_html=True)


# ================================
# 🌿 Sidebar – Clear Conversation Button
# ================================
st.sidebar.header(" Mental Wellness Companion")

if st.sidebar.button("🔄 Start New Conversation", type="primary"):
    st.session_state.messages = []
    st.session_state.chat_history = []
    reset_attack_memory()  # Reset security tracking
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("Your mental wellness companion powered by AI")


# ================================
# 🌱 Main App Header
# ================================
st.markdown(
    '<img src="https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExeW44b3NiZGxqZnZ2Y3h3MWplbnEwY3Q0bDVmZ241Z2wxaWEwNWhicSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/x4YhPygegeOPbFrwIQ/giphy.gif" style="width: 100%; max-width: 600px; display: block; margin: 0 auto;">',
    unsafe_allow_html=True
)

st.markdown("<h3 style='color: #000000;'>🌼 Today's Affirmation</h3>", unsafe_allow_html=True)
st.markdown(
    '<div style="background-color: #FAF0DA; padding: 12px; border-radius: 8px; color: #000;">'
    "You are allowed to pause, breathe, and take things one step at a time."
    "</div>",
    unsafe_allow_html=True,
)
st.divider()


# ================================
# 💬 Chat Initialization
# ================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Initialize survey values in session state
if "survey_mood" not in st.session_state:
    st.session_state.survey_mood = 5
if "survey_stress" not in st.session_state:
    st.session_state.survey_stress = 5
if "survey_sleep" not in st.session_state:
    st.session_state.survey_sleep = 7
if "survey_energy" not in st.session_state:
    st.session_state.survey_energy = 5
if "survey_social" not in st.session_state:
    st.session_state.survey_social = "Prefer not to say"
if "use_survey" not in st.session_state:
    st.session_state.use_survey = True
if "show_survey" not in st.session_state:
    st.session_state.show_survey = False

# Flag to clear the input textbox safely (set before widget creation)
if "clear_input" not in st.session_state:
    st.session_state.clear_input = False


# ================================
# Helper: Convert URLs to clickable hyperlinks
# ================================
import re

def make_links_clickable(text):
    """Convert URLs in text to clickable HTML hyperlinks."""
    url_pattern = r'(https?://[^\s<>"\']+)'
    return re.sub(url_pattern, r'<a href="\1" target="_blank" style="color: #F9C8CD; text-decoration: underline;">\1</a>', text)


# ================================
# 💬 Chat Display
# ================================
if st.session_state.messages:
    chat_html = '<div class="chat-container">'
    
    for msg, role in st.session_state.messages:
        if role == "user":
            chat_html += f'<div class="chat-bubble-user">{msg}</div>'
        else:
            msg_with_links = make_links_clickable(msg)
            chat_html += f'<div class="chat-bubble-bot">{msg_with_links}</div>'
    
    chat_html += '</div>'
    
    st.markdown(chat_html, unsafe_allow_html=True)

else:
    st.markdown("<p style='color: #000000; font-size: 14px; opacity: 0.8;'>✨ Say something to begin the conversation…</p>", unsafe_allow_html=True)


# ================================
# Helper: Build survey context
# ================================
def build_survey_context():
    return (
        f"[Context - mood: {st.session_state.survey_mood}/10, "
        f"stress: {st.session_state.survey_stress}/10, "
        f"sleep: {st.session_state.survey_sleep}h, "
        f"energy: {st.session_state.survey_energy}/10, "
        f"social: {st.session_state.survey_social.lower()}]\n\n"
    )


# ================================
# User Input
# ================================
# If requested, clear the input value before creating the widget
if st.session_state.get("clear_input", False):
    st.session_state["input_box"] = ""
    st.session_state["clear_input"] = False

user_input = st.text_area(
    "Your message",
    placeholder="What's on your mind today?",
    height=110,
    key="input_box",
    label_visibility="collapsed"
)

col1, col2, col3 = st.columns([4, 1, 2])

with col1:
    send_button = st.button("Send", type="primary", key="send_button", use_container_width=True)

# (Clear button removed)

with col3:
    survey_button = st.button("📋 Take Survey", key="survey_button", use_container_width=True)

# Clear button handler removed

if survey_button:
    st.session_state.show_survey = not st.session_state.show_survey
    st.rerun()


# ================================
# 🌿 Survey Dropdown (Expandable)
# ================================
if st.session_state.show_survey:
    with st.expander("🌿 Mini Wellness Survey", expanded=True):
        st.write("Helps personalize responses. You may skip anytime.")
        
        st.session_state.survey_mood = st.slider("Mood (1–10)", 1, 10, st.session_state.survey_mood, key="mood_slider")
        st.session_state.survey_stress = st.slider("Stress (1–10)", 1, 10, st.session_state.survey_stress, key="stress_slider")
        st.session_state.survey_sleep = st.number_input("Sleep (hours)", min_value=0, max_value=24, value=st.session_state.survey_sleep, key="sleep_input")
        st.session_state.survey_energy = st.slider("Energy (1–10)", 1, 10, st.session_state.survey_energy, key="energy_slider")
        st.session_state.survey_social = st.selectbox("Social State", ["Alone", "With family", "With friends", "Prefer not to say"], 
                                                       index=["Alone", "With family", "With friends", "Prefer not to say"].index(st.session_state.survey_social),
                                                       key="social_select")
        
        st.session_state.use_survey = st.checkbox("Use survey in responses", value=st.session_state.use_survey, key="use_survey_checkbox")
        
        st.caption("Chat works normally even if you skip the survey.")


# ================================
# 🚀 Handle Send
# ================================
if send_button and user_input.strip():

    # Add user message to UI chat
    st.session_state.messages.append((user_input, "user"))

    # Prepare survey data to pass to the model
    survey_data = {
        "use_survey": st.session_state.use_survey,
        "mood": st.session_state.survey_mood,
        "stress": st.session_state.survey_stress,
        "sleep": st.session_state.survey_sleep,
        "energy": st.session_state.survey_energy,
        "social": st.session_state.survey_social,
    }

    # Get bot response WITH CONVERSATION HISTORY AND SURVEY DATA
    with st.spinner("Responding with care..."):
        intent, reply, crisis, updated_history = wellness_chat(
            user_input,
            st.session_state.chat_history,
            survey_data
        )

    # Update the LangChain chat history
    st.session_state.chat_history = updated_history

    # Add bot reply to UI chat
    st.session_state.messages.append((reply, "bot"))

    # Request a clear of the input box on the next run (safe: before widget creation)
    st.session_state.clear_input = True

    if crisis:
        st.error(
            "💛 Your message shows signs of severe distress. "
            "Please reach out to someone you trust or contact a hotline immediately."
        )

    # Show conversation stats in sidebar
    st.sidebar.markdown("---")
    st.sidebar.caption(f"💬 Messages in conversation: {len(st.session_state.messages)}")
    st.sidebar.caption(f"🔍 Detected intent: {intent}")

    st.rerun()


# ================================
# 🎭 Meme Generator
# ================================
st.markdown("---")
meme_button = st.button("Generate Meme Based on My Mood 😄", use_container_width=True)

if meme_button:
    with st.spinner("Creating a funny mood-based meme..."):
        prompt = (
            f"The user feels {st.session_state.survey_mood}/10 mood and {st.session_state.survey_stress}/10 stress. "
            f"Generate a wholesome, funny meme that could uplift them."
        )

        meme_path = generate_meme_image(prompt)

    if meme_path.startswith("ERROR"):
        st.error(meme_path)
    else:
        st.image(meme_path, caption="Here's your mood-based meme 💚", use_container_width=True)


# ================================
# Footer
# ================================
st.markdown("---")
st.markdown("<p style='color: #000000; font-size: 14px; opacity: 0.8;'>Built with 💚 using your fine-tuned model + DALL·E + Streamlit.</p>", unsafe_allow_html=True)
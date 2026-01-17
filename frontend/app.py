import streamlit as st
import requests
import uuid

# ---------------- CONFIG ----------------
API_URL = "http://api_gateway:8000/api/chat"  # docker
# API_URL = "http://localhost:8000/api/chat" # local run

st.set_page_config(
    page_title="AI Agriculture Assistant",
    page_icon="🌾",
    layout="centered",
)

# ---------------- THEME ----------------
st.markdown("""
<style>
body {
    background-color: #0e1117;
    color: white;
}
.chat-user {
    background-color: #1f2937;
    padding: 10px;
    border-radius: 8px;
    margin-bottom: 5px;
}
.chat-bot {
    background-color: #065f46;
    padding: 10px;
    border-radius: 8px;
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- STATE ----------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "chat" not in st.session_state:
    st.session_state.chat = []

# ---------------- UI ----------------
st.title("🧑‍🌾 AI Agriculture Assistant")
st.caption("Hindi / Hinglish • Backend Powered")

user_input = st.text_input(
    "🌱 Apna sawal likhein (jaise: gehu ke liye khaad)",
    placeholder="gehu ke liye khaad"
)

send = st.button("Send")

# ---------------- ACTION ----------------
if send and user_input.strip():
    payload = {
        "session_id": st.session_state.session_id,
        "message": user_input
    }

    try:
        res = requests.post(API_URL, json=payload, timeout=20)
        res.raise_for_status()
        data = res.json()
        reply = data.get("reply", "Kuch galat ho gaya")

    except Exception as e:
        reply = f"❌ Backend error: {e}"

    st.session_state.chat.append(("user", user_input))
    st.session_state.chat.append(("bot", reply))

# ---------------- CHAT DISPLAY ----------------
st.divider()
for role, msg in st.session_state.chat:
    if role == "user":
        st.markdown(f"<div class='chat-user'>🧑‍🌾 <b>You:</b><br>{msg}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-bot'>🌾 <b>AI:</b><br>{msg}</div>", unsafe_allow_html=True)
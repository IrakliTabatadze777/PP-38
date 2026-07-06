import streamlit as st

st.title("Simple AI Chat Demo")

# "AI brain" - just a dict mapping keywords to responses
responses = {
    "hello": "Hi there! How can I help you today?",
    "how are you": "I'm just code, but I'm doing great!",
    "streamlit": "Streamlit makes building web apps in Python super easy.",
    "bye": "Goodbye! Have a great day.",
}
default_response = "Sorry, I don't understand. Try: hello, how are you, streamlit, bye."

# all chats live in one dict: {chat_name: [list of messages]}
if "chats" not in st.session_state:
    st.session_state.chats = {"Chat 1": []}

if "current_chat" not in st.session_state:
    st.session_state.current_chat = "Chat 1"

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("Saved Chats")

    if st.button("+ New Chat"):
        new_name = f"Chat {len(st.session_state.chats) + 1}"
        st.session_state.chats[new_name] = []
        st.session_state.current_chat = new_name

    # list existing chats as selectable buttons
    for chat_name in st.session_state.chats:
        if st.button(chat_name, key=f"select_{chat_name}"):
            st.session_state.current_chat = chat_name

# ---------------- Main chat area ----------------
current = st.session_state.current_chat
st.subheader(current)

messages = st.session_state.chats[current]

# show past messages for the selected chat
for msg in messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# chat input box
user_input = st.chat_input("Type a message...")

if user_input:
    # show user message
    messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # pick a response from the dict (simple keyword match)
    reply = default_response
    for key, value in responses.items():
        if key in user_input.lower():
            reply = value
            break

    # show assistant message
    messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.write(reply)
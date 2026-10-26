import streamlit as st

import client
import config
import ui

EXAMPLES = [
    "Can I return boots I wore once?",
    "Order 1042 arrived with a broken zipper and I want my money back.",
    "Order 1049 arrived with a snapped tent pole and I want a refund.",
    "I'd like to talk to a real person.",
]
WELCOME = (
    "Hi, I'm the customer support assistant. "
    "I can help with orders, returns, refunds and gear care."
)
ROLE_FOR = {"customer": "user", "assistant": "assistant"}


def reset_conversation() -> None:
    st.session_state.thread_id = None
    st.session_state.messages = []
    st.session_state.awaiting = False
    st.query_params.pop("thread", None)


def load_thread(thread_id: str) -> bool:
    try:
        thread = client.get_thread(thread_id, ui.token())
    except client.ApiError as error:
        if error.code == "thread_not_found":
            return False
        ui.show_error(error)
        return True
    st.session_state.thread_id = thread_id
    st.session_state.messages = [
        {"role": ROLE_FOR[m["role"]], "content": m["content"]} for m in thread["messages"]
    ]
    st.session_state.awaiting = thread["status"] == "awaiting_approval"
    return True


def init_state() -> None:
    if "messages" in st.session_state:
        return
    reset_conversation()
    saved = st.query_params.get("thread")
    if saved and not load_thread(saved):
        st.query_params.pop("thread", None)


def open_conversation(thread_id: str) -> None:
    reset_conversation()
    st.session_state.thread_id = thread_id
    if load_thread(thread_id):
        st.query_params["thread"] = thread_id
    else:
        reset_conversation()


def past_conversations() -> list[dict]:
    try:
        return client.list_threads(ui.token())
    except client.ApiError as error:
        ui.check_session(error)
        return []


def queue_example(text: str) -> None:
    st.session_state.queued_prompt = text


def sidebar() -> None:
    with st.sidebar:
        st.button(
            "New conversation",
            icon=":material/add:",
            on_click=reset_conversation,
            use_container_width=True,
        )
        st.subheader("Conversations")
        for entry in past_conversations():
            current = entry["thread_id"] == st.session_state.thread_id
            st.button(
                entry["title"],
                key=f"history-{entry['thread_id']}",
                on_click=open_conversation,
                args=(entry["thread_id"],),
                type="primary" if current else "secondary",
                icon=":material/chat_bubble:",
                use_container_width=True,
            )
        with st.expander("Try an example"):
            st.caption("The demo orders belong to customer@example.com.")
            for text in EXAMPLES:
                st.button(
                    text,
                    key=f"example-{text}",
                    on_click=queue_example,
                    args=(text,),
                    disabled=st.session_state.awaiting,
                    use_container_width=True,
                )
    ui.backend_status()


@st.fragment(run_every=config.THREAD_POLL_SECONDS)
def wait_for_decision() -> None:
    thread_id = st.session_state.thread_id
    try:
        status = client.get_thread(thread_id, ui.token())["status"]
    except client.ApiError as error:
        ui.check_session(error)
        status = "awaiting_approval"
    if status != "awaiting_approval":
        load_thread(thread_id)
        st.rerun()
    st.info(
        "Your request is with our team for review. This page updates by itself "
        "when there is a decision.",
        icon="⏳",
    )


def send(prompt: str) -> None:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    text, failed = "", False
    with st.chat_message("assistant"):
        activity = st.empty()
        answer = st.empty()
        activity.caption("Thinking…")
        try:
            for event in client.stream_chat(prompt, st.session_state.thread_id, ui.token()):
                if event.event == "thread":
                    st.session_state.thread_id = event.data["thread_id"]
                    st.query_params["thread"] = event.data["thread_id"]
                elif event.event == "token":
                    text += event.data.get("text", "")
                    answer.markdown(text + "▌")
                elif event.event == "tool_call":
                    activity.caption(f"{event.data.get('name', 'Working')}…")
                elif event.event == "awaiting_approval":
                    st.session_state.awaiting = True
                elif event.event == "error":
                    failed = True
                    st.error(event.data.get("message", "Something went wrong. Please try again."))
        except client.ApiError as error:
            failed = True
            if error.code == "thread_awaiting_approval":
                st.session_state.awaiting = True
            elif error.code == "thread_not_found":
                reset_conversation()
            ui.show_error(error)
        activity.empty()
        answer.markdown(text)
    if text:
        st.session_state.messages.append({"role": "assistant", "content": text})
    if st.session_state.awaiting or not failed:
        st.rerun()


ui.require_token()
init_state()
sidebar()

st.title("Customer Support Agent")
st.caption("Ask about an order, a return, a refund, or our gear policies.")

with st.chat_message("assistant"):
    st.markdown(WELCOME)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if st.session_state.awaiting:
    wait_for_decision()

prompt = st.chat_input(
    "Your request is under review" if st.session_state.awaiting else "Type your message",
    disabled=st.session_state.awaiting,
    max_chars=2000,
)
prompt = prompt or st.session_state.pop("queued_prompt", None)
if prompt:
    send(prompt)

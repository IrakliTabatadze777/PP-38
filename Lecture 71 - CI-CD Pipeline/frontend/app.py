import streamlit as st

import ui

st.set_page_config(page_title="Customer Support Agent", page_icon="🏔️")

PAGES_BY_ROLE = {
    "customer": [
        st.Page("views/chat.py", title="Support chat", icon=":material/chat:", default=True)
    ],
    "reviewer": [
        st.Page("views/reviewer.py", title="Approval queue", icon=":material/fact_check:")
    ],
    "admin": [st.Page("views/documents.py", title="Knowledge base", icon=":material/menu_book:")],
}

if not ui.token():
    pages = [st.Page("views/login.py", title="Sign in", icon=":material/login:")]
elif ui.user().get("role") in PAGES_BY_ROLE:
    pages = PAGES_BY_ROLE[ui.user()["role"]]
else:
    ui.sign_out("This account has no page in the UI.")
    st.stop()

navigation = st.navigation(pages, position="sidebar" if ui.token() else "hidden")
if ui.token():
    with st.sidebar:
        user = ui.user()
        st.caption(f"Signed in as **{user['name']}** ({user['role']})")
        if st.button("Sign out", icon=":material/logout:", key="sign_out"):
            ui.sign_out()
navigation.run()

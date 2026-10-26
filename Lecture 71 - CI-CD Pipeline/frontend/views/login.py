import streamlit as st

import client
import ui

MIN_PASSWORD_LENGTH = 8

st.title("Customer Support Agent")
st.caption("Sign in to chat with the assistant, review requests or manage the knowledge base.")

if notice := st.session_state.pop("login_notice", None):
    st.warning(notice)

sign_in_tab, sign_up_tab = st.tabs(["Sign in", "Create account"])

with sign_in_tab, st.form("login"):
    email = st.text_input("Email", key="login_email", autocomplete="username")
    password = st.text_input(
        "Password", type="password", key="login_password", autocomplete="current-password"
    )
    submitted = st.form_submit_button("Sign in", type="primary")

with sign_up_tab, st.form("register"):
    st.caption("New accounts are customer accounts.")
    new_name = st.text_input("Name", key="register_name", autocomplete="name")
    new_email = st.text_input("Email", key="register_email", autocomplete="email")
    new_password = st.text_input(
        "Password",
        type="password",
        key="register_password",
        autocomplete="new-password",
        help=f"At least {MIN_PASSWORD_LENGTH} characters.",
    )
    confirm = st.text_input(
        "Repeat password",
        type="password",
        key="register_confirm",
        autocomplete="new-password",
    )
    registered = st.form_submit_button("Create account", type="primary")

if submitted:
    if not email.strip() or not password:
        sign_in_tab.warning("Enter your email and password.")
    else:
        try:
            session = client.login(email.strip(), password)
        except client.ApiError as error:
            sign_in_tab.error(error.message)
        else:
            ui.sign_in(session)
            st.rerun()

if registered:
    if not new_name.strip() or not new_email.strip() or not new_password:
        sign_up_tab.warning("Fill in your name, email and password.")
    elif len(new_password) < MIN_PASSWORD_LENGTH:
        sign_up_tab.warning(f"Use a password of at least {MIN_PASSWORD_LENGTH} characters.")
    elif new_password != confirm:
        sign_up_tab.warning("The two passwords are not the same.")
    else:
        try:
            session = client.register(new_name.strip(), new_email.strip(), new_password)
        except client.ApiError as error:
            sign_up_tab.error(error.message)
        else:
            ui.sign_in(session)
            st.rerun()
ui.backend_status()

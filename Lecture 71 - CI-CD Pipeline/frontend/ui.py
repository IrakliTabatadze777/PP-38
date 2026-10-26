import time

import streamlit as st

import client
import config


def usd(cents: int | None) -> str:
    if cents is None:
        return "n/a"
    sign = "-" if cents < 0 else ""
    dollars, remainder = divmod(abs(cents), 100)
    return f"{sign}${dollars:,}.{remainder:02d}"


REFRESH_MARGIN_SECONDS = 30


def token() -> str:
    _renew_if_due()
    return st.session_state.get("token", "")


def user() -> dict[str, str]:
    return st.session_state.get("user", {})


def sign_in(session: dict) -> None:
    st.session_state["token"] = session["access_token"]
    st.session_state["user"] = session["user"]
    st.session_state["refresh_token"] = session.get("refresh_token", "")
    expires_in = session.get("expires_in")
    st.session_state["token_expires_at"] = time.time() + expires_in if expires_in else None
    st.session_state.pop("login_notice", None)


def _renew_if_due() -> None:
    state = st.session_state
    expires_at = state.get("token_expires_at")
    if not state.get("token") or not state.get("refresh_token") or expires_at is None:
        return
    if time.time() < expires_at - REFRESH_MARGIN_SECONDS:
        return
    try:
        renewed = client.refresh(state["refresh_token"])
    except client.ApiError as error:
        if error.code in (client.INVALID_REFRESH_TOKEN, client.NOT_AUTHENTICATED):
            sign_out("Your session has ended. Please sign in again.")
        return
    sign_in(renewed)


def sign_out(notice: str | None = None) -> None:
    refresh_token = st.session_state.get("refresh_token")
    if refresh_token:
        try:
            client.logout(refresh_token)
        except client.ApiError:
            pass
    st.session_state.clear()
    if notice:
        st.session_state["login_notice"] = notice
    else:
        st.query_params.clear()
    st.rerun()


def check_session(error: client.ApiError) -> None:
    if error.code == client.NOT_AUTHENTICATED:
        sign_out("Your session has ended. Please sign in again.")


def show_error(error: client.ApiError) -> None:
    check_session(error)
    st.error(error.message)


def require_token() -> str:
    if not token():
        st.info("Please sign in first.")
        st.stop()
    return token()


def backend_status() -> None:
    with st.sidebar:
        st.divider()
        if client.health():
            st.caption(f"🟢 Connected to {config.API_URL}")
        else:
            st.caption(f"🔴 Cannot reach {config.API_URL}")

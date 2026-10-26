import streamlit as st

import client
import ui

FRONT_MATTER = """---
title: Gift cards
category: policy
last_updated: 2026-01-15
---
# Gift cards
..."""


def show_flash() -> None:
    if "documents_flash" in st.session_state:
        kind, message = st.session_state.pop("documents_flash")
        (st.success if kind == "success" else st.error)(message)


def delete(token: str, source: str) -> None:
    try:
        client.delete_document(token, source)
    except client.ApiError as error:
        ui.check_session(error)
        st.session_state.documents_flash = ("error", error.message)
    else:
        st.session_state.documents_flash = ("success", f"Removed {source}.")
    st.rerun()


def upload_form(token: str) -> None:
    generation = st.session_state.get("upload_generation", 0)
    with st.container(border=True):
        st.subheader("Add or replace a document")
        file = st.file_uploader(
            "Markdown or text file (up to 200 KB)",
            type=["md", "txt"],
            key=f"upload-{generation}",
        )
        st.caption("A file with the same name replaces the existing one. It must start with:")
        st.code(FRONT_MATTER, language="markdown")
        if file and st.button("Upload and ingest", type="primary"):
            with st.spinner("Ingesting…"):
                try:
                    done = client.upload_document(token, file.name, file.getvalue())
                except client.ApiError as error:
                    ui.show_error(error)
                    return
            st.session_state.upload_generation = generation + 1
            st.session_state.documents_flash = (
                "success",
                f"Ingested {done['source']} as {done['chunks']} chunks.",
            )
            st.rerun()


token = ui.require_token()
ui.backend_status()

st.title("Knowledge base")
st.caption("The policy documents the assistant searches before it answers.")
show_flash()
try:
    documents = client.list_documents(token)
except client.ApiError as error:
    ui.show_error(error)
    st.stop()

if not documents:
    st.info("No documents are ingested yet.")
for document in documents:
    name, chunks, action = st.columns([5, 2, 2], vertical_alignment="center")
    name.markdown(f"**{document['source']}**")
    chunks.caption(f"{document['chunks']} chunks")
    with action.popover("Delete", icon=":material/delete:"):
        st.write(f"Remove {document['source']} from the knowledge base?")
        if st.button("Yes, delete", key=f"delete-{document['source']}", type="primary"):
            delete(token, document["source"])

upload_form(token)

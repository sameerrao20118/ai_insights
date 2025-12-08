import datetime as dt
from typing import Optional

import streamlit as st

from storage.vector_db_manager import VectorDBManager


def get_vdb() -> Optional[VectorDBManager]:
    """Return a cached VectorDBManager instance with user-friendly error handling."""
    if "vdb" in st.session_state:
        return st.session_state["vdb"]

    try:
        st.session_state["vdb"] = VectorDBManager()
    except Exception as exc:  # noqa: BLE001 - surface config errors clearly in UI
        st.session_state["vdb_error"] = str(exc)
        st.error(
            "Vector store is not ready. Check that your OpenAI credentials and Chroma path are configured."
        )
        st.caption(str(exc))
        return None

    return st.session_state["vdb"]


def record_ingest(count: int) -> None:
    """Remember the last ingest details for display in the UI."""
    st.session_state["last_ingest_count"] = count
    st.session_state["last_ingest_time"] = dt.datetime.now()

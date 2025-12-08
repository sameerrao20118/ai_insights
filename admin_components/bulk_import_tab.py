import datetime as dt

import pandas as pd
import streamlit as st

from admin.admin_utils import get_vdb, record_ingest
from ingestion.excel_ingest import EXCEL_PATH, ingest_excel


def render_bulk_import_tab():
    st.subheader("Bulk Import from Excel")
    st.write("Refresh the catalogue directly from `data/BankWide AI Project Tracker.xlsx`.")

    if not EXCEL_PATH.exists():
        st.error(f"Excel file not found at {EXCEL_PATH}.")
        return

    modified = dt.datetime.fromtimestamp(EXCEL_PATH.stat().st_mtime)
    preview_df = pd.read_excel(EXCEL_PATH, nrows=5)

    col1, col2 = st.columns(2)
    col1.metric("Rows previewed", len(preview_df))
    col2.metric("Last updated", modified.strftime("%d %b %Y"))
    st.dataframe(preview_df, hide_index=True, use_container_width=True)

    if st.button("Ingest / Refresh Catalogue", type="primary"):
        vdb = get_vdb()
        if not vdb:
            return
        with st.spinner("Ingesting Excel and updating vector store..."):
            usecases = ingest_excel(vdb=vdb)
        record_ingest(len(usecases))
        st.success(f"Ingested {len(usecases)} use cases.")

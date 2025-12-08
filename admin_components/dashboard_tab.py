import pandas as pd
import streamlit as st

from admin.admin_utils import get_vdb


def render_dashboard_tab():
    st.subheader("Catalogue Overview")
    st.write("Search the indexed catalogue, explore sampled records, and monitor ingestion health.")

    vdb = get_vdb()
    if not vdb:
        return

    query = st.text_input("Search or describe a use case", placeholder="All use cases")
    k = st.slider("Results to show", min_value=5, max_value=50, value=20, step=5)
    results = vdb.search_similar(query.strip() or "all use cases", k=k)

    st.metric("Use cases sampled", len(results))
    if results:
        df = pd.DataFrame(
            [
                {
                    "ID": r["metadata"].get("UseCaseID"),
                    "Use Case": r["metadata"].get("UseCaseName"),
                    "Team": r["metadata"].get("Team"),
                    "Env": r["metadata"].get("Environment"),
                    "AI Type": r["metadata"].get("AIType"),
                    "Budget (GBP)": r["metadata"].get("EstimatedBudgetGBP"),
                }
                for r in results
            ]
        )
        st.dataframe(df, hide_index=True, use_container_width=True)

        st.caption("Showing the most similar records based on your query.")
    else:
        st.info("No records yet. Try running Bulk Import to populate the catalogue.")

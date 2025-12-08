import streamlit as st
from pydantic import ValidationError

from admin.admin_utils import get_vdb, record_ingest
from models import AIUseCase


def render_manual_add_tab():
    st.subheader("Manual Add")
    st.write("Capture a single use-case without waiting for the next Excel refresh. Fields mirror the bulk import file.")

    vdb = get_vdb()
    if not vdb:
        return

    with st.form("manual_add_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        usecase_name = col1.text_input("Use-Case Name", placeholder="GenAI assistant for ops playbooks").strip()
        usecase_id = col2.text_input("Use-Case ID", placeholder="UC-123").strip()
        function_id = col3.text_input("Function ID", placeholder="FN-001").strip()

        col4, col5 = st.columns(2)
        team = col4.text_input("Team", placeholder="Payments").strip()
        environment = col5.selectbox("Production/Lower Environment", ["Production", "Lower", "Both", "Unknown"], index=3)

        key_contact = st.text_input("Use Case Project Manager / Key Contact", placeholder="alex.smith@company.com").strip()
        project_description = st.text_area("Project Description", placeholder="What problem are we solving?", height=120)

        col6, col7, col8 = st.columns(3)
        estimated_budget = col6.number_input("Estimated Budget (GBP)", min_value=0.0, step=10000.0, format="%.0f")
        benefit_value = col7.number_input("Benefit Value per annum", min_value=0.0, step=10000.0, format="%.0f")
        ai_type = col8.selectbox(
            "AI Type (AI Gateway / Aiden / Co-pilot / Duo / 3rd Party)",
            ["AI Gateway", "Aiden", "Co-pilot", "Duo", "3rd Party", "Other"],
        )

        col9, col10, col11 = st.columns(3)
        number_users = col9.number_input("Number of Users", min_value=0, step=10)
        usage_start = col10.text_input("Usage Start Date", placeholder="2025-02-01")
        cost_to_date = col11.number_input("Cost till date (GBP)", min_value=0.0, step=10000.0, format="%.0f")

        col12, col13, col14 = st.columns(3)
        last_month_cost = col12.number_input("Last Month Cost (GBP)", min_value=0.0, step=10000.0, format="%.0f")
        last_three_months = col13.number_input("Last 3 Months Cost (GBP)", min_value=0.0, step=10000.0, format="%.0f")
        last_year_cost = col14.number_input("Last 1 Year Cost (GBP)", min_value=0.0, step=10000.0, format="%.0f")

        benefit_cost_pa = st.number_input("Benefit / Cost per annum", min_value=0.0, step=0.1, format="%.2f")

        submitted = st.form_submit_button("Save to Catalogue", type="primary")

    if submitted:
        try:
            uc = AIUseCase(
                UseCaseName=usecase_name,
                UseCaseID=usecase_id,
                FunctionID=function_id or None,
                Environment=environment if environment != "Unknown" else None,
                Team=team,
                KeyContact=key_contact,
                ProjectDescription=project_description,
                EstimatedBudgetGBP=estimated_budget or None,
                BenefitValuePerAnnum=benefit_value or None,
                AIType=ai_type,
                NumberOfUsers=number_users or None,
                UsageStartDate=usage_start or None,
                CostToDateGBP=cost_to_date or None,
                LastMonthCostGBP=last_month_cost or None,
                LastThreeMonthsCostGBP=last_three_months or None,
                LastYearCostGBP=last_year_cost or None,
                BenefitCostPerAnnum=benefit_cost_pa or None,
            )
        except ValidationError as exc:
            st.error("Please correct the highlighted fields before saving.")
            st.json(exc.errors())
            return

        meta = uc.model_dump()
        vdb.add_documents(
            [
                {
                    "id": meta["UseCaseID"],
                    "title": meta["UseCaseName"],
                    "content": f"{meta['UseCaseName']} - {meta['ProjectDescription']}",
                    "metadata": meta,
                }
            ]
        )
        record_ingest(st.session_state.get("last_ingest_count", 0) + 1)
        st.success(f"Saved '{uc.UseCaseName}' to the catalogue.")

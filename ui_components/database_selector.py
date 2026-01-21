"""
Database selector UI component for switching between MySQL databases.
"""
import streamlit as st
from typing import List
import logging

logger = logging.getLogger(__name__)


def get_available_databases() -> List[str]:
    """
    Get list of available databases from MySQL server.
    
    Returns:
        List of database names
    """
    # For now, return hardcoded list. Could query MySQL for actual databases.
    return ["ai_insights", "tpch"]


def render_database_selector():
    """
    Render database selector dropdown in Streamlit UI.
    Updates session state when selection changes.
    """
    # Initialize session state if not exists
    if 'selected_database' not in st.session_state:
        st.session_state.selected_database = "ai_insights"  # default
    
    # Get available databases
    databases = get_available_databases()
    
    # Render selector
    selected = st.selectbox(
        "📊 Select Database",
        databases,
        index=databases.index(st.session_state.selected_database) if st.session_state.selected_database in databases else 0,
        key="database_selector",
        help="Choose which database to query"
    )
    
    # Detect change
    if selected != st.session_state.selected_database:
        logger.info(f"Database switched: {st.session_state.selected_database} → {selected}")
        st.session_state.selected_database = selected
        
        # Clear schema cache when database changes
        if 'schema_cache' in st.session_state:
            del st.session_state['schema_cache']
        
        st.success(f"✅ Switched to database: **{selected}**")
        st.rerun()
    
    return selected


def get_current_database() -> str:
    """
    Get currently selected database from session state.
    
    Returns:
        Current database name
    """
    if 'selected_database' not in st.session_state:
        st.session_state.selected_database = "ai_insights"
    
    return st.session_state.selected_database

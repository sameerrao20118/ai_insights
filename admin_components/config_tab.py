"""
Configuration tab for data source management.
"""
import streamlit as st
import pandas as pd
from config import settings
from data_sources import get_data_source
from data_sources.factory import reset_data_source
import services_mysql


def render_config_tab():
    """Render the configuration tab."""
    st.subheader("⚙️ Data Source Configuration")
    
    st.info(
        "Configure your data source (Excel or MySQL). "
        "Changes require restarting the application to take effect."
    )
    
    # Show current configuration
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Current Data Source")
        current_source = settings.data_source.upper()
        
        if current_source == "EXCEL":
            st.success(f"✅ Active: {current_source}")
        elif current_source == "MYSQL":
            st.success(f"✅ Active: {current_source}")
        else:
            st.warning(f"⚠️ Unknown: {current_source}")
    
    with col2:
        st.markdown("### Connection Status")
        try:
            data_source = get_data_source()
            source_info = data_source.get_source_info()
            
            st.write(f"**Type**: {source_info.get('type', 'N/A')}")
            st.write(f"**Location**: {source_info.get('location', 'N/A')}")
            st.write(f"**Status**: {source_info.get('status', 'N/A')}")
            st.write(f"**Records**: {source_info.get('records', 0):,}")
        except Exception as e:
            st.error(f"Error getting source info: {e}")
    
    st.markdown("---")
    
    # MySQL Configuration Section
    if settings.data_source == "mysql":
        render_mysql_config()
    else:
        render_excel_config()
    
    # Configuration instructions
    st.markdown("---")
    st.markdown("### How to Change Data Source")
    
    st.code("""
# Edit your .env file:

# For Excel data source (default):
DATA_SOURCE=excel

# For MySQL data source:
DATA_SOURCE=mysql
MYSQL_HOST=your-mysql-host
MYSQL_PORT=3306
MYSQL_DATABASE=your-database
MYSQL_USER=your-username
MYSQL_PASSWORD=your-password
MYSQL_TABLE=ai_usecases
    """, language="bash")
    
    st.caption("After updating .env, restart the Streamlit application for changes to take effect.")


def render_excel_config():
    """Render Excel-specific configuration."""
    st.markdown("### Excel Data Source")
    
    try:
        data_source = get_data_source()
        metadata = data_source.get_metadata()
        
        if metadata.get("file_exists"):
            st.success(f"✅ Excel file found: {metadata.get('file_path')}")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Rows", metadata.get("row_count", 0))
            col2.metric("Columns", metadata.get("column_count", 0))
            
            with st.expander("View Column Names"):
                columns = metadata.get("columns", [])
                if columns:
                    st.write(columns)
                else:
                    st.write("No columns found")
        else:
            st.error(f"❌ Excel file not found: {metadata.get('file_path')}")
            st.info("Upload an Excel file using the 'Bulk Import' tab")
    
    except Exception as e:
        st.error(f"Error loading Excel configuration: {e}")


def render_mysql_config():
    """Render MySQL-specific configuration."""
    st.markdown("### MySQL Data Source")
    
    # Connection Details
    with st.expander("📋 Connection Details", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Host**: {settings.mysql_host}")
            st.write(f"**Port**: {settings.mysql_port}")
            st.write(f"**Database**: {settings.mysql_database}")
        
        with col2:
            st.write(f"**Table**: {settings.mysql_table}")
            st.write(f"**User**: {settings.mysql_user}")
            st.write(f"**SSL**: {'Enabled' if settings.mysql_ssl_enabled else 'Disabled'}")
    
    # Test Connection
    st.markdown("### Connection Test")
    
    if st.button("🔌 Test MySQL Connection", type="primary"):
        with st.spinner("Testing connection..."):
            result = services_mysql.validate_mysql_connection()
            
            if result.get("connected"):
                st.success("✅ Connection successful!")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Database", result.get("database", "N/A"))
                col2.metric("Table", result.get("table", "N/A"))
                col3.metric("Records", result.get("row_count", 0))
            else:
                st.error(f"❌ Connection failed: {result.get('error', 'Unknown error')}")
                st.info("Check your .env file configuration and ensure MySQL server is running")
    
    # Schema Viewer
    st.markdown("### Database Schema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 View Schema"):
            with st.spinner("Loading schema..."):
                schema = services_mysql.get_database_schema()
                
                if "error" in schema:
                    st.error(f"Error loading schema: {schema['error']}")
                else:
                    st.write(f"**Database**: {schema.get('database')}")
                    st.write(f"**Tables**: {schema.get('table_count', 0)}")
                    st.write(f"**Relationships**: {len(schema.get('relationships', []))}")
                    
                    # Display tables in a nice table
                    tables_data = []
                    for table_name, table_info in schema.get("tables", {}).items():
                        tables_data.append({
                            "Table": table_name,
                            "Columns": len(table_info.get("columns", [])),
                            "Rows": table_info.get("row_count", 0),
                            "Foreign Keys": len(table_info.get("foreign_keys", [])),
                        })
                    
                    if tables_data:
                        df = pd.DataFrame(tables_data)
                        st.dataframe(df, use_container_width=True)
                    
                    # Show relationships
                    relationships = schema.get("relationships", [])
                    if relationships:
                        with st.expander(f"View {len(relationships)} Relationships"):
                            for rel in relationships:
                                st.write(
                                    f"• `{rel['from_table']}.{rel['from_column']}` → "
                                    f"`{rel['to_table']}.{rel['to_column']}`"
                                )
    
    with col2:
        if st.button("🔄 Refresh Schema Cache"):
            with st.spinner("Refreshing schema cache..."):
                result = services_mysql.refresh_schema_cache()
                
                if result.get("success"):
                    st.success(f"✅ {result.get('message')}")
                    st.write(f"**Tables**: {result.get('table_count', 0)}")
                    st.write(f"**Relationships**: {result.get('relationship_count', 0)}")
                    st.info("Schema cache refreshed. New tables and columns will be detected on next query.")
                else:
                    st.error(f"❌ Refresh failed: {result.get('error')}")
    
    st.caption("**Tip**: Click 'Refresh Schema Cache' after adding/removing tables or columns to update the natural language query system.")
    
    # Query Observability Settings
    st.markdown("### Query Observability")
    
    col1, col2 = st.columns(2)
    
    with col1:
        status = "✅ Enabled" if settings.enable_sql_logging else "❌ Disabled"
        st.write(f"**SQL Logging**: {status}")
    
    with col2:
        status = "✅ Enabled" if settings.show_generated_sql else "❌ Disabled"
        st.write(f"**Show Generated SQL**: {status}")
    
    st.caption("Configure these settings in your .env file:")
    st.code("""
ENABLE_SQL_LOGGING=true
SHOW_GENERATED_SQL=true
    """, language="bash")

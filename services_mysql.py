"""
MySQL-specific service functions.
"""
from typing import Dict, Any, Optional
import logging

from data_sources.mysql_source import MySQLSource
from data_sources.nl_to_sql import NLToSQLTranslator, SQLQueryResult
from config import settings

logger = logging.getLogger(__name__)

# Global instances
_mysql_source: Optional[MySQLSource] = None
_nl_translator: Optional[NLToSQLTranslator] = None


def get_mysql_source() -> MySQLSource:
    """Get or create MySQL source instance."""
    global _mysql_source
    if _mysql_source is None:
        _mysql_source = MySQLSource()
    return _mysql_source


def get_nl_translator() -> NLToSQLTranslator:
    """Get or create NL-to-SQL translator instance."""
    global _nl_translator
    if _nl_translator is None:
        mysql_source = get_mysql_source()
        _nl_translator = NLToSQLTranslator(mysql_source)
    return _nl_translator


def query_with_nl(question: str) -> SQLQueryResult:
    """
    Execute a natural language query against MySQL.
    
    Args:
        question: Natural language question
        
    Returns:
        SQLQueryResult with SQL, results, and metadata
    """
    if settings.data_source != "mysql":
        raise ValueError("Natural language SQL queries are only available with MySQL data source")
    
    translator = get_nl_translator()
    return translator.execute_nl_query(question)


def validate_mysql_connection() -> Dict[str, Any]:
    """
    Validate MySQL connection.
    
    Returns:
        Dict with connection status and details
    """
    try:
        mysql_source = get_mysql_source()
        is_connected = mysql_source.validate_connection()
        
        if is_connected:
            metadata = mysql_source.get_metadata()
            return {
                "connected": True,
                "host": settings.mysql_host,
                "database": settings.mysql_database,
                "table": settings.mysql_table,
                "row_count": metadata.get("row_count", 0),
            }
        else:
            return {
                "connected": False,
                "error": "Connection failed",
            }
    except Exception as e:
        logger.error(f"MySQL connection validation failed: {e}")
        return {
            "connected": False,
            "error": str(e),
        }


def get_database_schema() -> Dict[str, Any]:
    """
    Get MySQL database schema.
    
    Returns:
        Dict with schema information
    """
    if settings.data_source != "mysql":
        return {"error": "Schema information only available for MySQL data source"}
    
    try:
        mysql_source = get_mysql_source()
        return mysql_source.get_full_database_schema()
    except Exception as e:
        logger.error(f"Error getting schema: {e}")
        return {"error": str(e)}


def refresh_schema_cache() -> Dict[str, Any]:
    """
    Refresh the schema cache. Call this after schema changes.
    
    Returns:
        Status dict with refresh results
    """
    global _nl_translator
    
    try:
        if _nl_translator is not None:
            _nl_translator.refresh_schema()
        
        # Get fresh schema
        schema = get_database_schema()
        
        if "error" not in schema:
            return {
                "success": True,
                "message": "Schema cache refreshed successfully",
                "table_count": schema.get("table_count", 0),
                "relationship_count": len(schema.get("relationships", [])),
            }
        else:
            return {
                "success": False,
                "error": schema["error"]
            }
    except Exception as e:
        logger.error(f"Error refreshing schema cache: {e}")
        return {
            "success": False,
            "error": str(e)
        }

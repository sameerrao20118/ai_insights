"""
MySQL-specific service functions.
Multi-database support via UI selection.
"""
from typing import Dict, Any, Optional
import logging

from data_sources.factory import get_mysql_source
from data_sources.nl_to_sql import NLToSQLTranslator, SQLQueryResult
from config import settings

logger = logging.getLogger(__name__)

# Per-database translator instances
_nl_translators: Dict[str, NLToSQLTranslator] = {}


def get_nl_translator(database: Optional[str] = None) -> NLToSQLTranslator:
    """
    Get or create NL-to-SQL translator instance for specific database.
    
    Args:
        database: Database name. If None, uses default from settings
    
    Returns:
        NLToSQLTranslator instance
    """
    global _nl_translators
    
    db_name = database if database is not None else settings.mysql_database
    
    if db_name not in _nl_translators:
        mysql_source = get_mysql_source(database=db_name)
        _nl_translators[db_name] = NLToSQLTranslator(mysql_source)
        logger.info(f"Created NL translator for database: {db_name}")
    
    return _nl_translators[db_name]


def query_with_nl(question: str, database: Optional[str] = None) -> SQLQueryResult:
    """
    Execute a natural language query against MySQL.
    
    Args:
        question: Natural language question
        database: Optional database name. If None, uses default
        
    Returns:
        SQLQueryResult with SQL, results, and metadata
    """
    if settings.data_source != "mysql":
        raise ValueError("Natural language SQL queries are only available with MySQL data source")
    
    translator = get_nl_translator(database=database)
    return translator.execute_nl_query(question)


def validate_mysql_connection(database: Optional[str] = None) -> Dict[str, Any]:
    """
    Validate MySQL connection.
    
    Args:
        database: Optional database name
    
    Returns:
        Dict with connection status and details
    """
    try:
        mysql_source = get_mysql_source(database=database)
        is_connected = mysql_source.validate_connection()
        
        db_name = database if database is not None else settings.mysql_database
        
        if is_connected:
            metadata = mysql_source.get_metadata()
            return {
                "connected": True,
                "host": settings.mysql_host,
                "database": db_name,
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


def get_database_schema(database: Optional[str] = None) -> Dict[str, Any]:
    """
    Get MySQL database schema.
    
    Args:
        database: Optional database name
    
    Returns:
        Dict with schema information
    """
    if settings.data_source != "mysql":
        return {"error": "Schema information only available for MySQL data source"}
    
    try:
        mysql_source = get_mysql_source(database=database)
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

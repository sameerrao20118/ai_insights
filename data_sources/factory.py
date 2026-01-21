"""
Factory for creating database-specific data sources.
Supports multi-database selection via UI.
"""
from typing import Optional
from config import settings
from .base import DataSource
from .excel_source import ExcelSource
from .mysql_source import MySQLSource
import logging

logger = logging.getLogger(__name__)

# Singleton instances per database
_mysql_sources = {}
_excel_source = None


def get_data_source(database: Optional[str] = None) -> DataSource:
    """
    Get appropriate data source based on configuration.
    
    Args:
        database: Optional MySQL database name (for MySQL data source only)
    
    Returns:
        DataSource instance
    """
    global _mysql_sources, _excel_source
    
    if settings.data_source == "mysql":
        # Use provided database or default
        db_name = database if database is not None else settings.mysql_database
        
        # Create singleton per database
        if db_name not in _mysql_sources:
            logger.info(f"Creating MySQL data source for database: {db_name}")
            _mysql_sources[db_name] = MySQLSource(database=db_name)
        
        return _mysql_sources[db_name]
    
    elif settings.data_source == "excel":
        if _excel_source is None:
            logger.info("Creating Excel data source")
            _excel_source = ExcelSource()
        return _excel_source
    
    else:
        raise ValueError(f"Unknown data source: {settings.data_source}")


def get_mysql_source(database: Optional[str] = None) -> MySQLSource:
    """
    Get MySQL data source for specific database.
    
    Args:
        database: Database name. If None, uses default from settings
    
    Returns:
        MySQLSource instance
    """
    db_name = database if database is not None else settings.mysql_database
    
    if db_name not in _mysql_sources:
        logger.info(f"Creating MySQL source for database: {db_name}")
        _mysql_sources[db_name] = MySQLSource(database=db_name)
    
    return _mysql_sources[db_name]


def reset_data_source():
    """Reset/clear cached data sources."""
    global _mysql_sources, _excel_source
    _mysql_sources = {}
    _excel_source = None
    logger.info("Data source cache cleared")

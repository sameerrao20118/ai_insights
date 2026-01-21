"""
Factory for creating data source instances.
"""
import logging
from typing import Optional

from .base import DataSource
from .excel_source import ExcelSource
from .mysql_source import MySQLSource
from config import settings

logger = logging.getLogger(__name__)

_data_source_instance: Optional[DataSource] = None


def get_data_source(force_reload: bool = False) -> DataSource:
    """
    Factory function to get the appropriate data source based on configuration.
    
    Args:
        force_reload: If True, create a new instance even if one exists
        
    Returns:
        DataSource instance (ExcelSource or MySQLSource)
    """
    global _data_source_instance

    if _data_source_instance is not None and not force_reload:
        return _data_source_instance

    source_type = settings.data_source.lower()

    if source_type == "mysql":
        logger.info("Initializing MySQL data source")
        _data_source_instance = MySQLSource()
    elif source_type == "excel":
        logger.info("Initializing Excel data source")
        _data_source_instance = ExcelSource()
    else:
        logger.warning(f"Unknown data source type: {source_type}, defaulting to Excel")
        _data_source_instance = ExcelSource()

    return _data_source_instance


def reset_data_source():
    """Reset the data source instance (useful for testing or reconfiguration)."""
    global _data_source_instance
    _data_source_instance = None

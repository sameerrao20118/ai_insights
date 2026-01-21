"""
Data sources package for AI Insights.

Provides abstract interface and factory for multiple data sources (Excel, MySQL).
"""
from typing import List
from models import AIUseCase
from .base import DataSource
from .factory import get_data_source

__all__ = ["DataSource", "get_data_source"]

"""
Abstract base class for data sources.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from models import AIUseCase


class DataSource(ABC):
    """Abstract interface for data sources (Excel, MySQL, etc.)"""

    @abstractmethod
    def load_all_usecases(self) -> List[AIUseCase]:
        """Load all use cases from the data source."""
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the data source."""
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """Validate that the data source is accessible."""
        pass

    @abstractmethod
    def get_source_info(self) -> Dict[str, Any]:
        """Get information about the data source for display."""
        pass

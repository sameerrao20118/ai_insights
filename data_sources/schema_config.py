"""
Schema Configuration Loader

Loads database schema configurations from YAML files and formats them for LLM consumption.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SchemaConfigLoader:
    """Loads and formats schema configurations for different databases."""
    
    def __init__(self, schemas_dir: str = "schemas"):
        """
        Initialize schema loader.
        
        Args:
            schemas_dir: Directory containing schema YAML files
        """
        self.schemas_dir = Path(schemas_dir)
        self._cache = {}
    
    def load_schema_config(self, database: str) -> Optional[Dict[str, Any]]:
        """
        Load schema configuration for a database.
        
        Args:
            database: Database name (e.g., 'tpch', 'ai_insights')
            
        Returns:
            Schema configuration dict or None if not found
        """
        if database in self._cache:
            return self._cache[database]
        
        schema_file = self.schemas_dir / f"{database}.yaml"
        
        if not schema_file.exists():
            logger.warning(f"No schema config found for database: {database}")
            return None
        
        try:
            with open(schema_file, 'r') as f:
                config = yaml.safe_load(f)
                self._cache[database] = config
                logger.info(f"Loaded schema config for {database}")
                return config
        except Exception as e:
            logger.error(f"Error loading schema config for {database}: {e}")
            return None
    
    def format_for_llm(self, database: str) -> str:
        """
        Format schema configuration as text for LLM prompt.
        
        Args:
            database: Database name
            
        Returns:
            Formatted schema description
        """
        config = self.load_schema_config(database)
        
        if not config:
            return ""
        
        output = []
        output.append(f"\n=== {config['database']['description'].upper()} ===")
        output.append("")
        
        # Tables section
        output.append("📋 TABLES:")
        for table_name, table_info in config.get('tables', {}).items():
            output.append(f"\n**{table_name}**: {table_info['description']}")
            output.append(f"  Primary Key: {table_info['primary_key']}")
            
            if 'important_columns' in table_info:
                output.append("  Key Columns:")
                for col_info in table_info['important_columns']:
                    for col_name, col_desc in col_info.items():
                        output.append(f"    - {col_name}: {col_desc}")
        
        # JOIN paths section
        if 'join_paths' in config:
            output.append("\n🔗 PREDEFINED JOIN PATHS:")
            output.append("Use these exact patterns for multi-table queries:")
            
            for path_name, path_info in config['join_paths'].items():
                output.append(f"\n**{path_name}**: {path_info['description']}")
                output.append(f"  Example question: \"{path_info['example']}\"")
                output.append("  SQL Pattern:")
                
                # Format the path
                tables_used = []
                joins = []
                
                for i, step in enumerate(path_info['path']):
                    if i == 0:
                        tables_used.append(step['from'])
                    tables_used.append(step['to'])
                    joins.append(f"INNER JOIN {step['to']} ON {step['on']}")
                
                output.append(f"    FROM {tables_used[0]}")
                for join in joins:
                    output.append(f"    {join}")
        
        # Query patterns section
        if 'query_patterns' in config:
            output.append("\n📝 COMMON QUERY PATTERNS:")
            for pattern_name, pattern_info in config['query_patterns'].items():
                output.append(f"\n{pattern_info['description']}:")
                output.append(f"  {pattern_info['template']}")
        
        return "\n".join(output)


# Global instance
_schema_loader = None

def get_schema_loader() -> SchemaConfigLoader:
    """Get singleton schema loader instance."""
    global _schema_loader
    if _schema_loader is None:
        _schema_loader = SchemaConfigLoader()
    return _schema_loader

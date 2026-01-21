"""
Natural Language to SQL translation using LLM.
"""
from typing import Dict, Any, List, Tuple, Optional
import logging
import json

from llm.lm_interface import LLMInterface
from config import settings

logger = logging.getLogger(__name__)


NL_TO_SQL_SYSTEM_PROMPT = """You are a SQL expert that translates natural language questions into MySQL queries.

Given a database schema (with multiple tables and their relationships) and a natural language question, generate a valid MySQL query.

RULES:
1. Generate ONLY valid MySQL syntax
2. Use proper table and column names from the schema
3. **IMPORTANT**: When data spans multiple tables, use appropriate JOINs based on foreign key relationships
4. Analyze which tables contain the required data and JOIN them correctly
5. Use table aliases for clarity (e.g., `u` for users, `o` for orders)
6. Include WHERE, ORDER BY, GROUP BY, LIMIT as needed
7. Return queries that are safe (no DROP, DELETE, UPDATE, ALTER, INSERT, TRUNCATE)
8. Use appropriate aggregations (COUNT, SUM, AVG, MAX, MIN) when needed
9. Handle NULL values appropriately
10. For questions spanning tables, identify the relationship path and construct JOINs
11. Use INNER JOIN for required relationships, LEFT JOIN when data might be missing

RELATIONSHIP ANALYSIS:
- Study the foreign key relationships provided in the schema
- Determine which tables need to be joined to answer the question
- Find the shortest path between tables (avoid circular joins)
- Use the correct join columns based on FK relationships

EXAMPLES OF MULTI-TABLE QUERIES:
- "Show me users and their orders" → JOIN users and orders tables
- "What is the total revenue by customer?" → JOIN orders and customers, then GROUP BY
- "List products that have never been ordered" → LEFT JOIN products and order_items

RESPONSE FORMAT:
Return a JSON object with:
{
  "sql": "SELECT ... FROM ... JOIN ... WHERE ...",
  "explanation": "Brief explanation including which tables were joined and why",
  "tables_used": ["table1", "table2", ...]
}
"""


class SQLQueryResult:
    """Result of SQL query execution."""
    def __init__(self, sql: str, results: List[Dict[str, Any]], row_count: int, explanation: str = ""):
        self.sql = sql
        self.results = results
        self.row_count = row_count
        self.explanation = explanation


class NLToSQLTranslator:
    """Translates natural language questions to SQL queries."""

    def __init__(self, mysql_source):
        self.mysql_source = mysql_source
        self.llm = LLMInterface()
        self.schema_cache = None
        self.schema_cache_timestamp = None

    def refresh_schema(self):
        """Force refresh of the schema cache. Use when database structure changes."""
        self.schema_cache = None
        self.schema_cache_timestamp = None
        logger.info("Schema cache cleared - will reload on next query")

    def _get_schema_description(self) -> str:
        """Get a comprehensive text description of the database schema including relationships."""
        from datetime import datetime
        
        # Cache schema for performance, but allow refresh
        if self.schema_cache is None:
            logger.info("Loading full database schema...")
            # Get full database schema with all tables and relationships
            self.schema_cache = self.mysql_source.get_full_database_schema()
            self.schema_cache_timestamp = datetime.now()
            
            if "error" not in self.schema_cache:
                table_count = self.schema_cache.get('table_count', 0)
                rel_count = len(self.schema_cache.get('relationships', []))
                logger.info(f"Schema loaded: {table_count} tables, {rel_count} relationships")

        if "error" in self.schema_cache:
            return f"Error getting schema: {self.schema_cache['error']}"

        # Build comprehensive schema description
        desc_lines = [
            f"Database: {self.schema_cache.get('database')}",
            f"Total Tables: {self.schema_cache.get('table_count', 0)}",
            "\nTABLES AND COLUMNS:",
        ]

        tables = self.schema_cache.get("tables", {})
        for table_name, table_info in tables.items():
            desc_lines.append(f"\n--- Table: {table_name} ---")
            desc_lines.append(f"Rows: ~{table_info.get('row_count', 0)}")
            
            if table_info.get('comment'):
                desc_lines.append(f"Description: {table_info['comment']}")
            
            desc_lines.append("Columns:")
            for col in table_info.get("columns", []):
                col_name = col.get("COLUMN_NAME", "")
                col_type = col.get("DATA_TYPE", "")
                nullable = "NULL" if col.get("IS_NULLABLE") == "YES" else "NOT NULL"
                key = f" [PRIMARY KEY]" if col.get("COLUMN_KEY") == "PRI" else ""
                key += f" [FOREIGN KEY]" if col.get("COLUMN_KEY") == "MUL" else ""
                comment = f" -- {col.get('COLUMN_COMMENT')}" if col.get('COLUMN_COMMENT') else ""
                desc_lines.append(f"  - {col_name}: {col_type} {nullable}{key}{comment}")

        # Add relationships section
        relationships = self.schema_cache.get("relationships", [])
        if relationships:
            desc_lines.append("\nFOREIGN KEY RELATIONSHIPS:")
            for rel in relationships:
                desc_lines.append(
                    f"  {rel['from_table']}.{rel['from_column']} → {rel['to_table']}.{rel['to_column']}"
                )
        
        return "\n".join(desc_lines)

    def translate_to_sql(self, question: str) -> Tuple[str, str]:
        """
        Translate natural language question to SQL.
        
        Returns:
            Tuple of (sql_query, explanation)
        """
        schema_desc = self._get_schema_description()

        user_prompt = f"""Database Schema:
{schema_desc}

Natural Language Question:
{question}

Generate the SQL query to answer this question."""

        try:
            # Use LLM to generate SQL
            messages = [
                {"role": "system", "content": NL_TO_SQL_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self.llm.chat_completion(messages)
            
            # Parse response
            try:
                result = json.loads(response)
                sql = result.get("sql", "").strip()
                explanation = result.get("explanation", "")
            except json.JSONDecodeError:
                # Fallback: treat entire response as SQL
                sql = response.strip()
                explanation = "SQL generated from natural language query"

            # Validate SQL is safe (basic check)
            sql_upper = sql.upper()
            dangerous_keywords = ["DROP", "DELETE", "UPDATE", "ALTER", "TRUNCATE", "INSERT"]
            if any(keyword in sql_upper for keyword in dangerous_keywords):
                raise ValueError("Generated SQL contains potentially dangerous operations")

            if settings.enable_sql_logging:
                logger.info(f"Translated NL to SQL: {sql}")

            return sql, explanation

        except Exception as e:
            logger.error(f"Error translating NL to SQL: {e}")
            raise

    def execute_nl_query(self, question: str) -> SQLQueryResult:
        """
        Execute a natural language query.
        
        Args:
            question: Natural language question
            
        Returns:
            SQLQueryResult with query, results, and metadata
        """
        # Translate to SQL
        sql, explanation = self.translate_to_sql(question)

        # Execute SQL
        try:
            results = self.mysql_source.execute_query(sql)
            row_count = len(results)

            if settings.enable_sql_logging:
                logger.info(f"Query returned {row_count} rows")

            return SQLQueryResult(
                sql=sql,
                results=results,
                row_count=row_count,
                explanation=explanation
            )

        except Exception as e:
            logger.error(f"Error executing SQL: {e}")
            raise


def get_nl_to_sql_translator(mysql_source) -> NLToSQLTranslator:
    """Factory function to get NL-to-SQL translator."""
    return NLToSQLTranslator(mysql_source)

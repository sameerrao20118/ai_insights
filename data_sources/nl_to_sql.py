
"""
Natural Language to SQL translation using LLM.
"""
from typing import Dict, Any, List, Tuple, Optional
import logging
import json

from llm.lm_interface import LLMInterface
from config import settings
from .schema_config import get_schema_loader

logger = logging.getLogger(__name__)


NL_TO_SQL_SYSTEM_PROMPT = """You are a SQL expert that translates natural language questions into MySQL queries.

⚠️ CRITICAL: MySQL table and column names are CASE-SENSITIVE!
- You MUST use EXACT names from the schema below (character-for-character)
- If schema shows "ORDERS", you MUST write "FROM ORDERS" NOT "from orders"
- If schema shows "O_ORDERKEY", you MUST write "O_ORDERKEY" NOT "o_orderkey"

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
12. **CRITICAL - GROUP BY**: When using GROUP BY, ALL non-aggregated columns in SELECT must be in GROUP BY clause (MySQL ONLY_FULL_GROUP_BY mode)
13. Example: `SELECT p.product_id, p.name, SUM(qty) FROM products p GROUP BY p.product_id, p.name` ✅
14. Wrong: `SELECT p.product_id, p.name, SUM(qty) FROM products p GROUP BY p.product_id` ❌

RELATIONSHIP ANALYSIS:
- Study the foreign key relationships provided in the schema
- Determine which tables need to be joined to answer the question
- Find the shortest path between tables (avoid circular joins)
- Use the correct join columns based on FK relationships

EXAMPLES OF MULTI-TABLE QUERIES:
- "Show me users and their orders" → `SELECT u.name, o.order_id FROM users u INNER JOIN orders o ON u.id = o.user_id`
- "What is the total revenue by customer?" → `SELECT c.name, SUM(o.amount) FROM customers c INNER JOIN orders o ON c.id = o.customer_id GROUP BY c.id, c.name`
- "List products that have never been ordered" → `SELECT p.name FROM products p LEFT JOIN order_items oi ON p.id = oi.product_id WHERE oi.id IS NULL`
- "Year-wise sales by product" → `SELECT p.name, YEAR(o.order_date) AS year, SUM(oi.quantity) AS total FROM products p INNER JOIN order_items oi ON p.id = oi.product_id INNER JOIN orders o ON oi.order_id = o.id GROUP BY p.id, p.name, YEAR(o.order_date) ORDER BY year, total DESC`

**CRITICAL - Table Aliases**:
- ALWAYS define aliases in FROM/JOIN clauses: `FROM products p` not `FROM products`
- Use the alias consistently: `SELECT p.name FROM products p` ✅
- Wrong: `SELECT p.name FROM products` ❌

RESPONSE FORMAT:
**CRITICAL**: Return ONLY a valid JSON object. No additional text before or after.

{
  "sql": "SELECT ... FROM ... JOIN ... WHERE ...",
  "explanation": "Brief explanation including which tables were joined and why",
  "tables_used": ["table1", "table2", ...]
}

DO NOT include:
- Introductory text like "Here is the query"
- Markdown code blocks
- Explanatory paragraphs
- Any text outside the JSON object

Example valid response:
{"sql": "SELECT * FROM customers WHERE email = 'john@example.com'", "explanation": "Simple query to find customer by email", "tables_used": ["customers"]}
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

        # Try to load declarative schema config first
        try:
            schema_loader = get_schema_loader()
            db_name = self.mysql_source.database_name
            schema_config_text = schema_loader.format_for_llm(db_name)
            
            if schema_config_text:
                logger.info(f"Using declarative schema config for {db_name}")
                return schema_config_text
        except Exception as e:
            logger.warning(f"Could not load schema config: {e}")
        
        # Fallback: Use auto-generated schema from MySQL
        logger.info("Using auto-generated schema from MySQL")
        return self._format_schema_for_llm(self.schema_cache)

    def _format_schema_for_llm(self, schema: Dict[str, Any]) -> str:
        """Format database schema for LLM prompt - PRESERVE EXACT CASE and show clear relationships."""
        output = []
        output.append("\n=== DATABASE SCHEMA ===")
        output.append("CRITICAL: Use EXACT table and column names (case-sensitive)")
        output.append("")
        
        table_schemas = schema.get("tables", {})
        relationships = schema.get("relationships", [])
        
        # Part 1: Table Definitions with Column Ownership
        output.append("📋 TABLES AND COLUMNS:")
        for table_name, table_info in table_schemas.items():
            output.append(f"\n**Table: {table_name}**")
            columns = table_info.get("columns", [])
            
            # Group columns by type for clarity
            pk_cols = []
            fk_cols = []
            regular_cols = []
            
            for col in columns:
                col_name = col.get("COLUMN_NAME", col.get("column_name", ""))
                col_type = col.get("DATA_TYPE", col.get("data_type", ""))
                col_key = col.get("COLUMN_KEY", col.get("column_key", ""))
                
                col_info = f"{col_name} ({col_type})"
                
                if col_key == "PRI":
                    pk_cols.append(col_info + " [PRIMARY KEY]")
                elif col_key == "MUL":
                    fk_cols.append(col_info + " [FOREIGN KEY]")
                else:
                    regular_cols.append(col_info)
            
            # Display grouped
            for col in pk_cols + fk_cols + regular_cols:
                output.append(f"  - {col}")
        
        # Part 2: Foreign Key Relationships (JOIN Paths)
        if relationships:
            output.append("\n🔗 FOREIGN KEY RELATIONSHIPS (Use these for JOINs):")
            output.append("Format: table.column → referenced_table.referenced_column")
            for rel in relationships:
                output.append(
                    f"  • {rel['from_table']}.{rel['from_column']} → {rel['to_table']}.{rel['to_column']}"
                )
        
        # Part 3: JOIN Path Examples (Dynamic from schema)
        output.append("\n📍 EXAMPLE JOIN PATTERNS:")
        output.append("(Use these patterns to construct queries)")
        
        # Generate simple JOIN examples from actual relationships
        if relationships:
            # Show first few relationships as examples
            for i, rel in enumerate(relationships[:3]):
                from_tbl = rel['from_table']
                to_tbl = rel['to_table']
                from_col = rel['from_column']
                to_col = rel['to_column']
                
                # Use first letter as alias (simple heuristic)
                from_alias = from_tbl[0].lower()
                to_alias = to_tbl[0].lower()
                
                output.append(f"""
Example {i+1}: Joining {from_tbl} with {to_tbl}:
  SELECT {from_alias}.*, {to_alias}.*
  FROM {from_tbl} {from_alias}
  INNER JOIN {to_tbl} {to_alias} ON {from_alias}.{from_col} = {to_alias}.{to_col}
""")
        
        # Part 4: Multi-hop JOIN guidance
        output.append("\n⚠️ MULTI-TABLE QUERIES:")
        output.append("- Follow FK relationships in correct order")
        output.append("- Do NOT skip intermediate tables")
        output.append("- Each column belongs to ONE table - check table definitions above")
        output.append("- If column X is not in table A, find which table has it and JOIN accordingly")
        
        return "\n".join(output)

    def _translate(self, question: str) -> Tuple[str, str]:
        """Translate natural language to SQL using LLM."""
        # Get schema
        schema_text = self._get_schema_description()
        
        # DEBUG: Log the schema being sent to LLM
        if settings.enable_sql_logging:
            logger.info(f"=== SCHEMA SENT TO LLM ===")
            logger.info(schema_text[:500])  # First 500 chars
        
        # Create prompt
        user_prompt = f"""{schema_text}

QUESTION: {question}

Generate a MySQL query to answer this question. Return ONLY a JSON object with this format:
{{"sql": "YOUR_SQL_QUERY_HERE", "explanation": "Brief explanation"}}

REMEMBER: Use exact table and column names from the schema above (case-sensitive)!
"""
        
        messages = [
            {"role": "system", "content": NL_TO_SQL_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        # Get LLM response
        if settings.enable_sql_logging:
            logger.info(f"Translating question: {question}")
        
        response = self.llm.chat_completion(messages)
        
        # DEBUG: Log raw LLM response
        if settings.enable_sql_logging:
            logger.info(f"=== RAW LLM RESPONSE ===")
            logger.info(response[:300])
        
        # Parse response - handle cases where LLM adds extra text
        import re
        
        try:
            sql = None
            explanation = ""
            
            # Strategy 1: Try to parse as pure JSON
            try:
                result = json.loads(response.strip())
                sql = result.get("sql", "").strip()
                explanation = result.get("explanation", "")
                if settings.enable_sql_logging:
                    logger.info("Strategy 1: Pure JSON parsing succeeded")
            except json.JSONDecodeError as e:
                if settings.enable_sql_logging:
                    logger.warning(f"Strategy 1 failed: {e}")
                pass
            
            # Strategy 2: Extract JSON with brace counting
            if not sql:
                try:
                    start_idx = response.find('{')
                    if start_idx != -1:
                        brace_count = 0
                        end_idx = start_idx
                        for i in range(start_idx, len(response)):
                            if response[i] == '{':
                                brace_count += 1
                            elif response[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end_idx = i + 1
                                    break
                        
                        if brace_count == 0:
                            json_str = response[start_idx:end_idx]
                            result = json.loads(json_str)
                            sql = result.get("sql", "").strip()
                            explanation = result.get("explanation", "")
                            if settings.enable_sql_logging:
                                logger.info("Strategy 2: Brace counting succeeded")
                except (json.JSONDecodeError, ValueError) as e:
                    if settings.enable_sql_logging:
                        logger.warning(f"Strategy 2 failed: {e}")
                    pass
            
            # Strategy 3: Regex extraction of SQL value from JSON
            if not sql:
                try:
                    # Look for "sql": "SELECT ... " pattern
                    sql_match = re.search(r'"sql"\s*:\s*"([^"]+(?:\\.[^"]*)*)"', response, re.DOTALL)
                    if sql_match:
                        sql = sql_match.group(1).strip()
                        # Unescape the string
                        sql = sql.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
                        explanation = "SQL extracted via regex from malformed JSON"
                        if settings.enable_sql_logging:
                            logger.info("Strategy 3: Regex extraction succeeded")
                except Exception as e:
                    if settings.enable_sql_logging:
                        logger.warning(f"Strategy 3 failed: {e}")
                    pass
            
            # Strategy 4: Last resort - treat whole response as SQL
            if not sql:
                sql = response.strip()
                
                # Remove common LLM prefixes
                prefixes_to_remove = [
                    "Here is the MySQL query",
                    "Here's the MySQL query", 
                    "The SQL query is:",
                    "SQL Query:",
                    "Query:",
                ]
                for prefix in prefixes_to_remove:
                    if sql.lower().startswith(prefix.lower()):
                        sql = sql[len(prefix):].strip().lstrip(':').strip().strip('"\'')
                        break
                
                # Remove markdown code blocks
                sql = re.sub(r'^```sql\s*', '', sql, flags=re.IGNORECASE)
                sql = re.sub(r'^```\s*', '', sql)
                sql = re.sub(r'\s*```$', '', sql)
                sql = sql.strip()
                
                explanation = "SQL extracted from raw text response"
                if settings.enable_sql_logging:
                    logger.info("Strategy 4: Raw text extraction used")
            
            # Final validation
            if sql.startswith('{'):
                # One last try with regex
                sql_match = re.search(r'"sql"\s*:\s*"([^"]+)"', sql)
                if sql_match:
                    sql = sql_match.group(1)
                    if settings.enable_sql_logging:
                        logger.warning("Final extraction from JSON-like string")
            
            if settings.enable_sql_logging:
                logger.info(f"Extracted SQL (first 200 chars): {sql[:200]}")

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

    def translate_to_sql(self, question: str) -> Tuple[str, str]:
        """
        Translate natural language question to SQL.
        Public wrapper for _translate method.
        
        Returns:
            Tuple of (sql_query, explanation)
        """
        return self._translate(question)

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
        logger.info(f"Executing SQL: {sql[:200]}...")
        
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
            e.sql_query = sql  # Attach for UI display
            raise


def get_nl_to_sql_translator(mysql_source) -> NLToSQLTranslator:
    """Factory function to get NL-to-SQL translator."""
    return NLToSQLTranslator(mysql_source)

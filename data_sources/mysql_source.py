"""
MySQL data source implementation.
"""
from typing import List, Dict, Any, Optional
import logging
import mysql.connector
from mysql.connector import pooling, Error

from .base import DataSource
from models import AIUseCase
from config import settings

logger = logging.getLogger(__name__)


class MySQLSource(DataSource):
    """MySQL database data source implementation."""

    def __init__(self, database: str = None):
        """
        Initialize MySQL data source.
        
        Args:
            database: Optional database name. If None, uses settings.mysql_database
        """
        # Use provided database or fall back to settings
        target_database = database if database is not None else settings.mysql_database
        
        self.config = {
            "host": settings.mysql_host,
            "port": settings.mysql_port,
            "database": target_database,  # Use dynamic database
            "user": settings.mysql_user,
            "password": settings.mysql_password,
        }
        
        if settings.mysql_ssl_enabled:
            self.config["ssl_disabled"] = False
        
        self.table_name = settings.mysql_table
        self.database_name = target_database  # Store for reference
        self.connection_pool = None
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize connection pool."""
        try:
            self.connection_pool = pooling.MySQLConnectionPool(
                pool_name="ai_insights_pool",
                pool_size=settings.mysql_connection_pool_size,
                pool_reset_session=True,
                **self.config
            )
            logger.info("MySQL connection pool initialized successfully")
        except Error as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise

    def _get_connection(self):
        """Get a connection from the pool."""
        if self.connection_pool:
            return self.connection_pool.get_connection()
        raise RuntimeError("Connection pool not initialized")

    def _map_row_to_usecase(self, row: Dict[str, Any]) -> AIUseCase:
        """Map a database row to AIUseCase model."""
        # Handle different column naming conventions (snake_case or PascalCase)
        def get_value(key_variants):
            for key in key_variants:
                if key in row:
                    return row[key]
            return None

        return AIUseCase(
            UseCaseName=get_value(["UseCaseName", "use_case_name", "name"]) or "",
            UseCaseID=get_value(["UseCaseID", "use_case_id", "id"]) or "",
            FunctionID=get_value(["FunctionID", "function_id"]),
            Environment=get_value(["Environment", "environment"]),
            Team=get_value(["Team", "team"]) or "",
            KeyContact=get_value(["KeyContact", "key_contact", "contact"]) or "",
            ProjectDescription=get_value(["ProjectDescription", "project_description", "description"]) or "",
            EstimatedBudgetGBP=get_value(["EstimatedBudgetGBP", "estimated_budget_gbp", "budget"]),
            BenefitValuePerAnnum=get_value(["BenefitValuePerAnnum", "benefit_value_per_annum", "benefit"]),
            AIType=get_value(["AIType", "ai_type", "type"]),
            NumberOfUsers=get_value(["NumberOfUsers", "number_of_users", "users"]),
            UsageStartDate=get_value(["UsageStartDate", "usage_start_date", "start_date"]),
            CostToDateGBP=get_value(["CostToDateGBP", "cost_to_date_gbp", "cost_to_date"]),
            LastMonthCostGBP=get_value(["LastMonthCostGBP", "last_month_cost_gbp"]),
            LastThreeMonthsCostGBP=get_value(["LastThreeMonthsCostGBP", "last_three_months_cost_gbp"]),
            LastYearCostGBP=get_value(["LastYearCostGBP", "last_year_cost_gbp"]),
            BenefitCostPerAnnum=get_value(["BenefitCostPerAnnum", "benefit_cost_per_annum"]),
            ROIPerAnnum=get_value(["ROIPerAnnum", "roi_per_annum", "roi"]),
            BudgetOverrun=get_value(["BudgetOverrun", "budget_overrun"]),
        )

    def load_all_usecases(self) -> List[AIUseCase]:
        """Load all use cases from MySQL database."""
        connection = None
        cursor = None
        try:
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)
            
            query = f"SELECT * FROM {self.table_name}"
            if settings.enable_sql_logging:
                logger.info(f"Executing SQL: {query}")
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            usecases = [self._map_row_to_usecase(row) for row in rows]
            logger.info(f"Loaded {len(usecases)} use cases from MySQL")
            
            return usecases

        except Error as e:
            logger.error(f"Error loading use cases from MySQL: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results.
        
        Args:
            sql: SQL query string
            
        Returns:
            List of dictionaries representing rows
        """
        # Safety check: ensure SQL doesn't start with JSON
        sql = sql.strip()
        if sql.startswith('{'):
            # This looks like JSON, try to extract SQL from it
            try:
                import json
                data = json.loads(sql)
                if 'sql' in data:
                    sql = data['sql'].strip()
                    logger.warning("Extracted SQL from JSON object in execute_query")
                else:
                    raise ValueError("SQL appears to be JSON but has no 'sql' field")
            except (json.JSONDecodeError, ValueError) as e:
                raise ValueError(f"Invalid SQL: appears to be JSON format: {str(e)}")
        
        connection = None
        cursor = None
        try:
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)
            
            if settings.enable_sql_logging:
                logger.info(f"Executing SQL: {sql}")
            
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            return rows

        except Error as e:
            logger.error(f"Error executing query: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_schema(self) -> Dict[str, Any]:
        """Get database schema information including relationships."""
        connection = None
        cursor = None
        try:
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Get column information for the primary table
            query = f"""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """
            cursor.execute(query, (settings.mysql_database, self.table_name))
            columns = cursor.fetchall()
            
            # Get foreign key relationships for the primary table
            fk_query = """
                SELECT 
                    CONSTRAINT_NAME,
                    COLUMN_NAME,
                    REFERENCED_TABLE_NAME,
                    REFERENCED_COLUMN_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = %s
                AND REFERENCED_TABLE_NAME IS NOT NULL
            """
            cursor.execute(fk_query, (settings.mysql_database, self.table_name))
            foreign_keys = cursor.fetchall()
            
            return {
                "table_name": self.table_name,
                "columns": columns,
                "column_count": len(columns),
                "column_names": [col["COLUMN_NAME"] for col in columns],
                "foreign_keys": foreign_keys,
            }

        except Error as e:
            logger.error(f"Error getting schema: {e}")
            return {"error": str(e)}
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_full_database_schema(self) -> Dict[str, Any]:
        """Get complete database schema including all tables and relationships."""
        connection = None
        cursor = None
        try:
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Get all tables in the database (use self.database_name for multi-DB support)
            cursor.execute("""
                SELECT TABLE_NAME, TABLE_ROWS, TABLE_COMMENT
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = %s
                AND TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """, (self.database_name,))
            tables = cursor.fetchall()
            
            # For each table, get columns
            table_schemas = {}
            for table in tables:
                table_name = table["TABLE_NAME"]
                
                # Get columns
                cursor.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_COMMENT
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                """, (self.database_name, table_name))
                columns = cursor.fetchall()
                
                # Get foreign keys
                cursor.execute("""
                    SELECT 
                        CONSTRAINT_NAME,
                        COLUMN_NAME,
                        REFERENCED_TABLE_NAME,
                        REFERENCED_COLUMN_NAME
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = %s 
                    AND TABLE_NAME = %s
                    AND REFERENCED_TABLE_NAME IS NOT NULL
                """, (self.database_name, table_name))
                foreign_keys = cursor.fetchall()
                
                table_schemas[table_name] = {
                    "columns": columns,
                    "foreign_keys": foreign_keys,
                    "row_count": table["TABLE_ROWS"],
                    "comment": table["TABLE_COMMENT"],
                }
            
            # Build relationship graph
            relationships = []
            for table_name, schema in table_schemas.items():
                for fk in schema.get("foreign_keys", []):
                    relationships.append({
                        "from_table": table_name,
                        "from_column": fk["COLUMN_NAME"],
                        "to_table": fk["REFERENCED_TABLE_NAME"],
                        "to_column": fk["REFERENCED_COLUMN_NAME"],
                        "constraint": fk["CONSTRAINT_NAME"],
                    })
            
            return {
                "database": settings.mysql_database,
                "table_count": len(tables),
                "tables": table_schemas,
                "relationships": relationships,
            }

        except Error as e:
            logger.error(f"Error getting full schema: {e}")
            return {"error": str(e)}
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the MySQL database."""
        connection = None
        cursor = None
        try:
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Get row count
            query = f"SELECT COUNT(*) as count FROM {self.table_name}"
            cursor.execute(query)
            result = cursor.fetchone()
            row_count = result["count"] if result else 0
            
            # Get schema info
            schema = self.get_schema()
            
            return {
                "source_type": "mysql",
                "host": settings.mysql_host,
                "database": settings.mysql_database,
                "table": self.table_name,
                "row_count": row_count,
                "columns": schema.get("column_names", []),
                "column_count": schema.get("column_count", 0),
            }

        except Error as e:
            logger.error(f"Error getting metadata: {e}")
            return {
                "source_type": "mysql",
                "error": str(e),
            }
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def validate_connection(self) -> bool:
        """Validate that the MySQL connection works."""
        try:
            connection = self._get_connection()
            if connection.is_connected():
                connection.close()
                return True
            return False
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            return False

    def get_source_info(self) -> Dict[str, Any]:
        """Get information about the MySQL source for display."""
        metadata = self.get_metadata()
        is_connected = self.validate_connection()
        
        return {
            "type": "MySQL Database",
            "location": f"{metadata.get('host', 'N/A')}:{settings.mysql_port}/{metadata.get('database', 'N/A')}",
            "table": metadata.get("table", "N/A"),
            "status": "Connected" if is_connected else "Connection Failed",
            "records": metadata.get("row_count", 0),
        }

# MySQL Integration Guide

This guide explains how to use MySQL as a data source for the AI Insights platform.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Database Setup](#database-setup)
5. [Configuration](#configuration)
6. [Data Migration](#data-migration)
7. [Natural Language Queries](#natural-language-queries)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The AI Insights platform now supports two data sources:

- **Excel** (default): Load data from Excel files
- **MySQL**: Connect to a MySQL database for live data access

### Key Features

✅ **Natural Language to SQL**: Ask questions in plain English  
✅ **Query Observability**: View generated SQL for every query  
✅ **Schema Introspection**: Auto-detect database structure  
✅ **Backward Compatible**: Excel functionality remains unchanged  
✅ **Connection Pooling**: Optimized database performance  

---

## Prerequisites

### System Requirements

- Python 3.12+
- MySQL Server 5.7+ or MySQL 8.0+ (recommended)
- All Python dependencies from `requirements.txt`

### Install MySQL Python Libraries

```bash
pip install mysql-connector-python pymysql sqlalchemy
```

Or install all dependencies:

```bash
pip install -r requirements.txt
```

---

## Quick Start

### 1. Set up MySQL Database

```bash
# Connect to MySQL
mysql -u root -p

# Run the schema setup script
source scripts/setup_mysql_schema.sql
```

### 2. Configure Environment

Edit your `.env` file:

```bash
# Switch to MySQL data source
DATA_SOURCE=mysql

# MySQL connection details
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=ai_insights
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_TABLE=ai_usecases

# Query observability
ENABLE_SQL_LOGGING=true
SHOW_GENERATED_SQL=true
```

### 3. Start the Application

```bash
streamlit run app.py
```

### 4. Test the Connection

Navigate to **⚙️ Configuration** tab and click **🔌 Test MySQL Connection**.

---

## Database Setup

### Option A: Use Provided Schema

The `scripts/setup_mysql_schema.sql` file contains the complete schema:

```bash
mysql -u root -p < scripts/setup_mysql_schema.sql
```

### Option B: Manual Setup

```sql
CREATE DATABASE ai_insights;
USE ai_insights;

CREATE TABLE ai_usecases (
    UseCaseID VARCHAR(50) PRIMARY KEY,
    UseCaseName VARCHAR(255) NOT NULL,
    Team VARCHAR(100) NOT NULL,
    -- ... (see full schema in setup_mysql_schema.sql)
);
```

### Database Schema

The `ai_usecases` table must have these key columns:

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `UseCaseID` | VARCHAR(50) | ✅ | Unique identifier |
| `UseCaseName` | VARCHAR(255) | ✅ | Project name |
| `Team` | VARCHAR(100) | ✅ | Team responsible |
| `ProjectDescription` | TEXT | ✅ | Detailed description |
| `EstimatedBudgetGBP` | DECIMAL(15,2) | - | Estimated budget |
| `ROIPerAnnum` | DECIMAL(15,2) | - | Annual ROI percentage |
| `Environment` | VARCHAR(50) | - | Production/Lower |
| `AIType` | VARCHAR(100) | - | AI platform type |

> **Note**: The MySQL source uses flexible column mapping and can adapt to both PascalCase (`UseCaseID`) and snake_case (`use_case_id`) column names.

---

## Configuration

### Environment Variables

All configuration is in your `.env` file:

```bash
# ===== Data Source Selection =====
DATA_SOURCE=mysql  # Options: excel, mysql

# ===== MySQL Connection =====
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=ai_insights
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_TABLE=ai_usecases

# ===== SSL/Security =====
MYSQL_SSL_ENABLED=false

# ===== Performance =====
MYSQL_CONNECTION_POOL_SIZE=5

# ===== Observability =====
ENABLE_SQL_LOGGING=true        # Log SQL queries
SHOW_GENERATED_SQL=true        # Display SQL in UI
```

### Connection Testing

Use the Configuration tab in the web UI to:
- Test database connectivity
- View schema information
- Verify table and column names
- Check record counts

---

## Data Migration

### Migrate from Excel to MySQL

If you have existing Excel data, use the migration script:

```bash
# 1. Ensure MySQL database and table exist
mysql -u root -p < scripts/setup_mysql_schema.sql

# 2. Configure .env for MySQL
# Edit DATA_SOURCE and MySQL credentials

# 3. Run migration
python scripts/migrate_excel_to_mysql.py
```

The script will:
1. Load all data from your Excel file
2. Connect to MySQL
3. Insert records (with duplicate handling)
4. Verify the migration

### Manual Data Import

You can also import data using standard MySQL tools:

```bash
# Export Excel to CSV first, then:
mysql -u root -p ai_insights -e "
LOAD DATA LOCAL INFILE 'data.csv'
INTO TABLE ai_usecases
FIELDS TERMINATED BY ','
ENCLOSED BY '\"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
"
```

---

## Natural Language Queries

### Using the NL Query Interface

1. Navigate to **💬 Natural Language Query** tab
2. Enter your question in plain English
3. Click **🔍 Execute Query**
4. View generated SQL and results

### Example Questions

**Financial Analysis:**
```
Show me all projects with ROI greater than 200%
What is the total budget by team?
Which projects are over budget?
```

**Portfolio Insights:**
```
Count projects by AI type
List all production projects
Show projects with more than 1000 users
```

**Aggregations:**
```
What is the average budget per team?
Calculate total benefits by environment
Show ROI distribution across teams
```

### SQL Observability

When `SHOW_GENERATED_SQL=true`, you'll see:

- **Generated SQL**: The actual query executed
- **Explanation**: Why this query was generated
- **Results**: Data returned
- **Row Count**: Number of records
- **Download**: CSV export of results

Example output:

```sql
-- Generated SQL
SELECT Team, AVG(EstimatedBudgetGBP) as AvgBudget
FROM ai_usecases
WHERE Environment = 'Production'
GROUP BY Team
ORDER BY AvgBudget DESC;
```

---

## Troubleshooting

### Connection Issues

**Problem**: `Connection failed`

**Solutions**:
1. Verify MySQL is running: `mysql -u root -p`
2. Check credentials in `.env`
3. Test network connectivity if remote host
4. Verify database exists: `SHOW DATABASES;`

**Problem**: `Table not found`

**Solutions**:
1. Run schema setup: `source scripts/setup_mysql_schema.sql`
2. Verify table name in `.env` matches actual table
3. Check you're connected to correct database

### Query Errors

**Problem**: `SQL syntax error`

**Solutions**:
1. Check the generated SQL (shown in UI)
2. Verify column names match your schema
3. Try simpler questions first
4. Rephrase the query

**Problem**: `No results returned`

**Solutions**:
1. Verify data exists: `SELECT COUNT(*) FROM ai_usecases;`
2. Check filter conditions aren't too restrictive
3. Review the generated SQL query

### Performance Issues

**Problem**: Slow queries

**Solutions**:
1. Add indexes to frequently queried columns
2. Increase connection pool size in `.env`
3. Optimize your MySQL server configuration
4. Use more specific queries to reduce data scanned

### Migration Issues

**Problem**: Migration script fails

**Solutions**:
1. Ensure database and table exist first
2. Check Excel file path is correct
3. Verify `.env` has MySQL credentials
4. Review error messages for specific issues

---

## Advanced Usage

### Custom Schema Mapping

The MySQL source automatically maps columns using flexible matching:

- PascalCase: `UseCaseID`, `UseCaseName`
- snake_case: `use_case_id`, `use_case_name`
- Alternative names: `name`, `description`, `budget`

### Direct SQL Queries

For advanced users, you can execute SQL directly using Python:

```python
from data_sources.mysql_source import MySQLSource

mysql = MySQLSource()
results = mysql.execute_query("SELECT * FROM ai_usecases WHERE ROIPerAnnum > 150")
```

### Query Logging

All SQL queries are logged when `ENABLE_SQL_LOGGING=true`:

```python
import logging
logging.basicConfig(level=logging.INFO)
# Queries will appear in logs
```

---

## Switching Between Excel and MySQL

You can switch data sources anytime by changing one line in `.env`:

```bash
# Use Excel
DATA_SOURCE=excel

# Use MySQL
DATA_SOURCE=mysql
```

Then restart the Streamlit application:

```bash
streamlit run app.py
```

All existing functionality (dashboards, leader insights, chat) works with both data sources!

---

## Security Best Practices

1. **Never commit `.env`**: It contains credentials
2. **Use environment-specific configs**: Different `.env` for dev/prod
3. **Enable SSL for production**: `MYSQL_SSL_ENABLED=true`
4. **Limit database user permissions**: Grant only SELECT and INSERT
5. **Use strong passwords**: For MySQL users
6. **Firewall rules**: Restrict database access to application servers

---

## Next Steps

- ✅ [View main README](README.md) for application features
- ✅ [Check API documentation](docs/) for programmatic access
- ✅ [Explore sample queries](#natural-language-queries)
- ✅ [Configure observability](#query-observability)

---

## Support

If you encounter issues:

1. Check this guide's troubleshooting section
2. Review application logs
3. Test MySQL connection independently
4. Verify schema matches expected structure

For SQL generation issues, try rephrasing your question in simpler terms or use more specific column references.

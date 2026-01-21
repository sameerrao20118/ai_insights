# Natural Language to SQL - Architecture & Data Flow

## Overview

This document explains how the system translates natural language questions into SQL queries using **declarative schema configurations** (YAML files) to guide the LLM.

---

## System Architecture

```
┌─────────────┐
│    User     │
│  "Show me   │
│  orders by  │
│  country"   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│              Streamlit UI (app_ui.py)                   │
│  - Displays database selector                           │
│  - User selects: tpch                                   │
│  - User enters question                                 │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│         MySQL Services (services_mysql.py)              │
│  query_with_nl(question, database="tpch")              │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│      Data Source Factory (factory.py)                   │
│  get_mysql_source(database="tpch")                     │
│    ↓                                                    │
│  Returns: MySQLSource instance for tpch database        │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│      NL-to-SQL Translator (nl_to_sql.py)               │
│  NLToSQLTranslator(mysql_source)                       │
│  execute_nl_query(question)                            │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│     Schema Description (_get_schema_description)        │
│                                                          │
│  Step 1: Try to load YAML config                       │
│    schema_loader = get_schema_loader()                 │
│    config = schema_loader.load_schema_config("tpch")   │
│    ↓                                                    │
│    Looks for: schemas/tpch.yaml ✅                     │
│                                                          │
│  Step 2: Format config for LLM                          │
│    schema_text = schema_loader.format_for_llm("tpch")  │
│    ↓                                                    │
│    Converts YAML → structured text prompt              │
│                                                          │
│  Step 3: Fallback if no YAML                           │
│    If no tpch.yaml exists:                             │
│    schema_text = _format_schema_for_llm(mysql_schema)  │
│    ↓                                                    │
│    Auto-generates from MySQL INFORMATION_SCHEMA        │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│         LLM Prompt Construction                         │
│                                                          │
│  System Prompt (nl_to_sql_prompt.py):                  │
│  ┌─────────────────────────────────────────┐           │
│  │ You are a SQL expert...                 │           │
│  │ ⚠️ CRITICAL RULES:                      │           │
│  │ - Case sensitive names                  │           │
│  │ - Follow FK chains                      │           │
│  │ - Don't skip intermediate tables        │           │
│  └─────────────────────────────────────────┘           │
│                                                          │
│  User Prompt:                                           │
│  ┌─────────────────────────────────────────┐           │
│  │ DATABASE SCHEMA:                        │           │
│  │                                          │           │
│  │ 📋 TABLES:                              │           │
│  │ **ORDERS**: Customer orders             │           │
│  │   - O_ORDERKEY (PRIMARY KEY)            │           │
│  │   - O_CUSTKEY (FOREIGN KEY)             │           │
│  │                                          │           │
│  │ **CUSTOMER**: Customer information      │           │
│  │   - C_CUSTKEY (PRIMARY KEY)             │           │
│  │   - C_NATIONKEY (FOREIGN KEY)           │           │
│  │                                          │           │
│  │ **NATION**: Countries                   │           │
│  │   - N_NATIONKEY (PRIMARY KEY)           │           │
│  │   - N_NAME                              │           │
│  │                                          │           │
│  │ 🔗 FOREIGN KEY RELATIONSHIPS:            │           │
│  │ • ORDERS.O_CUSTKEY → CUSTOMER.C_CUSTKEY │           │
│  │ • CUSTOMER.C_NATIONKEY → NATION.N_NATIONKEY │      │
│  │                                          │           │
│  │ 📍 PREDEFINED JOIN PATHS:               │           │
│  │ **orders_to_country**:                  │           │
│  │   FROM ORDERS                           │           │
│  │   INNER JOIN CUSTOMER ON ...            │           │
│  │   INNER JOIN NATION ON ...              │           │
│  │                                          │           │
│  │ QUESTION: Show me orders by country     │           │
│  └─────────────────────────────────────────┘           │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│              LLM (OpenAI/Gemini/etc)                    │
│  Reads the schema with JOIN paths                      │
│  Generates SQL following the explicit path              │
│                                                          │
│  Returns JSON:                                          │
│  {                                                      │
│    "sql": "SELECT o.O_ORDERKEY, n.N_NAME                │
│            FROM ORDERS o                                │
│            INNER JOIN CUSTOMER c ON o.O_CUSTKEY = c.C_CUSTKEY │
│            INNER JOIN NATION n ON c.C_NATIONKEY = n.N_NATIONKEY", │
│    "explanation": "Joins orders through customer to nation" │
│  }                                                      │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│         SQL Extraction & Validation                     │
│  extract_sql_from_response(llm_response)               │
│    ↓                                                    │
│  Validates:                                             │
│  - No dangerous keywords (DROP, DELETE, etc)            │
│  - Extracts SQL from JSON                              │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│         MySQL Execution (mysql_source.py)               │
│  execute_query(sql)                                     │
│    ↓                                                    │
│  Connects to tpch database                             │
│  Executes: SELECT o.O_ORDERKEY, n.N_NAME...            │
│  Returns: ResultSet                                     │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│           Streamlit UI Display                          │
│  ✅ Shows generated SQL                                │
│  ✅ Shows query results in table                       │
│  ✅ Shows explanation                                  │
└─────────────────────────────────────────────────────────┘
```

---

## Key Components Deep Dive

### 1. Schema Config Loader (`schema_config.py`)

**Purpose**: Load and format YAML schema configurations

**Flow**:
```python
# Step 1: User selects database "tpch"
schema_loader = get_schema_loader()

# Step 2: Load YAML file
config = schema_loader.load_schema_config("tpch")
# Reads: schemas/tpch.yaml

# Step 3: Format for LLM
schema_text = schema_loader.format_for_llm("tpch")
# Converts YAML structure to formatted text
```

**YAML Structure** (`schemas/tpch.yaml`):
```yaml
database:
  name: tpch
  description: "TPC-H benchmark database"

tables:
  ORDERS:
    description: "Customer orders"
    primary_key: O_ORDERKEY
    important_columns:
      - O_CUSTKEY: "Foreign key to CUSTOMER"
    foreign_keys:
      - column: O_CUSTKEY
        references: CUSTOMER.C_CUSTKEY

join_paths:
  orders_to_country:
    description: "Get country for an order"
    path:
      - from: ORDERS
        to: CUSTOMER
        on: "ORDERS.O_CUSTKEY = CUSTOMER.C_CUSTKEY"
      - from: CUSTOMER
        to: NATION
        on: "CUSTOMER.C_NATIONKEY = NATION.N_NATIONKEY"
    example: "Show orders by country"
```

**Output** (formatted text for LLM):
```
=== TPC-H BENCHMARK DATABASE ===

📋 TABLES:

**ORDERS**: Customer orders
  Primary Key: O_ORDERKEY
  Key Columns:
    - O_CUSTKEY: Foreign key to CUSTOMER

**CUSTOMER**: Customer information
  Primary Key: C_CUSTKEY
  Key Columns:
    - C_NATIONKEY: Foreign key to NATION

🔗 PREDEFINED JOIN PATHS:

**orders_to_country**: Get country for an order
  Example question: "Show orders by country"
  SQL Pattern:
    FROM ORDERS
    INNER JOIN CUSTOMER ON ORDERS.O_CUSTKEY = CUSTOMER.C_CUSTKEY
    INNER JOIN NATION ON CUSTOMER.C_NATIONKEY = NATION.N_NATIONKEY
```

---

### 2. NL-to-SQL Translator (`nl_to_sql.py`)

**Method**: `_get_schema_description()`

```python
def _get_schema_description(self) -> str:
    # Cache schema for performance
    if self.schema_cache is None:
        self.schema_cache = self.mysql_source.get_full_database_schema()
    
    # TRY: Load declarative config first
    try:
        schema_loader = get_schema_loader()
        db_name = self.mysql_source.database_name  # "tpch"
        schema_text = schema_loader.format_for_llm(db_name)
        
        if schema_text:
            logger.info(f"Using declarative config for {db_name}")
            return schema_text  # ← Returns YAML-based schema
    except Exception as e:
        logger.warning(f"Could not load config: {e}")
    
    # FALLBACK: Auto-generate from MySQL
    logger.info("Using auto-generated schema")
    return self._format_schema_for_llm(self.schema_cache)
```

**Key Point**: YAML config **takes priority** over auto-generated schema!

---

### 3. LLM Prompt Construction

**System Prompt** (`nl_to_sql_prompt.py`):
- Generic rules (case sensitivity, FK chains, etc.)
- **No database-specific examples**

**User Prompt**:
```
<schema_text from tpch.yaml>

QUESTION: Show me orders by country

Generate MySQL query...
```

**LLM Sees**:
1. **Exact table names**: ORDERS, CUSTOMER, NATION
2. **FK relationships**: ORDERS.O_CUSTKEY → CUSTOMER.C_CUSTKEY
3. **Pre-defined JOIN path**: Complete path from ORDERS to NATION
4. **Example question**: "Show orders by country" (matches user query!)

**Result**: LLM follows the explicit JOIN path from YAML!

---

## Why This Works

### Problem (Before YAML):
LLM would see this auto-generated schema:
```
ORDERS (O_CUSTKEY)
CUSTOMER (C_CUSTKEY, C_NationKEY)
NATION (N_NATIONKEY)

FK: ORDERS.O_CUSTKEY → CUSTOMER.C_CUSTKEY
FK: CUSTOMER.C_NATIONKEY → NATION.N_NATIONKEY
```

**LLM's mistake**: "I see both ORDERS and NATION have key columns, let me join them directly!"
```sql
-- WRONG (skips CUSTOMER):
FROM ORDERS o JOIN NATION n ON o.O_CUSTKEY = n.N_NATIONKEY
```

### Solution (With YAML):
LLM sees explicit JOIN path:
```
orders_to_country:
  Example: "Show orders by country"
  FROM ORDERS
  INNER JOIN CUSTOMER ON ORDERS.O_CUSTKEY = CUSTOMER.C_CUSTKEY
  INNER JOIN NATION ON CUSTOMER.C_NATIONKEY = NATION.N_NATIONKEY
```

**LLM's decision**: "Perfect! This matches the user's question. I'll use this exact path."
```sql
-- CORRECT (follows complete path):
FROM ORDERS o 
INNER JOIN CUSTOMER c ON o.O_CUSTKEY = c.C_CUSTKEY
INNER JOIN NATION n ON c.C_NATIONKEY = n.N_NATIONKEY
```

---

## File Locations

```
ai_insights/
├── schemas/                        # ← YAML configs
│   ├── tpch.yaml                  # TPC-H schema
│   ├── ai_insights.yaml           # AI Insights schema
│   ├── template.yaml              # Template for new DBs
│   └── README.md                  # How to add new DBs
│
├── data_sources/
│   ├── schema_config.py           # ← YAML loader
│   ├── nl_to_sql.py               # ← Uses schema loader
│   ├── nl_to_sql_prompt.py        # Generic prompt
│   └── mysql_source.py            # DB connection
│
└── app_ui.py                      # UI entry point
```

---

## Adding a New Database

**1. Create YAML config**:
```bash
cp schemas/template.yaml schemas/my_db.yaml
```

**2. Define schema**:
```yaml
database:
  name: my_db

tables:
  users:
    primary_key: id
  
join_paths:
  orders_to_users:
    path:
      - from: orders
        to: users
        on: "orders.user_id = users.id"
```

**3. That's it!** System automatically:
- Detects `my_db.yaml` when user selects `my_db` database
- Loads YAML and formats for LLM
- LLM generates queries using defined JOIN paths

---

## Summary

**The Flow**:
1. User selects database → "tpch"
2. System looks for `schemas/tpch.yaml` → ✅ Found
3. YAML loaded and formatted → Structured text with JOIN paths
4. Text sent to LLM as part of prompt
5. LLM reads JOIN paths and generates correct SQL
6. SQL executed → Results displayed

**Key Insight**: YAML acts as a "guide" for the LLM, showing it the **correct** way to join tables, preventing common mistakes like skipping intermediate tables.

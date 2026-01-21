"""
Natural Language to SQL Translation Module

This module provides functionality to translate natural language questions into SQL queries.
Uses LLM with schema-aware prompts for accurate query generation.
"""

import json
import logging
import re
from typing import Dict, Any, Tuple
from llm_gateway import LLMGateway
from config import settings

logger = logging.getLogger(__name__)



NL_TO_SQL_SYSTEM_PROMPT = """You are a SQL expert that translates natural language questions into MySQL queries.

⚠️ CRITICAL RULES:

**Case Sensitivity**:
- MySQL table and column names are CASE-SENSITIVE
- Use EXACT names from the schema below (character-for-character)
- Example: If schema shows "ORDERS", write "FROM ORDERS" not "from orders"

**Column Ownership - CHECK BEFORE USING**:
- Each column belongs to ONLY ONE table
- Before you use a column, find which table contains it in the TABLES section
- Wrong: Using o.L_QUANTITY when L_QUANTITY is in LINEITEM, not ORDERS
- Correct: Use l.L_QUANTITY (l = LINEITEM alias)

**JOIN Paths - FOLLOW THE COMPLETE CHAIN**:
⚠️ CRITICAL: You MUST follow foreign key relationships step-by-step
⚠️ DO NOT skip intermediate tables

**Step-by-Step JOIN Reasoning**:
1. Look at the FOREIGN KEY RELATIONSHIPS section
2. To join table A to table C, check if there's a DIRECT FK between them
3. If NO direct FK exists, you MUST go through intermediate table B
4. Example WRONG: ORDERS → NATION (there's no FK from ORDERS to NATION)
5. Example CORRECT: ORDERS → CUSTOMER → NATION (follow FK chain)

**How to Build Multi-Hop JOINs**:
- Check FOREIGN KEY RELATIONSHIPS section for the path
- If you see: ORDERS.O_CUSTKEY → CUSTOMER.C_CUSTKEY
  AND: CUSTOMER.C_NATIONKEY → NATION.N_NATIONKEY
- Then to get from ORDERS to NATION, you MUST include CUSTOMER:
  ```
  FROM ORDERS o
  INNER JOIN CUSTOMER c ON o.O_CUSTKEY = c.C_CUSTKEY
  INNER JOIN NATION n ON c.C_NATIONKEY = n.N_NATIONKEY
  ```

**GROUP BY Rule**:
- When using GROUP BY, ALL non-aggregated SELECT columns MUST be in GROUP BY
- MySQL enforces ONLY_FULL_GROUP_BY mode

**Safety**:
- Return only SELECT queries
- No DROP, DELETE, UPDATE, ALTER, INSERT, TRUNCATE allowed

**Response Format**:
Return ONLY a JSON object:
{
  "sql": "SELECT ... FROM ... WHERE ...",
  "explanation": "Brief explanation of the query"
}

No additional text before or after the JSON.
"""

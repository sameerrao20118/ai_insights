#!/usr/bin/env python3
"""
Debug script to check what schema is being sent to the LLM
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_sources.factory import get_mysql_source
from data_sources.nl_to_sql import NLToSQLTranslator

# Get tpch schema
print("=" * 60)
print("Checking tpch database schema...")
print("=" * 60)

source = get_mysql_source(database='tpch')
schema = source.get_full_database_schema()

print(f"\nDatabase: {source.database_name}")
print(f"Total tables: {schema.get('table_count', 0)}")
print("\nTable names (exact case):")

if 'table_schemas' in schema:
    for table_name in schema['table_schemas'].keys():
        print(f"  - '{table_name}' (type: {type(table_name).__name__})")
        
    # Check specific table
    if 'ORDERS' in schema['table_schemas']:
        print("\n✅ Found 'ORDERS' (uppercase)")
    elif 'orders' in schema['table_schemas']:
        print("\n❌ Found 'orders' (lowercase) - THIS IS THE PROBLEM")
    else:
        print("\n⚠️  No orders table found at all!")

# Test translator
print("\n" + "=" * 60)
print("Testing NL-to-SQL Translator...")
print("=" * 60)

translator = NLToSQLTranslator(source)
print(f"\nSchema passed to LLM includes these tables:")
# The translator formats the schema - let's see what it sends
schema_text = translator._format_schema_for_llm(schema)
print(schema_text[:500] + "...")

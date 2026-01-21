# Handling Schema Evolution

## Overview

The AI Insights platform is designed to **gracefully handle database schema changes** without requiring code modifications or application restarts. This document explains how the system adapts to schema evolution.

---

## Dynamic Schema Detection

### Automatic Discovery

The system uses **runtime schema introspection** rather than hardcoded table definitions:

```python
# NO hardcoded schemas - everything discovered at runtime
schema = mysql_source.get_full_database_schema()
# Returns: all tables, columns, relationships discovered dynamically
```

**What Gets Detected**:
- ✅ All tables in the database
- ✅ All columns with types and constraints
- ✅ Primary keys
- ✅ Foreign key relationships
- ✅ Column comments/descriptions
- ✅ Table row counts

---

## Schema Change Scenarios

### 1. Adding a New Table

**Scenario**: You add a `suppliers` table to your database

**System Behavior**:
- ✅ Automatically discovered on next schema refresh
- ✅ Available for queries immediately
- ✅ Foreign keys to/from this table detected
- ✅ LLM can generate JOINs involving this table

**Action Required**: Click "🔄 Refresh Schema Cache" in Configuration tab

**Example**:
```sql
-- Add new table
CREATE TABLE suppliers (
    supplier_id INT PRIMARY KEY,
    supplier_name VARCHAR(255),
    country VARCHAR(100)
);

-- Add relationship
ALTER TABLE products 
ADD COLUMN supplier_id INT,
ADD FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id);
```

Then refresh cache, and you can immediately ask:
- "Which products come from suppliers in USA?"
- "Show supplier names for all products"

---

### 2. Adding New Columns

**Scenario**: You add `discount_percentage` to the `products` table

**System Behavior**:
- ✅ New column detected on refresh
- ✅ Available in SELECT queries
- ✅ Can be used in WHERE clauses
- ✅ Supports aggregations

**Action Required**: Refresh schema cache

**Example**:
```sql
ALTER TABLE products 
ADD COLUMN discount_percentage DECIMAL(5,2) DEFAULT 0;
```

After refresh:
- "Show products with discounts over 10%"
- "What's the average discount by category?"

---

### 3. Removing Columns

**Scenario**: You deprecate the `old_price` column

**System Behavior**:
- ✅ Removed from schema automatically
- ✅ Queries won't reference this column
- ⚠️ Old cached queries might fail (cache is cleared)

**Action** Required**: Refresh schema cache

**Best Practice**: 
- Refresh cache after ALTER TABLE operations
- Test queries that previously used removed columns

---

### 4. Changing Relationships

**Scenario**: You modify foreign key constraints

**System Behavior**:
- ✅ New relationships detected
- ✅ JOIN suggestions updated
- ✅ Relationship graph rebuilt

**Example**:
```sql
-- Drop old FK
ALTER TABLE orders DROP FOREIGN KEY orders_ibfk_1;

-- Add new FK with different column
ALTER TABLE orders 
ADD COLUMN warehouse_id INT,
ADD FOREIGN KEY (warehouse_id) REFERENCES warehouses(id);
```

After refresh, queries automatically adapt:
- "Which warehouse fulfilled each order?"
- "Total orders by warehouse"

---

## Schema Refresh Mechanisms

### Manual Refresh (UI)

**Steps**:
1. Navigate to **⚙️ Configuration** tab
2. Scroll to "Database Schema" section
3. Click **🔄 Refresh Schema Cache** button
4. Wait for confirmation

**When to Use**:
- After adding/removing tables
- After modifying columns
- After changing foreign keys
- When queries fail unexpectedly
- During development/testing

### Programmatic Refresh (API)

```python
from services_mysql import refresh_schema_cache

# Refresh in your code
result = refresh_schema_cache()

if result['success']:
    print(f"Schema refreshed: {result['table_count']} tables")
else:
    print(f"Refresh failed: {result['error']}")
```

### Automatic Refresh (On Error)

The system **does not** automatically refresh on query errors to avoid performance overhead. Manual refresh is recommended.

---

## Schema Cache Behavior

### How Caching Works

```python
# First query - loads schema
translator = NLToSQLTranslator(mysql_source)
sql1 = translator.translate_to_sql("Show customers")
# Schema loaded and cached

# Subsequent queries - uses cache
sql2 = translator.translate_to_sql("Show orders")
# Same schema reused (fast)

# Manual refresh - clears cache
translator.refresh_schema()
# Next query reloads schema
```

### Cache Lifetime

- **Duration**: Until manual refresh or application restart
- **Scope**: Per NLToSQLTranslator instance
- **Storage**: In-memory (not persisted)

### Cache Contents

```python
{
    "database": "your_db",
    "table_count": 8,
    "tables": {
        "customers": {...},
        "orders": {...}
    },
    "relationships": [...]
}
```

---

## Best Practices

### Development Workflow

```bash
# 1. Modify schema
mysql> ALTER TABLE products ADD COLUMN weight DECIMAL(10,2);

# 2. Refresh cache via UI or:
python -c "from services_mysql import refresh_schema_cache; refresh_schema_cache()"

# 3. Test queries
# Ask: "Show products heavier than 5kg"
```

### Production Deployments

**Before Schema Migration**:
1. Plan downtime if relationships change significantly
2. Test queries with new schema in staging
3. Document new columns/tables for users

**During Migration**:
1. Apply schema changes
2. Refresh cache immediately
3. Monitor query errors

**After Migration**:
1. Validate key queries still work
2. Update documentation
3. Notify users of new query capabilities

### Backward Compatibility

**Safe Changes** (no refresh needed immediately):
- Adding nullable columns
- Adding new tables (if not queried)
- Adding indexes

**Breaking Changes** (require refresh):
- Removing columns
- Renaming columns
- Dropping tables
- Modifying foreign keys

---

## Troubleshooting

### Issue: Queries fail after schema change

**Symptom**: "Column not found" or "Table doesn't exist"

**Solution**:
```
1. Click 🔄 Refresh Schema Cache
2. Retry the query
3. Check SQL generated uses new column names
```

### Issue: New table not appearing in queries

**Symptom**: LLM doesn't know about new table

**Solution**:
```
1. Verify table exists: SHOW TABLES;
2. Refresh schema cache
3. Try explicit question: "Show all data from newtable"
```

### Issue: Relationship not detected

**Symptom**: JOIN not generated correctly

**Solution**:
```
1. Verify FK exists:
   SELECT * FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
   WHERE TABLE_SCHEMA = 'your_db';

2. If missing, add FK:
   ALTER TABLE child ADD FOREIGN KEY (parent_id) 
   REFERENCES parent(id);

3. Refresh schema cache
```

### Issue: Old column still in queries

**Symptom**: SQL references dropped column

**Solution**:
```
1. Clear browser cache (Streamlit session state)
2. Refresh schema cache
3. Restart application if needed
```

---

## Schema Versioning (Advanced)

### Tracking Schema Changes

While not built-in, you can track schema versions:

```sql
CREATE TABLE schema_versions (
    version INT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_versions (version, description)
VALUES (2, 'Added suppliers table and relationships');
```

### Migration Scripts

```bash
# migrations/002_add_suppliers.sql
START TRANSACTION;

CREATE TABLE suppliers (...);
ALTER TABLE products ADD COLUMN supplier_id INT;
ALTER TABLE products ADD FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id);

INSERT INTO schema_versions (version, description)
VALUES (2, 'Added suppliers table');

COMMIT;
```

After running migration:
1. Execute migration script
2. Refresh schema cache
3. Test queries

---

## Performance Considerations

### Schema Introspection Cost

**Impact**: Loading full schema queries `INFORMATION_SCHEMA`

**Optimization**:
- Schema is cached after first load
- Only refreshed manually
- Typical load time: 100-500ms for 10-50 tables

**For Large Databases** (100+ tables):
- Consider limiting scope to specific schema
- Use database views to expose subset
- Refresh only when needed

### Query Performance

Schema changes don't affect query performance if:
- Indexes maintained on FK columns
- Table statistics updated regularly: `ANALYZE TABLE tablename;`

---

## FAQ

**Q: Do I need to restart the application after schema changes?**  
A: No, just click "Refresh Schema Cache" in the Configuration tab.

**Q: Will existing queries break if I add a column?**  
A: No, adding columns is backward compatible.

**Q: How often should I refresh the cache?**  
A: Only after schema changes. There's no need for periodic refresh.

**Q: Can I use the system while schema is being modified?**  
A: Yes, but refresh cache immediately after changes complete.

**Q: What if I rename a table?**  
A: Rename is equivalent to drop + add. Refresh cache, and all queries adapt to new name.

**Q: Does schema refresh affect other users?**  
A: In Streamlit, each user has their own session. Refresh is per-session unless using shared backend.

---

## Summary

✅ **Dynamic Schema Detection**: No hardcoded table/column definitions  
✅ **Automatic Relationship Discovery**: Foreign keys detected via INFORMATION_SCHEMA  
✅ **Manual Refresh**: One-click schema cache update  
✅ **Zero Downtime**: No application restart needed  
✅ **Flexible Column Mapping**: Handles PascalCase and snake_case  
✅ **Graceful Degradation**: Falls back safely on errors  

The system is designed to **grow with your database** without code changes!

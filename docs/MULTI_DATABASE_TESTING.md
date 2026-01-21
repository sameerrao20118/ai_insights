# Multi-Database Support - Quick Test Guide

## What's Implemented

✅ **UI Database Selector** - Dropdown in sidebar to switch databases  
✅ **Session State Management** - Database selection persists within session  
✅ **Multi-Database Backend** - MySQLSource, Factory, and Services support database parameter  
✅ **Natural Language Queries** - Works with selected database  
✅ **Schema Auto-Detection** - Per-database schema caching  

---

## Quick Test (5 minutes)

### 1. Start the App

```bash
cd /Users/sameera/code/talktodata/ai_insights
streamlit run app.py
```

### 2. Create TPC-H Database (Currently in Docker)

The TPC-H schema is partially created. To complete it:

```bash
# Add to docker-compose or run manually
docker exec -i ai_insights_mysql mysql -uai_user -pai_password < scripts/tpch_schema.sql
```

### 3. Test Database Switching

1. Open sidebar in Streamlit
2. Look for **"📊 Database Selection"** dropdown
3. Switch between:
   - `ai_insights` (e-commerce schema)
   - `tpch` (will show when created)

### 4. Test Natural Language Queries

**In ai_insights database:**
- "Show all customers"
- "Which products have the most sales?"

**In tpch database:**  
- "Show all nations by region"
- "List customers by market segment"

---

## How It Works

```
User selects database in UI
        ↓
Streamlit session_state updated
        ↓
get_current_database() reads session state
        ↓
services_mysql.query_with_nl(question, database=selected_db)
        ↓
Per-database MySQLSource & NLToSQLTranslator instances
        ↓
Schema-specific query generation
```

---

## What's Next

To fully test with TPC-H:

1. **Complete TPC-H Schema** - Need to add remaining tables (supplier, part, orders, lineitem)
2. **Generate Sample Data** - 100+ rows per table
3. **Test Complex Queries** - Multi-table JOINs across TPC-H schema
4. **Add More Databases** - Easy to extend (Northwind, Sakila, etc.)

---

## File Changes

| File | Change |
|------|--------|
| `ui_components/database_selector.py` | New - UI component with session state |
| `data_sources/mysql_source.py` | Added `database` parameter to `__init__` |
| `data_sources/factory.py` | Per-database singleton pattern |
| `services_mysql.py` | All functions accept `database` parameter |
| `app_ui.py` | Integrated selector in sidebar, updated NL tab |
| `scripts/tpch_schema.sql` | Partial TPC-H schema (region, nation, 150 customers) |

---

## Known Limitations

1. **TPC-H Dataset Incomplete** - Only 3/8 tables with data
2. **No Cross-Database Queries** - Can only query one DB at a time
3. **Manual Docker Setup** - TPC-H not auto-loaded on init

These are easy to address as needed!

# Multi-Table Query Capability - Documentation

## Overview

The AI Insights platform now supports **intelligent multi-table queries** across complex relational databases. The LLM automatically detects table relationships and generates appropriate JOIN queries based on your natural language questions.

---

## Key Features

✅ **Automatic Relationship Detection**: Discovers foreign keys and table relationships  
✅ **Multi-Table JOIN Generation**: Creates complex JOIN queries automatically  
✅ **Relationship-Aware Prompts**: LLM understands your data model  
✅ **Full Database Schema Introspection**: Maps entire database structure  
✅ **Intelligent Query Routing**: Determines which tables to query  
✅ **Comprehensive Testing**: 10+ test scenarios validate  functionality

---

## How It Works

### 1. Schema Introspection

The system automatically:
- Discovers all tables in your database
- Maps all columns with data types
- Detects PRIMARY KEY and FOREIGN KEY relationships
- Builds a complete relationship graph

### 2. Natural Language Understanding

When you ask a question, the LLM:
- Analyzes which tables contain relevant data
- Identifies the relationships between those tables
- Determines the shortest JOIN path
- Generates appropriate SQL with JOINs

### 3. SQL Generation

The system generates:
- **INNER JOINs** for required relationships
- **LEFT JOINs** for optional data
- **Multi-table JOINs** when needed (3+ tables)
- **Aggregations** across joined tables
- **Filtering** on any table in the JOIN

---

## Example Queries

### Simple 2-Table JOIN

**Question**: "Show me all customers and their orders"

**Generated SQL**:
```sql
SELECT c.first_name, c.last_name, o.order_id, o.total_amount, o.status
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
ORDER BY o.order_date DESC;
```

**Tables Used**: `customers`, `orders`

---

### 3-Table JOIN

**Question**: "List all products ordered with customer names"

**Generated SQL**:
```sql
SELECT c.first_name, c.last_name, p.product_name, oi.quantity
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
INNER JOIN order_items oi ON o.order_id = oi.order_id
INNER JOIN products p ON oi.product_id = p.product_id
ORDER BY c.last_name;
```

**Tables Used**: `customers`, `orders`, `order_items`, `products`

---

### Aggregation with JOIN

**Question**: "What is the total revenue by customer?"

**Generated SQL**:
```sql
SELECT 
    c.first_name,
    c.last_name,
    SUM(o.total_amount) as total_revenue
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name
ORDER BY total_revenue DESC;
```

**Tables Used**: `customers`, `orders`

---

### Complex 5-Table JOIN

**Question**: "Which customers have ordered electronics products?"

**Generated SQL**:
```sql
SELECT DISTINCT 
    c.first_name,
    c.last_name,
    c.email
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
INNER JOIN order_items oi ON o.order_id = oi.order_id
INNER JOIN products p ON oi.product_id = p.product_id
INNER JOIN categories cat ON p.category_id = cat.category_id
WHERE cat.category_name = 'Electronics'
ORDER BY c.last_name;
```

**Tables Used**: `customers`, `orders`, `order_items`, `products`, `categories`

---

## Testing & Validation

### Test Schema

A comprehensive test schema is provided in [`scripts/test_multi_table_schema.sql`](file:///Users/sameera/code/talktodata/ai_insights/scripts/test_multi_table_schema.sql):

**Tables**:
- `categories` - Product categories
- `products` - Product catalog (FK to categories)
- `customers` - Customer information
- `orders` - Customer orders (FK to customers)
- `order_items` - Order line items (FK to orders and products)
- `reviews` - Product reviews (FK to products and customers)

**Relationships**:
```
categories ← products → order_items → orders → customers
              ↓
            reviews ← customers
```

### Setup Test Database

```bash
# Load test schema
mysql -u root -p < scripts/test_multi_table_schema.sql

# This creates sample data for:
# - 4 categories
# - 8 products
# - 5 customers
# - 7 orders
# - 14 order items
# - 8 reviews
```

### Run Validation Tests

```bash
# Execute comprehensive test suite
python scripts/validate_multi_table_queries.py
```

**Test Scenarios**:
1. Simple 2-table JOIN
2. 3-table JOIN
3. Aggregation with JOIN
4. LEFT JOIN for optional data
5. Complex 5-table query
6. Multi-table aggregation
7. Top N queries
8. HAVING clause with aggregation
9. Name-based filtering
10. Category performance analysis

**Expected Results**:
- All 10 tests should generate valid SQL
- Queries should execute successfully
- Correct tables identified and joined
- Results returned accurately

---

## Query Patterns Supported

### Pattern 1: Customer-Order Queries

```
"Show orders for customer X"
"What did customer Y purchase?"
"Total spending by customer"
```

### Pattern 2: Product-Category Queries

```
"List all electronics products"
"What products are in category X?"
"Average price by category"
```

### Pattern 3: Review Analysis

```
"Products with ratings above 4 stars"
"Which customers reviewed product X?"
"Average rating by product"
```

### Pattern 4: Sales Analytics

```
"Top selling products"
"Revenue by category"
"Customers who never ordered"
```

### Pattern 5: Complex Relationships

```
"Customers who ordered from multiple categories"
"Products ordered together"
"Repeat customers analysis"
```

---

## Implementation Details

### Enhanced MySQL Source

[`data_sources/mysql_source.py`](file:///Users/sameera/code/talktodata/ai_insights/data_sources/mysql_source.py)

**New Method**: `get_full_database_schema()`
```python
def get_full_database_schema() -> Dict[str, Any]:
    """
    Returns:
    - All tables with columns
    - Foreign key relationships
    - Relationship graph
    - Row counts
    """
```

**Schema Output**:
```python
{
    "database": "your_database",
    "table_count": 6,
    "tables": {
        "customers": {
            "columns": [...],
            "foreign_keys": [],
            "row_count": 100
        },
        "orders": {
            "columns": [...],
            "foreign_keys": [
                {"column": "customer_id", "references": "customers.customer_id"}
            ],
            "row_count": 450
        }
    },
    "relationships": [
        {
            "from_table": "orders",
            "from_column": "customer_id",
            "to_table": "customers",
            "to_column": "customer_id"
        }
    ]
}
```

### Enhanced NL-to-SQL Translator

[`data_sources/nl_to_sql.py`](file:///Users/sameera/code/talktodata/ai_insights/data_sources/nl_to_sql.py)

**Updated System Prompt**:
- Instructs LLM on JOIN strategies
- Emphasizes relationship analysis
- Provides JOIN examples
- Explains when to use INNER vs LEFT JOIN

**Schema Description Format**:
```
Database: ecommerce
Total Tables: 6

--- Table: customers ---
Rows: ~100
Columns:
  - customer_id: int NOT NULL [PRIMARY KEY]
  - first_name: varchar NOT NULL
  - email: varchar NOT NULL

--- Table: orders ---
Rows: ~450
Columns:
  - order_id: int NOT NULL [PRIMARY KEY]
  - customer_id: int NOT NULL [FOREIGN KEY]
  - total_amount: decimal NOT NULL

FOREIGN KEY RELATIONSHIPS:
  orders.customer_id → customers.customer_id
  order_items.order_id → orders.order_id
  order_items.product_id → products.product_id
```

---

## Best Practices

### 1. Question Formulation

**Good Questions** (Specific and clear):
- "Show customers who ordered electronics"
- "What is the average order value by customer?"
- "List products never reviewed"

**Avoid** (Ambiguous):
- "Show me everything"
- "What about orders?"
- "Data analysis"

### 2. Table Naming

Use clear, descriptive table names that the LLM can understand:
- `customers` not `cust` or `c1`
- `order_items` not `oi_tbl`
- `product_categories` not `pc`

### 3. Column Naming

Use consistent, semantic column names:
- `customer_id` not `cust_id` or `c_id`
- `total_amount` not `amt` or `tot`
- `created_at` not `ts` or `date1`

### 4. Relationship Definitions

Always define foreign keys explicitly:
```sql
FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
```

The system relies on these to generate JOINs.

---

## Troubleshooting

### Issue: Generated SQL missing tables

**Cause**: Question too vague or relationships not detected

**Solution**:
1. Check foreign keys exist: `SHOW CREATE TABLE your_table;`
2. Be more specific in question
3. Mention table names explicitly

### Issue: Incorrect JOIN type

**Cause**: LLM misunderstood required vs optional relationship

**Solution**:
1. Specify "all X including those without Y" for LEFT JOIN
2. Use "only X that have Y" for INNER JOIN

### Issue: Circular JOIN or cartesian product

**Cause**: Multiple possible join paths

**Solution**:
1. Be specific about which relationship to use
2. Simplify question to fewer tables
3. Check for duplicateforeign keys

---

## Performance Considerations

### Indexes

For optimal performance, create indexes:
```sql
-- On foreign key columns
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_order_items_order ON order_items(order_id);

-- On commonly filtered columns
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_orders_status ON orders(status);
```

### Query Optimization

The system generates standard SQL. You can:
1. Add `LIMIT` clauses for large datasets
2. Use `EXPLAIN` to analyze query plans
3. Optimize slow queries manually

---

## Next Steps

1. **Load Test Schema**: `mysql < scripts/test_multi_table_schema.sql`
2. **Run Validation**: `python scripts/validate_multi_table_queries.py`
3. **Try Your Own DB**: Configure .env with your database
4. **Ask Questions**: Use Natural Language Query tab in UI
5. **Review Generated SQL**: Check observability panel

---

## References

- [Main README](../README.md)
- [MySQL Setup Guide](MYSQL_SETUP.md)
- [Test Schema](../scripts/test_multi_table_schema.sql)
- [Validation Script](../scripts/validate_multi_table_queries.py)

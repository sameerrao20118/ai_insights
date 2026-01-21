# Simple TPC-H Test Queries

## Test 1: Basic Count (No JOINs)
**Question**: "Count all orders"
**Expected SQL**: 
```sql
SELECT COUNT(*) FROM ORDERS
```

## Test 2: Simple Filter
**Question**: "Show me 5 orders"
**Expected SQL**:
```sql
SELECT * FROM ORDERS LIMIT 5
```

## Test 3: Single JOIN
**Question**: "Show orders with customer names"
**Expected SQL**:
```sql
SELECT o.O_ORDERKEY, c.C_NAME
FROM ORDERS o
INNER JOIN CUSTOMER c ON o.O_CUSTKEY = c.C_CUSTKEY
LIMIT 10
```

## Test 4: Two JOINs
**Question**: "Show orders with customer and their country"
**Expected SQL**:
```sql
SELECT o.O_ORDERKEY, c.C_NAME, n.N_NAME
FROM ORDERS o
INNER JOIN CUSTOMER c ON o.O_CUSTKEY = c.C_CUSTKEY
INNER JOIN NATION n ON c.C_NATIONKEY = n.N_NATIONKEY
LIMIT 10
```

## Test 5: Complex (Your Original Query)
**Question**: "Show me the orders which was placed with maximum quantity and the orders came from which country"
**Expected SQL**:
```sql
SELECT o.O_ORDERKEY, n.N_NAME, l.L_QUANTITY
FROM LINEITEM l
INNER JOIN ORDERS o ON l.L_ORDERKEY = o.O_ORDERKEY
INNER JOIN CUSTOMER c ON o.O_CUSTKEY = c.C_CUSTKEY
INNER JOIN NATION n ON c.C_NATIONKEY = n.N_NATIONKEY
ORDER BY l.L_QUANTITY DESC
LIMIT 1
```

---

## How to Test

1. Start with Test 1 (simplest)
2. If it works, try Test 2
3. Progress through each test
4. Find where it breaks

This will tell us if the issue is:
- Basic queries (Tests 1-2)
- Single JOINs (Test 3)
- Multi-JOINs (Test 4)
- Complex multi-table (Test 5)

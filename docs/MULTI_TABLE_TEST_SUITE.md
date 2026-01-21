# Multi-Table Query Test Suite

This document contains complex SQL queries spanning multiple tables that you can use to test and validate the natural language to SQL translation feature.

## How to Use This Guide

1. **Run SQL in Adminer** - Execute the SQL query to see expected results
2. **Ask in Natural Language** - Use the NL question in the AI Insights app
3. **Compare Results** - Verify the app generates similar SQL and returns matching data

---

## Test 1: Customer Orders with Product Details

### SQL Query
```sql
SELECT 
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    o.order_id,
    o.order_date,
    p.product_name,
    oi.quantity,
    oi.unit_price,
    oi.subtotal
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
ORDER BY o.order_date DESC, customer_name;
```

### Natural Language Questions to Try
- "Show me all customers with their orders and products"
- "List customer names with their ordered products"
- "What products did each customer order?"

### Expected Results
- **Tables Joined**: 4 (customers, orders, order_items, products)
- **Rows**: ~14 (one per order item)
- **Columns**: Customer name, order details, product info

---

## Test 2: Electronics Orders by Customer

### SQL Query
```sql
SELECT DISTINCT
    c.first_name,
    c.last_name,
    c.email,
    o.order_id,
    o.total_amount,
    cat.category_name
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
JOIN categories cat ON p.category_id = cat.category_id
WHERE cat.category_name = 'Electronics'
ORDER BY c.last_name;
```

### Natural Language Questions to Try
- "Which customers ordered electronics?"
- "Show me customers who bought electronics products"
- "List all electronics orders with customer details"

### Expected Results
- **Tables Joined**: 5 (customers, orders, order_items, products, categories)
- **Rows**: ~2-3 (John Doe, Alice Williams)
- **Category**: Only Electronics

---

## Test 3: Product Revenue by Category

### SQL Query
```sql
SELECT 
    cat.category_name,
    COUNT(DISTINCT p.product_id) AS total_products,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    SUM(oi.quantity) AS items_sold,
    SUM(oi.subtotal) AS total_revenue
FROM categories cat
LEFT JOIN products p ON cat.category_id = p.category_id
LEFT JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY cat.category_id, cat.category_name
ORDER BY total_revenue DESC;
```

### Natural Language Questions to Try
- "What is the total revenue by category?"
- "Show sales performance by product category"
- "How much revenue did each category generate?"

### Expected Results
- **Tables Joined**: 3 (categories, products, order_items)
- **Rows**: 4 (one per category)
- **Aggregations**: COUNT, SUM
- **Top Category**: Electronics (highest revenue)

---

## Test 4: Customer Spending Analysis

### SQL Query
```sql
SELECT 
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    c.loyalty_points,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(o.total_amount) AS total_spent,
    AVG(o.total_amount) AS avg_order_value,
    MAX(o.order_date) AS last_order_date
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status != 'cancelled' OR o.status IS NULL
GROUP BY c.customer_id, c.first_name, c.last_name, c.loyalty_points
ORDER BY total_spent DESC;
```

### Natural Language Questions to Try
- "Show total spending by customer"
- "Which customers spent the most?"
- "What is the average order value per customer?"

### Expected Results
- **Tables Joined**: 2 (customers, orders)
- **Rows**: 5 (one per customer)
- **Top Spender**: Alice Williams or John Doe
- **Aggregations**: COUNT, SUM, AVG, MAX

---

## Test 5: Products with Reviews and Sales

### SQL Query
```sql
SELECT 
    p.product_name,
    cat.category_name,
    p.price,
    p.stock_quantity,
    COUNT(DISTINCT r.review_id) AS review_count,
    AVG(r.rating) AS avg_rating,
    COUNT(DISTINCT oi.order_item_id) AS times_ordered,
    SUM(oi.quantity) AS total_quantity_sold
FROM products p
JOIN categories cat ON p.category_id = cat.category_id
LEFT JOIN reviews r ON p.product_id = r.product_id
LEFT JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name, cat.category_name, p.price, p.stock_quantity
ORDER BY avg_rating DESC, times_ordered DESC;
```

### Natural Language Questions to Try
- "Show products with their ratings and sales"
- "Which products have the best reviews?"
- "List products with average rating and order count"

### Expected Results
- **Tables Joined**: 4 (products, categories, reviews, order_items)
- **Rows**: 8 (all products)
- **Top Rated**: Laptop Pro 15 (5.0 rating)
- **Includes**: Products with no reviews/sales (NULL values)

---

## Test 6: Orders with Complete Details

### SQL Query
```sql
SELECT 
    o.order_id,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    c.email,
    o.order_date,
    o.status,
    GROUP_CONCAT(p.product_name SEPARATOR ', ') AS products_ordered,
    SUM(oi.quantity) AS total_items,
    o.total_amount
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
GROUP BY o.order_id, customer_name, c.email, o.order_date, o.status, o.total_amount
ORDER BY o.order_date DESC;
```

### Natural Language Questions to Try
- "Show complete order details with products"
- "List all orders with customer names and items"
- "What products were in each order?"

### Expected Results
- **Tables Joined**: 4 (orders, customers, order_items, products)
- **Rows**: 7 (one per order)
- **Features**: Concatenated product list per order
- **Statuses**: delivered, shipped, pending, cancelled

---

## Test 7: Customers Who Never Purchased

### SQL Query
```sql
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    c.registration_date,
    c.loyalty_points,
    COUNT(o.order_id) AS order_count
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.email, c.registration_date, c.loyalty_points
HAVING order_count = 0;
```

### Natural Language Questions to Try
- "Which customers never placed an order?"
- "Show customers with no purchases"
- "List customers who haven't ordered anything"

### Expected Results
- **Tables Joined**: 2 (customers, orders)
- **Rows**: 0 (all test customers have orders)
- **JOIN Type**: LEFT JOIN to find unmatched customers

---

## Test 8: Products Ordered Together

### SQL Query
```sql
SELECT 
    o.order_id,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    p1.product_name AS product_1,
    p2.product_name AS product_2,
    cat1.category_name AS category_1,
    cat2.category_name AS category_2
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_items oi1 ON o.order_id = oi1.order_id
JOIN order_items oi2 ON o.order_id = oi2.order_id AND oi1.order_item_id < oi2.order_item_id
JOIN products p1 ON oi1.product_id = p1.product_id
JOIN products p2 ON oi2.product_id = p2.product_id
JOIN categories cat1 ON p1.category_id = cat1.category_id
JOIN categories cat2 ON p2.category_id = cat2.category_id
ORDER BY o.order_id;
```

### Natural Language Questions to Try
- "Which products were bought together?"
- "Show product combinations in orders"
- "What items did customers purchase in the same order?"

### Expected Results
- **Tables Joined**: 8 (self-join pattern)
- **Rows**: Orders with multiple items
- **Complexity**: HIGH - demonstrates self-joins

---

## Test 9: Category Performance with Reviews

### SQL Query
```sql
SELECT 
    cat.category_name,
    COUNT(DISTINCT p.product_id) AS product_count,
    COUNT(DISTINCT r.review_id) AS total_reviews,
    AVG(r.rating) AS avg_category_rating,
    SUM(oi.subtotal) AS category_revenue,
    SUM(oi.quantity) AS items_sold
FROM categories cat
LEFT JOIN products p ON cat.category_id = p.category_id
LEFT JOIN reviews r ON p.product_id = r.product_id
LEFT JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY cat.category_id, cat.category_name
ORDER BY category_revenue DESC;
```

### Natural Language Questions to Try
- "Show category performance with ratings and revenue"
- "What is the average rating by category?"
- "Compare categories by sales and reviews"

### Expected Results
- **Tables Joined**: 4 (categories, products, reviews, order_items)
- **Rows**: 4 categories
- **Metrics**: Reviews, ratings, revenue, quantity

---

## Test 10: Top Customers by Category

### SQL Query
```sql
SELECT 
    cat.category_name,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    COUNT(DISTINCT o.order_id) AS orders_in_category,
    SUM(oi.quantity) AS items_purchased,
    SUM(oi.subtotal) AS amount_spent
FROM categories cat
JOIN products p ON cat.category_id = p.category_id
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.order_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY cat.category_id, cat.category_name, c.customer_id, c.first_name, c.last_name
HAVING orders_in_category > 0
ORDER BY cat.category_name, amount_spent DESC;
```

### Natural Language Questions to Try
- "Who are the top customers in each category?"
- "Show customer spending by product category"
- "Which customers bought the most from each category?"

### Expected Results
- **Tables Joined**: 5 (all tables!)
- **Rows**: Multiple per category
- **Grouping**: By category AND customer

---

## Validation Checklist

For each test above:

### In Adminer/MySQL:
1. [ ] Copy SQL query
2. [ ] Execute in SQL command tool
3. [ ] Note the number of returned rows
4. [ ] Review the data structure
5. [ ] Take note of key results

### In AI Insights App:
1. [ ] Navigate to "Natural Language Query" tab
2. [ ] Enter the natural language question
3. [ ] Click "Execute Query"
4. [ ] View generated SQL
5. [ ] Compare with original SQL
6. [ ] Verify row count matches
7. [ ] Check key data values match

### What to Compare:
- ✅ **Tables used**: Same tables in JOIN?
- ✅ **JOIN types**: INNER vs LEFT appropriately?
- ✅ **Columns returned**: Similar data fields?
- ✅ **Row count**: Exact or very close?
- ✅ **Aggregations**: Same SUM, COUNT, AVG?
- ✅ **Ordering**: Similar sort logic?

---

## Quick Reference: Table Relationships

```
categories
    ↓ (1:N)
products
    ↓ (1:N)                  ↓ (1:N)
order_items              reviews
    ↓ (N:1)                  ↓ (N:1)
orders                   customers
    ↓ (N:1)                  
customers
```

**Key Relationships:**
- categories → products (1:N)
- products → order_items (1:N)
- products → reviews (1:N)
- orders → order_items (1:N)
- customers → orders (1:N)
- customers → reviews (1:N)

---

## Success Criteria

The natural language to SQL feature is working well if:

1. **Correct Tables**: Generated SQL includes all necessary tables
2. **Proper JOINs**: Uses appropriate JOIN conditions
3. **Similar Results**: Row counts are identical or very close
4. **Aggregations Work**: SUM, COUNT, AVG produce same values
5. **Filters Applied**: WHERE clauses match intent
6. **Readable SQL**: Generated SQL is well-formatted

---

## Troubleshooting

**Q: Row counts don't match exactly**  
A: Check if the LLM added extra filters or different JOINs. Minor differences are acceptable if the core data is correct.

**Q: LLM uses different column names**  
A: As long as the data is the same, column aliases can differ.

**Q: Missing tables in generated SQL**  
A: Try rephrasing your question to be more explicit about what data you need.

**Q: Query fails to execute** A: Check the error message. The LLM might have generated MySQL 8.0+ syntax if you're on an older version.

---

## Advanced Tests

Try asking these variant questions to test robustness:

- "Show me everything about customer purchases" (should include multiple tables)
- "Which products in electronics category got 5-star reviews?" (3-table JOIN + WHERE)
- "Compare sales across categories" (aggregation with grouping)
- "List orders from last month with customer details" (date filtering + JOIN)

Good luck testing! 🚀

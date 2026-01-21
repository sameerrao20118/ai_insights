# Viewing MySQL Data with Adminer

Adminer is a lightweight web-based database management tool that gives you a visual interface to interact with your MySQL database.

---

## Quick Start

### 1. Start Adminer Container

```bash
docker run -d \
  --name ai_insights_adminer \
  --network ai_insights_ai_insights_network \
  -p 8080:8080 \
  -e ADMINER_DEFAULT_SERVER=mysql \
  adminer:latest
```

**Expected output**: Container ID (e.g., `a1b2c3d4e5f6...`)

### 2. Verify It's Running

```bash
docker ps | grep adminer
```

You should see:
```
ai_insights_adminer   adminer:latest   ...   Up X seconds   0.0.0.0:8080->8080/tcp
```

### 3. Access Adminer

Open your browser and go to: **http://localhost:8080**

---

## Login to Adminer

You'll see a login form. Enter these credentials:

| Field | Value |
|-------|-------|
| **System** | MySQL |
| **Server** | `mysql` (or `ai_insights_mysql`) |
| **Username** | `ai_user` |
| **Password** | `ai_password` |
| **Database** | `ai_insights` |

Click **Login** button.

---

## What You Can Do

### Browse Tables

After logging in, you'll see a list of all tables:
- `ai_usecases`
- `categories`
- `customers`
- `orders`
- `order_items`
- `products`
- `reviews`

Click any table name to:
- **Select data** - View all records
- **Show structure** - See column definitions
- **Alter table** - Modify schema
- **Drop** - Delete table (careful!)

### View Data

1. Click a table name (e.g., `customers`)
2. Click **"Select data"** link
3. You'll see all records in a table format
4. Click column headers to sort
5. Click **Edit** to modify a record
6. Click **×** to delete a record

### Run SQL Queries

1. Click **"SQL command"** in the left sidebar
2. Type your SQL query:
   ```sql
   SELECT c.first_name, c.last_name, COUNT(o.order_id) as total_orders
   FROM customers c
   LEFT JOIN orders o ON c.customer_id = o.customer_id
   GROUP BY c.customer_id
   ORDER BY total_orders DESC;
   ```
3. Click **Execute**
4. Results appear below

### Export Data

1. Select a table
2. Click **"Export"** link
3. Choose format:
   - **SQL** - For backup/restore
   - **CSV** - For Excel/spreadsheets
   - **CSV;** - Alternative CSV format
4. Choose options (structure, data, or both)
5. Click **Export** button

### Import Data

1. Click **"Import"** in left sidebar
2. Click **Choose File**
3. Select your `.sql` or `.csv` file
4. Click **Execute**

---

## Managing Adminer

### Stop Adminer

```bash
docker stop ai_insights_adminer
```

Adminer will no longer be accessible at http://localhost:8080

### Start Adminer Again

```bash
docker start ai_insights_adminer
```

Wait 2-3 seconds, then access http://localhost:8080

### Restart Adminer

```bash
docker restart ai_insights_adminer
```

### Check Adminer Status

```bash
docker ps -a | grep adminer
```

### View Adminer Logs

```bash
docker logs ai_insights_adminer
```

### Remove Adminer (Completely)

```bash
docker rm -f ai_insights_adminer
```

To recreate, run the `docker run` command from step 1 again.

---

## Useful Queries to Try

Once you're in Adminer's SQL command interface:

### Count Records in All Tables

```sql
SELECT 'ai_usecases' as table_name, COUNT(*) as rows FROM ai_usecases
UNION SELECT 'customers', COUNT(*) FROM customers
UNION SELECT 'orders', COUNT(*) FROM orders
UNION SELECT 'products', COUNT(*) FROM products
UNION SELECT 'categories', COUNT(*) FROM categories
UNION SELECT 'order_items', COUNT(*) FROM order_items
UNION SELECT 'reviews', COUNT(*) FROM reviews;
```

### View Orders with Customer Names

```sql
SELECT 
    o.order_id,
    CONCAT(c.first_name, ' ', c.last_name) as customer_name,
    o.order_date,
    o.total_amount,
    o.status
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
ORDER BY o.order_date DESC;
```

### Products with Average Ratings

```sql
SELECT 
    p.product_name,
    p.price,
    AVG(r.rating) as avg_rating,
    COUNT(r.review_id) as review_count
FROM products p
LEFT JOIN reviews r ON p.product_id = r.product_id
GROUP BY p.product_id
ORDER BY avg_rating DESC;
```

### Top Customers by Spending

```sql
SELECT 
    CONCAT(c.first_name, ' ', c.last_name) as customer_name,
    c.email,
    SUM(o.total_amount) as total_spent,
    COUNT(o.order_id) as order_count
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status != 'cancelled'
GROUP BY c.customer_id
ORDER BY total_spent DESC
LIMIT 10;
```

---

## Troubleshooting

### Can't Access http://localhost:8080

**Check if Adminer is running:**
```bash
docker ps | grep adminer
```

**Check if port 8080 is available:**
```bash
lsof -i :8080
```

If another app is using port 8080, start Adminer on a different port:
```bash
docker rm -f ai_insights_adminer
docker run -d \
  --name ai_insights_adminer \
  --network ai_insights_ai_insights_network \
  -p 8081:8080 \
  -e ADMINER_DEFAULT_SERVER=mysql \
  adminer:latest
```
Then access at http://localhost:8081

### Login Fails

**Error: "Access denied"**
- Double-check username: `ai_user`
- Double-check password: `ai_password`
- Server should be: `mysql` (not `localhost`)

**Error: "Unknown MySQL server host"**
- Change Server from `ai_insights_mysql` to just `mysql`

**Error: "Can't connect to MySQL server"**
- Verify MySQL container is running:
  ```bash
  docker ps | grep mysql
  ```
- Check they're on same network:
  ```bash
  docker network inspect ai_insights_ai_insights_network
  ```

### Network Issues

If Adminer can't connect to MySQL, recreate with explicit network:

```bash
docker rm -f ai_insights_adminer

docker run -d \
  --name ai_insights_adminer \
  --network ai_insights_ai_insights_network \
  -p 8080:8080 \
  adminer:latest
```

---

## Alternative: phpMyAdmin

If you prefer phpMyAdmin over Adminer:

```bash
docker run -d \
  --name ai_insights_phpmyadmin \
  --network ai_insights_ai_insights_network \
  -p 8080:80 \
  -e PMA_HOST=mysql \
  -e PMA_USER=ai_user \
  -e PMA_PASSWORD=ai_password \
  phpmyadmin:latest
```

Access at: http://localhost:8080

---

## Summary

✅ **Start**: `docker run -d --name ai_insights_adminer --network ai_insights_ai_insights_network -p 8080:8080 adminer:latest`  
✅ **Access**: http://localhost:8080  
✅ **Login**: server=`mysql`, user=`ai_user`, password=`ai_password`, db=`ai_insights`  
✅ **Stop**: `docker stop ai_insights_adminer`  
✅ **Remove**: `docker rm -f ai_insights_adminer`  

**Enjoy your visual database interface!** 🎉

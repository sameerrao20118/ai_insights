# Docker MySQL Setup for AI Insights

## Quick Start

### 1. Start MySQL in Docker

```bash
# From the ai_insights directory
docker-compose -f docker-compose.mysql.yml up -d

# Check status
docker-compose -f docker-compose.mysql.yml ps
```

### 2. Verify MySQL is Running

```bash
# Check logs
docker-compose -f docker-compose.mysql.yml logs mysql

# Should see: "MySQL init process done. Ready for start up."
```

### 3. Update Your .env File

```bash
# Edit .env and add/update these lines:
DATA_SOURCE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=ai_insights
MYSQL_USER=ai_user
MYSQL_PASSWORD=ai_password
MYSQL_TABLE=ai_usecases
MYSQL_SSL_ENABLED=false
```

### 4. Test Connection

```bash
# From ai_insights directory
cd scripts
python3 -c "
import sys
sys.path.insert(0, '..')
from services_mysql import validate_mysql_connection
result = validate_mysql_connection()
print('Connected!' if result.get('connected') else f'Failed: {result}')
"
```

### 5. Run the Application

```bash
cd ..
streamlit run app.py
```

---

## What Gets Auto-Loaded

When you start the Docker container for the **first time**, it automatically runs:

1. **`setup_mysql_schema.sql`** - Creates the `ai_usecases` table
2. **`test_multi_table_schema.sql`** - Creates test schema with:
   - `categories` (4 records)
   - `products` (8 records)
   - `customers` (5 records)
   - `orders` (7 records)
   - `order_items` (14 records)
   - `reviews` (8 records)

This gives you sample data immediately for testing!

---

## Useful Commands

### Connect to MySQL CLI

```bash
# Using docker exec
docker exec -it ai_insights_mysql mysql -uai_user -pai_password ai_insights

# Or using mysql client (if installed locally)
mysql -h 127.0.0.1 -P 3306 -u ai_user -pai_password ai_insights
```

### Check Tables

```sql
SHOW TABLES;

-- Check ai_usecases table
SELECT COUNT(*) FROM ai_usecases;

-- Check test data
SELECT COUNT(*) FROM customers;
SELECT COUNT(*) FROM orders;
```

### Stop MySQL

```bash
docker-compose -f docker-compose.mysql.yml stop
```

### Restart MySQL

```bash
docker-compose -f docker-compose.mysql.yml restart
```

### Remove MySQL (and Data!)

```bash
# This removes container AND data volume
docker-compose -f docker-compose.mysql.yml down -v
```

### View Logs

```bash
# Follow logs
docker-compose -f docker-compose.mysql.yml logs -f mysql

# Last 100 lines
docker-compose -f docker-compose.mysql.yml logs --tail=100 mysql
```

---

## Database Credentials

**Root User:**
- Username: `root`
- Password: `rootpassword`

**Application User (Recommended):**
- Username: `ai_user`
- Password: `ai_password`
- Database: `ai_insights`

---

## Persistent Data

Data is stored in a Docker volume named `mysql_data`. This means:
- ✅ Data persists across container restarts
- ✅ Schema only runs on first initialization
- ⚠️ To reset database, you must remove the volume: `docker-compose -f docker-compose.mysql.yml down -v`

---

## Troubleshooting

### Port Already in Use

If you get "port 3306 already in use":

```bash
# Option 1: Stop local MySQL
brew services stop mysql

# Option 2: Change port in docker-compose.mysql.yml
# Change "3306:3306" to "3307:3306"
# Then update MYSQL_PORT=3307 in .env
```

### Connection Refused

```bash
# Check if container is running
docker ps | grep mysql

# Check health status
docker inspect ai_insights_mysql | grep -A 5 Health

# Wait for healthy status
docker-compose -f docker-compose.mysql.yml ps
```

### Schema Not Loading

If tables don't exist:

```bash
# Enter container and run manually
docker exec -it ai_insights_mysql bash
mysql -uroot -prootpassword ai_insights < /docker-entrypoint-initdb.d/01-schema.sql
mysql -uroot -prootpassword ai_insights < /docker-entrypoint-initdb.d/02-test-data.sql
exit
```

### Reset Everything

```bash
# Stop and remove everything
docker-compose -f docker-compose.mysql.yml down -v

# Start fresh
docker-compose -f docker-compose.mysql.yml up -d

# Wait 30 seconds for initialization
sleep 30

# Check logs
docker-compose -f docker-compose.mysql.yml logs mysql
```

---

## Testing Multi-Table Queries

Once MySQL is running with test data:

```bash
cd scripts

# Run validation suite
python3 validate_multi_table_queries.py

# Or test individual queries in the app
cd ..
streamlit run app.py
# Navigate to: Natural Language Query tab
```

**Example Questions to Try:**
- "Show all customers and their orders"
- "Which customers ordered electronics products?"
- "What is the total revenue by customer?"
- "List products that have never been ordered"

---

## Production Considerations

For production use:

1. **Change Passwords**: Update root and user passwords
2. **Enable SSL**: Set `MYSQL_SSL_ENABLED=true` in .env
3. **Backup Strategy**: Implement regular backups of `mysql_data` volume
4. **Resource Limits**: Add memory/CPU limits to docker-compose
5. **Monitoring**: Add health monitoring and alerting

---

## Summary

✅ MySQL runs in Docker (no local installation needed)  
✅ Sample data pre-loaded automatically  
✅ Data persists across container restarts  
✅ Easy to reset and start fresh  
✅ Ready for natural language queries  

**Next**: Update your `.env` file and run `streamlit run app.py`!

# AI Insights - Quick Start Guide

## Complete Setup (One Command)

For users who want everything installed at once:

```bash
# 1. Clone and enter directory
cd /path/to/ai_insights

# 2. Install ALL dependencies (including MySQL)
pip3 install -r requirements.txt

# 3. Verify installation
python3 -c "import streamlit, fastapi, mysql.connector, pymysql, langchain_core; print('✅ All packages installed successfully')"

# 4. Copy environment template
cp .env.example .env

# 5. Start application
streamlit run app.py
```

That's it! The app will run with Excel data source by default.

---

## What Gets Installed

When you run `pip install -r requirements.txt`, you get:

### Core Packages
- **streamlit** - Web UI framework
- **fastapi** - REST API server
- **uvicorn** - ASGI server

### LLM Integration
- **langchain-core** - LLM abstraction layer
- **langchain-openai** - OpenAI/Azure integration
- **chromadb** - Vector database

### Database & Data
- **mysql-connector-python** ✨ NEW - MySQL driver
- **pymysql** ✨ NEW - Alternative MySQL driver
- **sqlalchemy** ✨ NEW - Database toolkit
- **pandas** - Data manipulation
- **openpyxl** - Excel file handling

### Utilities
- **pydantic** - Data validation
- **python-dotenv** - Environment configuration
- **requests** - HTTP client

**Total install time**: ~2-3 minutes

---

## Option 1: Use Excel (Default)

**No additional setup required!**

The application comes preconfigured to use Excel files. Just run:

```bash
streamlit run app.py
```

Upload your Excel file via the "Bulk Import" tab.

---

## Option 2: Use MySQL (Docker - Recommended)

### Prerequisites
- Docker installed ([Get Docker](https://www.docker.com/get-started))
- Packages already installed from step 2 above

### Quick Start

```bash
# 1. Start MySQL container with test data
docker-compose -f docker-compose.mysql.yml up -d

# 2. Wait for initialization (30-60 seconds)
sleep 60

# 3. Verify MySQL is ready
docker-compose -f docker-compose.mysql.yml logs mysql | grep "ready for connections"

# 4. Configure application for MySQL
cat >> .env << 'EOF'

# MySQL Configuration
DATA_SOURCE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=ai_insights
MYSQL_USER=ai_user
MYSQL_PASSWORD=ai_password
MYSQL_TABLE=ai_usecases
MYSQL_SSL_ENABLED=false
ENABLE_SQL_LOGGING=true
SHOW_GENERATED_SQL=true
EOF

# 5. Test connection
cd scripts
python3 << 'PYTHON'
import sys
sys.path.insert(0, '..')
from services_mysql import validate_mysql_connection
result = validate_mysql_connection()
if result.get('connected'):
    print(f"✅ MySQL Connected!")
    print(f"   Database: {result['database']}")
    print(f"   Table: {result['table']}")
    print(f"   Records: {result.get('row_count', 0)}")
else:
    print(f"❌ Connection failed: {result.get('error')}")
PYTHON
cd ..

# 6. Start application
streamlit run app.py
```

### What You Get

The Docker container automatically loads:

**Main Table**:
- `ai_usecases` - Your primary data table

**Test Schema** (for multi-table queries):
- `categories` (4 records)
- `products` (8 records) 
- `customers` (5 records)
- `orders` (7 records)
- `order_items` (14 records)
- `reviews` (8 records)

**Try These Queries** (in the "Natural Language Query" tab):
- "Show all customers and their orders"
- "Which customers ordered electronics products?"
- "What is the total revenue by customer?"
- "List products with ratings above 4 stars"

---

## Option 3: Use MySQL (Local Installation)

If you have MySQL already installed:

```bash
# 1. Create database
mysql -u root -p -e "CREATE DATABASE ai_insights;"

# 2. Load schema
mysql -u root -p ai_insights < scripts/setup_mysql_schema.sql

# 3. (Optional) Load test data
mysql -u root -p ai_insights < scripts/test_multi_table_schema.sql

# 4. Update .env with your credentials
nano .env
# Set DATA_SOURCE=mysql
# Update MYSQL_* settings

# 5. Start application
streamlit run app.py
```

---

## Verification Checklist

After installation, verify everything works:

```bash
# ✅ Python packages
python3 -c "import streamlit, mysql.connector; print('Packages OK')"

# ✅ Application starts
streamlit run app.py
# Should open browser to http://localhost:8501

# ✅ MySQL (if using Docker)
docker ps | grep mysql
# Should show running container

# ✅ Database connection (if using MySQL)
cd scripts
python3 -c "import sys; sys.path.insert(0, '..'); from services_mysql import validate_mysql_connection; print(validate_mysql_connection())"
cd ..
```

---

## Troubleshooting

### Pip Install Fails

```bash
# Upgrade pip first
pip3 install --upgrade pip

# Install with verbose mode
pip3 install -r requirements.txt -v
```

### MySQL Connection Fails

```bash
# Check Docker container
docker ps

# View logs
docker-compose -f docker-compose.mysql.yml logs mysql

# Restart container
docker-compose -f docker-compose.mysql.yml restart
```

### Port 3306 Already in Use

```bash
# Option 1: Stop local MySQL
brew services stop mysql

# Option 2: Use different port
# Edit docker-compose.mysql.yml
# Change "3306:3306" to "3307:3306"
# Then update .env: MYSQL_PORT=3307
```

### Import Errors

If you see `ModuleNotFoundError`:

```bash
# Re-install specific package
pip3 install mysql-connector-python pymysql sqlalchemy

# Or reinstall everything
pip3 install -r requirements.txt --force-reinstall
```

---

## Next Steps

1. **Excel Users**: Upload data via "Bulk Import" tab
2. **MySQL Users**: Try natural language queries in "Natural Language Query" tab
3. **Both**: Explore dashboards and leader insights

## Documentation

- [Full README](README.md) - Complete documentation
- [MySQL Setup](docs/MYSQL_SETUP.md) - Detailed MySQL guide
- [Docker MySQL](docs/DOCKER_MYSQL_SETUP.md) - Docker-specific instructions
- [Multi-Table Queries](docs/MULTI_TABLE_QUERIES.md) - Advanced query examples
- [Schema Evolution](docs/SCHEMA_EVOLUTION.md) - Handling schema changes

---

## Summary

**Minimum Setup** (Excel mode):
```bash
pip3 install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

**Full Setup** (MySQL + Docker):
```bash
pip3 install -r requirements.txt
docker-compose -f docker-compose.mysql.yml up -d
cat .env.docker.mysql >> .env
streamlit run app.py
```

**Time Required**:
- Package installation: 2-3 minutes
- Docker MySQL: 1-2 minutes
- **Total**: ~5 minutes to fully functional app!

---

## Support

For issues:
1. Check [Troubleshooting](#troubleshooting) section
2. Review error messages carefully
3. Verify all prerequisites installed
4. Check Docker logs (if using MySQL)

✅ **Ready to use!** All packages installed, database ready, application configured.

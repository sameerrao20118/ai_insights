#!/bin/bash
# Setup TPC-H Database in MySQL Docker Container
# Run this script to create and populate the tpch database

echo "======================================"
echo "TPC-H Database Setup for Docker MySQL"
echo "======================================"
echo ""

# Check if Docker is running
if ! command -v docker &> /dev/null; then
    echo "❌ Docker command not found in PATH"
    echo "Please ensure Docker Desktop is running and try:"
    echo "  export PATH=/Applications/Docker.app/Contents/Resources/bin:\$PATH"
    exit 1
fi

# Check if MySQL container is running
if ! docker ps | grep -q ai_insights_mysql; then
    echo "❌ MySQL container 'ai_insights_mysql' is not running"
    echo "Start it with: docker-compose -f docker-compose.mysql.yml up -d"
    exit 1
fi

echo "✅ Docker MySQL container found"
echo ""

# Step 1: Create database and grant permissions
echo "Step 1: Creating tpch database and granting permissions..."
docker exec ai_insights_mysql mysql -uroot -prootpassword -e "
CREATE DATABASE IF NOT EXISTS tpch CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON tpch.* TO 'ai_user'@'%';
FLUSH PRIVILEGES;
SELECT 'Database created successfully' as status;
"

if [ $? -eq 0 ]; then
    echo "✅ Database created and permissions granted"
else
    echo "❌ Failed to create database"
    exit 1
fi

echo ""

# Step 2: Load schema
echo "Step 2: Loading TPC-H schema..."
docker exec -i ai_insights_mysql mysql -uai_user -pai_password tpch < scripts/tpch_schema.sql

if [ $? -eq 0 ]; then
    echo "✅ Schema loaded successfully"
else
    echo "❌ Failed to load schema"
    exit 1
fi

echo ""

# Step 3: Load customer data
echo "Step 3: Loading customer data (150 records)..."
if [ -f /tmp/tpch_customers.sql ]; then
    cat /tmp/tpch_customers.sql | docker exec -i ai_insights_mysql mysql -uai_user -pai_password tpch
    if [ $? -eq 0 ]; then
        echo "✅ Customer data loaded successfully"
    else
        echo "⚠️  Customer data load had issues (may already exist)"
    fi
else
    echo "⚠️  Customer data file not found at /tmp/tpch_customers.sql"
    echo "   Skipping customer data load"
fi

echo ""

# Step 4: Verify
echo "Step 4: Verifying data..."
docker exec ai_insights_mysql mysql -uai_user -pai_password tpch -e "
SELECT 
    'region' as table_name, COUNT(*) as row_count FROM region
UNION
SELECT 'nation', COUNT(*) FROM nation
UNION
SELECT 'customer', COUNT(*) FROM customer;
"

echo ""
echo "======================================"
echo "✅ TPC-H Database Setup Complete!"
echo "======================================"
echo ""
echo "You can now:"
echo "1. Switch to 'tpch' database in the Streamlit UI"
echo "2. Try sample questions like:"
echo "   - 'Show all customers by market segment'"
echo "   - 'List nations grouped by region'"
echo "   - 'Which customers have the highest account balance?'"
echo ""

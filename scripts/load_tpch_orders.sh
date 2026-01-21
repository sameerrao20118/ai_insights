#!/bin/bash
# Load ORDERS and LINEITEM tables into TPC-H database

echo "========================================"
echo "TPC-H: Adding ORDERS and LINEITEM Tables"
echo "========================================"

# Load the SQL file
echo "Loading ORDERS and LINEITEM tables..."
docker exec -i ai_insights_mysql mysql -uai_user -pai_password tpch < scripts/tpch_add_orders_lineitem.sql

if [ $? -eq 0 ]; then
    echo "✅ Tables loaded successfully"
else
    echo "❌ Failed to load tables"
    exit 1
fi

# Verify
echo ""
echo "Verifying data..."
docker exec ai_insights_mysql mysql -uai_user -pai_password tpch -e "
SELECT 
    'REGION' as table_name, COUNT(*) as row_count FROM REGION
UNION ALL
SELECT 'NATION', COUNT(*) FROM NATION
UNION ALL
SELECT 'CUSTOMER', COUNT(*) FROM CUSTOMER
UNION ALL
SELECT 'ORDERS', COUNT(*) FROM ORDERS
UNION ALL
SELECT 'LINEITEM', COUNT(*) FROM LINEITEM;
"

echo ""
echo "========================================"
echo "✅ TPC-H 5-Table Setup Complete!"
echo "========================================"
echo ""
echo "Tables loaded:"
echo "  - REGION (5 rows)"
echo "  - NATION (25 rows)"
echo "  - CUSTOMER (150 rows)"
echo "  - ORDERS (300 rows)"
echo "  - LINEITEM (900+ rows)"
echo ""
echo "Try these queries in the app:"
echo "  - Show all orders with customer names"
echo "  - What is total revenue by customer?"
echo "  - List orders from last month"
echo "  - Which customers have the most orders?"
echo ""

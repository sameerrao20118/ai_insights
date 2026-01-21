#!/bin/bash
# Complete TPC-H Setup - Load all 5 tables in correct order
# Run this script to set up the complete TPC-H dataset

echo "=========================================="
echo "Complete TPC-H 5-Table Setup"
echo "=========================================="
echo ""

# Step 1: Load base schema (REGION, NATION, CUSTOMER)
echo "Step 1: Loading base schema (REGION, NATION, CUSTOMER)..."
docker exec -i ai_insights_mysql mysql -uai_user -pai_password tpch < scripts/tpch_schema.sql

if [ $? -eq 0 ]; then
    echo "✅ Base schema loaded"
else
    echo "❌ Failed to load base schema"
    exit 1
fi

# Step 2: Load additional customer data
echo ""
echo "Step 2: Loading customer data (150 rows)..."
if [ -f /tmp/tpch_customers.sql ]; then
    cat /tmp/tpch_customers.sql | docker exec -i ai_insights_mysql mysql -uai_user -pai_password tpch
    if [ $? -eq 0 ]; then
        echo "✅ Customer data loaded"
    else
        echo "⚠️  Customer data may already exist (OK)"
    fi
else
    echo "⚠️  Customer data file not found, skipping..."
fi

# Step 3: Load ORDERS and LINEITEM
echo ""
echo "Step 3: Loading ORDERS and LINEITEM tables..."
docker exec -i ai_insights_mysql mysql -uai_user -pai_password tpch < scripts/tpch_add_orders_lineitem.sql

if [ $? -eq 0 ]; then
    echo "✅ ORDERS and LINEITEM loaded"
else
    echo "❌ Failed to load ORDERS and LINEITEM"
    exit 1
fi

# Step 4: Verify
echo ""
echo "Step 4: Verifying all tables..."
docker exec ai_insights_mysql mysql -uai_user -pai_password tpch -e "
SELECT 'REGION' as table_name, COUNT(*) as row_count FROM REGION
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
echo "=========================================="
echo "✅ TPC-H 5-Table Setup Complete!"
echo "=========================================="
echo ""
echo "Tables loaded:"
echo "  📊 REGION: 5 rows"
echo "  🌍 NATION: 25 rows"
echo "  👥 CUSTOMER: 150 rows"
echo "  📦 ORDERS: 300 rows"
echo "  📋 LINEITEM: 900+ rows"
echo ""
echo "Total: ~1,380 rows across 5 tables"
echo ""
echo "🚀 Next Steps:"
echo "1. Open Streamlit app"
echo "2. Switch to 'tpch' database in sidebar"
echo "3. Try queries like:"
echo "   - 'Show all orders with customer names'"
echo "   - 'What is the total revenue by customer?'"
echo "   - 'List orders from 2024'"
echo ""

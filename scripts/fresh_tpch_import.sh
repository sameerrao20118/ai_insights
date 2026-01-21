#!/bin/bash
# Fresh TPC-H Import - Drops and recreates all tables

echo "=========================================="
echo "TPC-H Fresh Import"
echo "=========================================="
echo ""
echo "⚠️  WARNING: This will DROP all existing tables in tpch database"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Importing complete TPC-H schema..."
docker exec -i ai_insights_mysql mysql -uai_user -pai_password tpch < scripts/tpch_full_fresh.sql

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ TPC-H Import Complete!"
    echo "=========================================="
    echo ""
    echo "📊 Tables loaded:"
    echo "   REGION: 5 rows"
    echo "   NATION: 25 rows"
    echo "   CUSTOMER: 150 rows"
    echo "   ORDERS: 300 rows"
    echo "   LINEITEM: 900+ rows"
    echo ""
    echo "Total: ~1,380 rows"
    echo ""
    echo "🚀 Ready to test!"
    echo "   1. Open Streamlit app"
    echo "   2. Switch to 'tpch' database"
    echo "   3. Try sample queries"
else
    echo "❌ Import failed"
    exit 1
fi

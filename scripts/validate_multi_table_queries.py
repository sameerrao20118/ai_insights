#!/usr/bin/env python3
"""
Multi-Table Query Validation Script

Tests the natural language to SQL translation capability across multiple tables
with various types of JOIN operations and complex queries.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from data_sources.mysql_source import MySQLSource
from data_sources.nl_to_sql import NLToSQLTranslator
import json


class MultiTableQueryTester:
    """Test suite for multi-table natural language queries."""
    
    def __init__(self):
        self.mysql_source = MySQLSource()
        self.translator = NLToSQLTranslator(self.mysql_source)
        self.test_results = []
    
    def run_test(self, test_name: str, question: str, expected_tables: list, notes: str = ""):
        """Run a single test and validate results."""
        print(f"\n{'='*80}")
        print(f"TEST: {test_name}")
        print(f"{'='*80}")
        print(f"Question: {question}")
        print(f"Expected Tables: {', '.join(expected_tables)}")
        if notes:
            print(f"Notes: {notes}")
        
        try:
            # Translate to SQL
            sql, explanation = self.translator.translate_to_sql(question)
            
            print(f"\n📝 Generated SQL:")
            print(sql)
            print(f"\n💡 Explanation:")
            print(explanation)
            
            # Execute query
            results = self.mysql_source.execute_query(sql)
            
            print(f"\n✅ Query executed successfully!")
            print(f"Rows returned: {len(results)}")
            
            if results and len(results) <= 5:
                print(f"\n📊 Sample Results:")
                for idx, row in enumerate(results, 1):
                    print(f"\nRow {idx}:")
                    for key, value in row.items():
                        print(f"  {key}: {value}")
            elif results:
                print(f"\n📊 First 3 Results:")
                for idx, row in enumerate(results[:3], 1):
                    print(f"\nRow {idx}: {json.dumps(row, default=str, indent=2)}")
            
            # Validate table usage
            sql_upper = sql.upper()
            tables_found = [table for table in expected_tables if table.upper() in sql_upper]
            
            if len(tables_found) == len(expected_tables):
                print(f"\n✅ All expected tables used: {', '.join(tables_found)}")
                status = "PASS"
            else:
                print(f"\n⚠️ Expected tables: {expected_tables}")
                print(f"Tables found in SQL: {tables_found}")
                status = "PARTIAL"
            
            self.test_results.append({
                "test": test_name,
                "status": status,
                "sql": sql,
                "rows": len(results)
            })
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            self.test_results.append({
                "test": test_name,
                "status": "FAIL",
                "error": str(e)
            })
    
    def print_summary(self):
        """Print test summary."""
        print(f"\n\n{'='*80}")
        print("TEST SUMMARY")
        print(f"{'='*80}\n")
        
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        partial = sum(1 for r in self.test_results if r["status"] == "PARTIAL")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"⚠️ Partial: {partial}")
        print(f"❌ Failed: {failed}")
        print(f"\nSuccess Rate: {(passed / total * 100):.1f}%")
        
        print(f"\n{'='*80}\n")


def main():
    """Run comprehensive multi-table query tests."""
    
    print("="*80)
    print("MULTI-TABLE QUERY VALIDATION TEST SUITE")
    print("="*80)
    print()
    print("This script validates natural language to SQL translation")
    print("across multiple tables with foreign key relationships.")
    print()
    
    # Check MySQL connection
    if settings.data_source != "mysql":
        print("❌ ERROR: DATA_SOURCE must be set to 'mysql' in .env")
        print("Please update your .env file and restart.")
        return
    
    tester = MultiTableQueryTester()
    
    # Test 1: Simple JOIN
    tester.run_test(
        test_name="Simple 2-Table JOIN",
        question="Show me all customers and their orders",
        expected_tables=["customers", "orders"],
        notes="Basic INNER JOIN between customers and orders"
    )
    
    # Test 2: 3-Table JOIN
    tester.run_test(
        test_name="3-Table JOIN",
        question="List all products that have been ordered with customer names",
        expected_tables=["products", "order_items", "customers"],
        notes="Requires joining through orders table"
    )
    
    # Test 3: Aggregation with JOIN
    tester.run_test(
        test_name="Aggregation with JOIN",
        question="What is the total revenue by customer?",
        expected_tables=["customers", "orders"],
        notes="JOIN with GROUP BY and SUM"
    )
    
    # Test 4: LEFT JOIN for optional data
    tester.run_test(
        test_name="LEFT JOIN",
        question="Show all products including those that have never been ordered",
        expected_tables=["products", "order_items"],
        notes="LEFT JOIN to find products without orders"
    )
    
    # Test 5: Complex multi-table with filtering
    tester.run_test(
        test_name="Complex Multi-Table Query",
        question="Which customers have ordered electronics products?",
        expected_tables=["customers", "orders", "order_items", "products", "categories"],
        notes="5-table JOIN with category filtering"
    )
    
    # Test 6: Aggregation across multiple tables
    tester.run_test(
        test_name="Multi-Table Aggregation",
        question="What is the average rating for each product category?",
        expected_tables=["categories", "products", "reviews"],
        notes="JOIN with GROUP BY across 3 tables"
    )
    
    # Test 7: Subquery equivalent
    tester.run_test(
        test_name="Top Customers by Spending",
        question="Show the top 5 customers by total spending",
        expected_tables=["customers", "orders"],
        notes="JOIN with aggregation, sorting, and limit"
    )
    
    # Test 8: Product recommendations (complex relationship)
    tester.run_test(
        test_name="Product with Best Reviews",
        question="Which products have an average rating above 4 stars?",
        expected_tables=["products", "reviews"],
        notes="JOIN with HAVING clause"
    )
    
    # Test 9: Customer purchase history
    tester.run_test(
        test_name="Customer Purchase Details",
        question="Show all items purchased by John Doe",
        expected_tables=["customers", "orders", "order_items", "products"],
        notes="4-table JOIN with name filtering"
    )
    
    # Test 10: Category performance
    tester.run_test(
        test_name="Category Sales Analysis",
        question="How many products have been sold in each category?",
        expected_tables=["categories", "products", "order_items"],
        notes="3-table JOIN with COUNT aggregation"
    )
    
    # Print summary
    tester.print_summary()
    
    # Detailed results
    print("\nDETAILED RESULTS:")
    print("="*80)
    for result in tester.test_results:
        status_icon = "✅" if result["status"] == "PASS" else ("⚠️" if result["status"] == "PARTIAL" else "❌")
        print(f"{status_icon} {result['test']}: {result['status']}")
        if "error" in result:
            print(f"   Error: {result['error']}")
    print("="*80)


if __name__ == "__main__":
    print("\n⚠️  PREREQUISITES:")
    print("1. MySQL server running")
    print("2. Test schema loaded (run test_multi_table_schema.sql)")
    print("3. .env configured with DATA_SOURCE=mysql")
    print("4. Database credentials in .env")
    print()
    
    response = input("Continue with tests? (yes/no): ")
    
    if response.lower() not in ["yes", "y"]:
        print("Tests cancelled")
        sys.exit(0)
    
    main()

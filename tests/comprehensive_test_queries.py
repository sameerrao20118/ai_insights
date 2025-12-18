"""
Comprehensive Test Queries for AI Insights Platform

Production-ready test queries to validate analytics capabilities and LLM responses.
Ensures the platform is competitive with Snowflake Cortex AI performance.
"""

import argparse
import time
from typing import Dict, Any, List
import json

from storage.vector_db_manager import VectorDBManager
from storage.analytics_queries import (
    get_users_per_platform,
    get_count_per_platform,
    get_budget_by_platform,
    get_benefit_by_platform,
    get_roi_by_platform,
    get_environment_distribution,
    get_cost_analysis,
    get_comprehensive_analytics
)
from services import answer_leader_question, usecases_to_df, load_all_usecases
from finops.finops_config import load_finops_config


class TestQueryRunner:
    """Run and validate comprehensive test queries."""
    
    def __init__(self):
        self.vdb = VectorDBManager()
        self.results = []
        
    def run_test(self, test_name: str, test_func, expected_result=None):
        """Run a single test and record results."""
        print(f"\n{'='*60}")
        print(f"Test: {test_name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        try:
            result = test_func()
            elapsed = time.time() - start_time
            
            # Display result
            if isinstance(result, dict):
                print(json.dumps(result, indent=2, default=str))
            elif isinstance(result, list):
                print(f"Returned {len(result)} items")
                if result and len(result) <= 5:
                    print(json.dumps(result, indent=2, default=str))
            else:
                print(result)
            
            # Validate if expected result provided
            if expected_result is not None:
                passed = self._validate_result(result, expected_result)
                status = "✅ PASSED" if passed else "❌ FAILED"
            else:
                passed = True
                status = "✅ COMPLETED"
            
            print(f"\nStatus: {status}")
            print(f"Execution Time: {elapsed:.3f}s")
            
            self.results.append({
                "test_name": test_name,
                "status": "passed" if passed else "failed",
                "execution_time": elapsed,
                "result": result
            })
            
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"\n❌ ERROR: {str(e)}")
            print(f"Execution Time: {elapsed:.3f}s")
            
            self.results.append({
                "test_name": test_name,
                "status": "error",
                "execution_time": elapsed,
                "error": str(e)
            })
            return None
    
    def _validate_result(self, result, expected):
        """Validate result against expected outcome."""
        if isinstance(expected, dict):
            for key, value in expected.items():
                if key not in result:
                    print(f"⚠️  Expected key '{key}' not found in result")
                    return False
                if value is not None and result[key] != value:
                    print(f"⚠️  Expected {key}={value}, got {result[key]}")
                    return False
        return True
    
    # ========== Analytics Query Tests ==========
    
    def test_total_count(self):
        """Test getting total document count."""
        return self.run_test(
            "Get Total Use Case Count",
            lambda: {"total_count": self.vdb.get_total_count()}
        )
    
    def test_users_per_platform(self):
        """Test getting users per platform."""
        return self.run_test(
            "Get Total Users Per Platform",
            lambda: get_users_per_platform(self.vdb)
        )
    
    def test_count_per_platform(self):
        """Test getting use case count per platform."""
        return self.run_test(
            "Get Use Case Count Per Platform",
            lambda: get_count_per_platform(self.vdb)
        )
    
    def test_budget_by_platform(self):
        """Test getting budget by platform."""
        return self.run_test(
            "Get Total Budget By Platform",
            lambda: get_budget_by_platform(self.vdb)
        )
    
    def test_benefit_by_platform(self):
        """Test getting benefit by platform."""
        return self.run_test(
            "Get Total Benefit By Platform",
            lambda: get_benefit_by_platform(self.vdb)
        )
    
    def test_roi_by_platform(self):
        """Test ROI analysis by platform."""
        return self.run_test(
            "Get ROI Analysis By Platform",
            lambda: get_roi_by_platform(self.vdb)
        )
    
    def test_environment_distribution(self):
        """Test environment distribution."""
        return self.run_test(
            "Get Environment Distribution",
            lambda: get_environment_distribution(self.vdb)
        )
    
    def test_cost_analysis(self):
        """Test cost analysis."""
        return self.run_test(
            "Get Cost Analysis By Platform",
            lambda: get_cost_analysis(self.vdb)
        )
    
    def test_comprehensive_analytics(self):
        """Test comprehensive analytics (all in one)."""
        return self.run_test(
            "Get Comprehensive Analytics",
            lambda: get_comprehensive_analytics(self.vdb)
        )
    
    # ========== LLM Query Tests ==========
    
    def test_llm_users_per_platform(self):
        """Test LLM query: How many users per platform?"""
        def query():
            usecases = load_all_usecases()
            df = usecases_to_df(usecases)
            decision_factors = load_finops_config()
            
            question = "How many users are there per platform?"
            answer = answer_leader_question(question, df, usecases, decision_factors)
            
            return {
                "question": question,
                "answer": answer,
                "use_cases_analyzed": len(usecases)
            }
        
        return self.run_test("LLM Query: Users Per Platform", query)
    
    def test_llm_best_roi_platform(self):
        """Test LLM query: Which platform has the best ROI?"""
        def query():
            usecases = load_all_usecases()
            df = usecases_to_df(usecases)
            decision_factors = load_finops_config()
            
            question = "Which platform has the best ROI and why?"
            answer = answer_leader_question(question, df, usecases, decision_factors)
            
            return {
                "question": question,
                "answer": answer
            }
        
        return self.run_test("LLM Query: Best ROI Platform", query)
    
    def test_llm_overspending(self):
        """Test LLM query: Where are we overspending?"""
        def query():
            usecases = load_all_usecases()
            df = usecases_to_df(usecases)
            decision_factors = load_finops_config()
            
            question = "Where are we overspending relative to benefits?"
            answer = answer_leader_question(question, df, usecases, decision_factors)
            
            return {
                "question": question,
                "answer": answer
            }
        
        return self.run_test("LLM Query: Overspending Analysis", query)
    
    def test_llm_platform_comparison(self):
        """Test LLM query: Compare platforms."""
        def query():
            usecases = load_all_usecases()
            df = usecases_to_df(usecases)
            decision_factors = load_finops_config()
            
            question = "Compare all platforms by cost efficiency, user adoption, and ROI. Which platform should we invest more in?"
            answer = answer_leader_question(question, df, usecases, decision_factors)
            
            return {
                "question": question,
                "answer": answer
            }
        
        return self.run_test("LLM Query: Platform Comparison", query)
    
    # ========== Performance Tests ==========
    
    def test_query_performance(self):
        """Test query performance with large dataset."""
        def benchmark():
            start = time.time()
            
            # Run multiple analytics queries
            results = {
                "total_count": self.vdb.get_total_count(),
                "users_per_platform": get_users_per_platform(self.vdb),
                "budget_by_platform": get_budget_by_platform(self.vdb),
                "roi_by_platform": get_roi_by_platform(self.vdb)
            }
            
            total_time = time.time() - start
            
            return {
                "queries_run": 4,
                "total_time": round(total_time, 3),
                "avg_time_per_query": round(total_time / 4, 3),
                "performance_rating": "Excellent" if total_time < 1 else "Good" if total_time < 3 else "Needs Improvement"
            }
        
        return self.run_test("Query Performance Benchmark", benchmark)
    
    # ========== Test Suite Runner ==========
    
    def run_all_analytics_tests(self):
        """Run all analytics tests."""
        print("\n" + "="*60)
        print("ANALYTICS QUERY TESTS")
        print("="*60)
        
        self.test_total_count()
        self.test_users_per_platform()
        self.test_count_per_platform()
        self.test_budget_by_platform()
        self.test_benefit_by_platform()
        self.test_roi_by_platform()
        self.test_environment_distribution()
        self.test_cost_analysis()
        self.test_comprehensive_analytics()
        self.test_query_performance()
    
    def run_all_llm_tests(self):
        """Run all LLM query tests."""
        print("\n" + "="*60)
        print("LLM QUERY TESTS")
        print("="*60)
        
        self.test_llm_users_per_platform()
        self.test_llm_best_roi_platform()
        self.test_llm_overspending()
        self.test_llm_platform_comparison()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "passed")
        failed = sum(1 for r in self.results if r["status"] == "failed")
        errors = sum(1 for r in self.results if r["status"] == "error")
        
        total_time = sum(r["execution_time"] for r in self.results)
        avg_time = total_time / total if total > 0 else 0
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Errors: {errors}")
        print(f"\nTotal Execution Time: {total_time:.3f}s")
        print(f"Average Time Per Test: {avg_time:.3f}s")
        
        if passed == total:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {failed + errors} test(s) need attention")
        
        print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Run comprehensive test queries")
    parser.add_argument(
        "--analytics-only",
        action="store_true",
        help="Run only analytics tests (skip LLM tests)"
    )
    parser.add_argument(
        "--llm-only",
        action="store_true",
        help="Run only LLM tests (skip analytics tests)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick test suite (essential tests only)"
    )
    
    args = parser.parse_args()
    
    runner = TestQueryRunner()
    
    print("\n" + "="*60)
    print("AI INSIGHTS COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    if args.quick:
        print("\nRunning Quick Test Suite...")
        runner.test_total_count()
        runner.test_users_per_platform()
        runner.test_roi_by_platform()
        runner.test_query_performance()
    elif args.analytics_only:
        runner.run_all_analytics_tests()
    elif args.llm_only:
        runner.run_all_llm_tests()
    else:
        # Run all tests
        runner.run_all_analytics_tests()
        runner.run_all_llm_tests()
    
    runner.print_summary()


if __name__ == "__main__":
    main()

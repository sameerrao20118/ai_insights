# Tests Directory

This directory contains all test scripts for the AI Insights platform.

## Test Scripts

### Analytics Tests
- **`test_analytics_queries.py`** - Tests all analytics query functions
  ```bash
  python3 tests/test_analytics_queries.py
  ```

### Core Component Tests
- **`test_auth.py`** - Tests enterprise JWT authentication
  ```bash
  python3 tests/test_auth.py
  ```

- **`test_llm.py`** - Tests LLM interface initialization
  ```bash
  python3 tests/test_llm.py
  ```

- **`test_vectordb.py`** - Tests VectorDB manager
  ```bash
  python3 tests/test_vectordb.py
  ```

- **`test_gemini.py`** - Tests Gemini integration
  ```bash
  python3 tests/test_gemini.py
  ```

### Comprehensive Testing
- **`comprehensive_test_queries.py`** - Full test suite with analytics and LLM query validation
  ```bash
  # Run all tests
  python3 tests/comprehensive_test_queries.py
  
  # Run only analytics tests
  python3 tests/comprehensive_test_queries.py --analytics-only
  
  # Run only LLM tests
  python3 tests/comprehensive_test_queries.py --llm-only
  
  # Quick test suite
  python3 tests/comprehensive_test_queries.py --quick
  ```

### Test Data Generation
- **`test_data_generator.py`** - Generates realistic test data (1000+ users per platform)
  ```bash
  # Generate and display
  python3 tests/test_data_generator.py --use-cases-per-platform 50
  
  # Generate and ingest into ChromaDB
  python3 tests/test_data_generator.py --use-cases-per-platform 50 --ingest
  
  # Save to JSON
  python3 tests/test_data_generator.py --output test_data.json
  ```

## Running All Tests

### Sequential Execution
```bash
# Run each test one by one
python3 tests/test_analytics_queries.py
python3 tests/test_llm.py
python3 tests/test_vectordb.py
python3 tests/comprehensive_test_queries.py --quick
```

### Expected Results
All tests should pass (✅) except:
- `test_auth.py` will fail if enterprise credentials are not configured (expected in local mode)
- Some LLM tests may fail if models are not properly configured

## Test Coverage

| Component | Test File | Coverage |
|-----------|-----------|----------|
| Analytics Queries | test_analytics_queries.py | ✅ Full |
| Authentication | test_auth.py | ✅ Full |
| LLM Interface | test_llm.py | ✅ Basic |
| Vector DB | test_vectordb.py | ✅ Basic |
| Comprehensive | comprehensive_test_queries.py | ✅ Full |

## Troubleshooting

### Import Errors
If you see `ModuleNotFoundError`, run from the project root:
```bash
cd /Users/sameera/code/AiInsights_V2
python3 tests/test_analytics_queries.py
```

### ChromaDB Not Found
Ensure you've run data ingestion:
```bash
python3 tests/test_data_generator.py --use-cases-per-platform 20 --ingest
```

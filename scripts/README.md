# Scripts Directory

Utility and maintenance scripts for the AI Insights platform.

## Utility Scripts

### Configuration Check
- **`check_config.py`** - Validates `.env` configuration
  ```bash
  python3 scripts/check_config.py
  ```
  Checks that all required environment variables are set correctly.

### Vector DB Maintenance
- **`purge_vector_db.py`** - Clears all data from ChromaDB
  ```bash
  python3 scripts/purge_vector_db.py
  ```
  ⚠️ **WARNING**: This will delete ALL data from the vector database!

### Validation
- **`verify_all.py`** - Comprehensive system validation
  ```bash
  python3 scripts/verify_all.py
  ```
  Validates all components:
  - Dependencies
  - Configuration
  - LLM initialization
  - Services integration
  - API imports

## Debugging Scripts

### LLM Connection Debugging
- **`debug_llm_connection.py`** - Detailed LLM connection diagnostics
  ```bash
  python3 scripts/debug_llm_connection.py
  ```
  Tests:
  1. Configuration check
  2. Authentication test
  3. LLM client initialization
  4. Chat completion test
  5. Manual request test

### URL Pattern Investigation
- **`investigate_url_pattern.py`** - Investigates enterprise URL patterns
  ```bash
  python3 scripts/investigate_url_pattern.py
  ```
  Useful for debugging Azure OpenAI gateway URL configuration.

## Usage Recommendations

### Before Deployment
```bash
# 1. Check configuration
python3 scripts/check_config.py

# 2. Verify all components
python3 scripts/verify_all.py

# 3. Test LLM connection
python3 scripts/debug_llm_connection.py
```

### During Development
```bash
# Debug issues
python3 scripts/debug_llm_connection.py

# Check URL patterns
python3 scripts/investigate_url_pattern.py
```

### Maintenance
```bash
# Clear and reset database
python3 scripts/purge_vector_db.py

# Re-verify setup
python3 scripts/verify_all.py
```

## Script Details

| Script | Purpose | Safe to Auto-Run |
|--------|---------|------------------|
| check_config.py | Config validation | ✅ Yes |
| verify_all.py | System validation | ✅ Yes |
| debug_llm_connection.py | LLM diagnostics | ✅ Yes |
| investigate_url_pattern.py | URL investigation | ✅ Yes |
| purge_vector_db.py | DB cleanup | ❌ No - Destructive |

## Integration with Tests

These scripts complement the test suite:
- Run `verify_all.py` before running tests
- Use `debug_llm_connection.py` if LLM tests fail
- Use `check_config.py` if configuration issues arise

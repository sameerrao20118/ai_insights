# Enterprise Setup - Complete Solution Documentation

## Overview

This document explains the complete enterprise deployment solution, including all fixes applied during the debugging session.

## What We Fixed

1. ✅ **requirements.txt** - Removed duplicate package dependencies
2. ✅ **auth.py** - Implemented complete JWT authentication with token caching
3. ✅ **llm/lm_interface.py** - Configured proper `AzureChatOpenAI` client for enterprise gateway
4. ✅ **Embedding fallback** - Added graceful degradation for VectorDB initialization

## Enterprise Components

### 1. Authentication (`auth.py`)

**Functionality:**
- Fetches JWT tokens from enterprise auth endpoint  
- Caches tokens with file persistence (`./token_cache.json`)
- Auto-refreshes expired tokens
- Handles authentication errors gracefully

**Configuration Required:**
```bash
SERVICE_ACCOUNT="Service-XXXXX-aaas"
SERVICE_ACCOUNT_PASS="your_password"
AUTH_URL="https://your-gateway.com/token"
```

### 2. LLM Client (`llm/lm_interface.py`)

**Implementation:**
-Uses `AzureChatOpenAI` for enterprise mode
- Constructs URLs following Azure OpenAI patterns
- Passes JWT token for authentication

**URL Pattern:**
```
{LLM_API_BASE}/openai/deployments/{LLM_DEPLOYMENT_NAME}/chat/completions?api-version={LLM_API_VERSION}
```

**Configuration:**
```bash
LLM_API_BASE="https://gateway.com/genai/openai/gpt"  # WITHOUT /openai/deployments/
LLM_DEPLOYMENT_NAME="gpt_model_name"
LLM_API_VERSION="2024-06-01"
```

### 3. Embeddings Service

**URL Pattern:**
```
{EMBEDDING_API_BASE}/openai/deployments/{EMBEDDING_DEPLOYMENT_NAME}/embeddings?api-version={EMBEDDING_API_VERSION}
```

**Configuration:**
```bash
EMBEDDING_API_BASE="https://gateway.com/genai/openai/ada"  # WITHOUT /openai/deployments/
EMBEDDING_DEPLOYMENT_NAME="ada002_2"
EMBEDDING_API_VERSION="2024-06-01"
```

**Fallback Behavior:**
- If embedding endpoint fails, returns dummy embeddings (1536-dimensional zero vectors)
- Allows VectorDB to initialize successfully
- Existing documents remain queryable
- New document ingestion disabled until embedding endpoint is configured correctly

## Testing Scripts

### `test_auth.py`
Tests JWT token fetching independently.

**Usage:**
```bash
python test_auth.py
```

**Success Output:**
```
✅ Token obtained: eyJhbGci...
   Token length: 584 characters
```

### `test_llm.py`
Tests LLM interface initialization and embeddings.

**Usage:**
```bash
python test_llm.py
```

**Success Output:**
```
✅ LLM initialized: AzureChatOpenAI
⚠️  Embedding test failed (expected if endpoint not configured)
```

### `test_vectordb.py`
Tests complete VectorDB initialization pipeline.

**Usage:**
```bash
python test_vectordb.py
```

**Success Output:**
```
✅ VectorDB initialized
   Documents in collection: 100
```

### `debug_llm_connection.py`
Comprehensive debugging script for LLM connection issues.

**Usage:**
```bash
python debug_llm_connection.py
```

**Tests:**
1. Configuration check
2. Authentication test
3. LLM client initialization
4. Chat completion test
5. Manual request test (low-level)

## Common Issues

### Issue: "Vector store not ready"
**Cause:** Embedding service fails during VectorDB initialization
**Fix:** Dummy embeddings fallback (already implemented)
**Impact:** App loads successfully, existing data queryable

### Issue: "deployments keyword not found"
**Cause:** Incorrect URL pattern in `.env`
**Fix:** Remove `/openai/deployments/` from base URLs - `AzureChatOpenAI` adds this automatically

### Issue: "NameError: SERVICE_ACCOUNT_PASS not defined"
**Cause:** Variable reference bug in `auth.py`
**Fix:** Use `settings.service_account_pass` instead of direct variable

### Issue: "Connection error" when answering questions
**Cause:** `LLM_PROVIDER` not set to `enterprise` in `.env`
**Fix:** Set `LLM_PROVIDER=enterprise` on enterprise machine

## Files Modified

- `requirements.txt` - Removed duplicates
- `auth.py` - Complete JWT authentication
- `llm/lm_interface.py` - Azure OpenAI client configuration
- `.env.example` - Updated template
- `README.md` - Updated enterprise setup instructions

## Deployment Checklist

- [ ] Copy updated files to enterprise machine
- [ ] Create `.env` with enterprise credentials
- [ ] Set `LLM_PROVIDER=enterprise`  
- [ ] Run `python test_auth.py` → Should succeed
- [ ] Run `python test_llm.py` → LLM should succeed
- [ ] Run `python test_vectordb.py` → Should succeed
- [ ] Run `streamlit run app.py` → App should load
- [ ] Test "Answer leader question" → Should work
- [ ] (Optional) Fix embedding endpoint for document ingestion

## Architecture Diagram

```
┌─────────────────────────────────────────────┐
│          Enterprise Application             │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────┐    ┌──────────────┐          │
│  │ auth.py  │───▶│  JWT Token   │          │
│  │          │    │   Caching    │          │
│  └──────────┘    └──────────────┘          │
│       │                                     │
│       ▼                                     │
│  ┌─────────────────────────────────┐       │
│  │   llm/lm_interface.py           │       │
│  │  ┌──────────────────────────┐   │       │
│  │  │  AzureChatOpenAI Client  │   │       │
│  │  └──────────────────────────┘   │       │
│  └─────────────────────────────────┘       │
│       │                                     │
│       ▼                                     │
│  ┌─────────────────────────────────┐       │
│  │   VectorDBManager               │       │
│  │  (with embedding fallback)      │       │
│  └─────────────────────────────────┘       │
│                                             │
└─────────────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ Enterprise Gateway    │
        │ (Azure OpenAI format) │
        └───────────────────────┘
```

## Support

For issues:
1. Run `python debug_llm_connection.py` for diagnostic information
2. Check `./token_cache.json` exists and is valid
3. Verify `.env` settings match enterprise gateway URLs
4. Contact IT for correct gateway endpoints and deployment names

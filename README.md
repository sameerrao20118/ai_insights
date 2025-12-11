# AI Usage Insights - Complete Setup Guide

**Enterprise AI Catalogue & Platform Recommendations for NatWest**

> **📋 Overview**: This guide provides step-by-step instructions for setting up the AI Usage Insights platform. Follow these instructions exactly to ensure successful deployment.

---

## 🎯 What You'll Build

By following this guide, you will have:
- ✅ A fully functional Streamlit web application
- ✅ A REST API server for programmatic access
- ✅ Integration with either local LLMs OR enterprise Azure/Gemini services
- ✅ Vector database for AI use case storage and retrieval
- ✅ Validated setup ready for production use

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup (Common for All Environments)](#initial-setup)
3. [Path A: Enterprise Setup (NO Ollama Required)](#path-a-enterprise-setup)
4. [Path B: Local Development Setup (With Ollama)](#path-b-local-development-setup)
5. [Validation & Testing](#validation--testing)
6. [Using the Application](#using-the-application)
7. [API Testing with Postman](#api-testing-with-postman)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

**For ALL setups:**
- ✅ Python 3.12 
- ✅ Git
- ✅ Text editor (VS Code, PyCharm, etc.)

**For local development ONLY:**
- ✅ Ollama (NOT needed for enterprise)

### How to Install Prerequisites

#### macOS

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.12 via Conda
# Download from: https://www.anaconda.com/download
# OR use Homebrew:
brew install --cask anaconda

# Install Git
brew install git
```

#### Windows

```powershell
# Install Chocolatey (package manager)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install Python and Git
choco install python312 git -y
```

---

## Initial Setup

**These steps are REQUIRED for both enterprise and local setups.**

### Step 1: Clone the Repository

Open your terminal/command prompt and run:

```bash
# Navigate to your projects folder
cd ~
mkdir -p code
cd code

# Clone the repository
git clone <YOUR_REPOSITORY_URL> opportunity-mine
cd opportunity-mine
```

✅ **Checkpoint**: You should now be in the `opportunity-mine` directory. Verify with:
```bash
pwd  # Should show: /Users/<your-username>/code/opportunity-mine
ls   # Should show files like: app.py, requirements.txt, README.md
```

### Step 2: Create Python Environment

**Choose ONE of these options:**

#### Option A: Using Conda (Recommended)

```bash
# Create a new environment with Python 3.12
conda create -n ai-insights python=3.12 -y

# Activate the environment
conda activate ai-insights

# VERIFY activation - your prompt should now show (ai-insights)
# Example: (ai-insights) user@machine:~/code/opportunity-mine$
```

#### Option B: Using venv (Alternative)

```bash
# Create virtual environment
python3.12 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# VERIFY activation - your prompt should show (venv)
```

✅ **Checkpoint**: Run `python --version` - it should show `Python 3.12.x`

### Step 3: Install Python Dependencies

```bash
# Make sure you're in the project directory
cd ~/code/opportunity-mine

# Install all required packages
pip install -r requirements.txt

# This will take 2-5 minutes. You should see packages being installed.
```

✅ **Checkpoint**: Verify installation:
```bash
python -c "import streamlit; import fastapi; print('✅ Dependencies installed')"
```

If you see `✅ Dependencies installed`, continue. If you see any errors, review the [Troubleshooting](#troubleshooting) section.

---

## Path A: Enterprise Setup

**⚠️ IMPORTANT**: This path is for deployment on enterprise machines where **Ollama is NOT available**. The application will use Azure OpenAI and Gemini via your corporate gateways.

### Step 4a: Configure Enterprise Authentication

#### 4a.1: Obtain Your Credentials

Contact your IT administrator to get:
- Service account username
- Service account password  
- Authentication URL
- Azure OpenAI gateway URL
- Embedding service URL
- Gemini/Vertex gateway URL

#### 4a.2: Set Up `auth.py`

**📝 ACTION REQUIRED**: You need to implement the authentication logic specific to your organization.

Open `auth.py` in your text editor and replace the contents with your enterprise auth logic:

```python
# auth.py
import requests
import time
from datetime import datetime

_TOKEN_CACHE = {}

def get_cached_or_new_token() -> str:
    """
    Fetch JWT token from enterprise auth service.
    """
    # Check if we have a valid cached token
    if _TOKEN_CACHE.get("token") and _TOKEN_CACHE.get("expiry", 0) > time.time():
        return _TOKEN_CACHE["token"]
    
    # Import settings to get credentials
    from config.settings import settings
    
    # CUSTOMIZE THIS: Your organization's token endpoint
    # Example shown - replace with your actual logic
    response = requests.post(
        settings.auth_url,
        json={
            "username": settings.service_account,
            "password": settings.service_account_pass
        },
        verify=False,  # adjust based on your corporate SSL policy
        timeout=30
    )
    
    response.raise_for_status()
    
    # Get token from response (adjust key names to match your API)
    data = response.json()
    token = data.get("access_token")  # or data.get("token")
    
    # Cache token (assuming 1 hour expiry - adjust as needed)
    _TOKEN_CACHE["token"] = token
    _TOKEN_CACHE["expiry"] = time.time() + 3600
    
    return token

def delete_token_cache() -> None:
    """Clears cached token to force refresh."""
    global _TOKEN_CACHE
    _TOKEN_CACHE.clear()
```

✅ **Checkpoint**: Save the file.

#### 4a.3: Configure `.env` File

Create a file named `.env` in the project root directory with the following content:

```bash
# =====================================
# ENTERPRISE MODE CONFIGURATION
# =====================================

# Set to 'enterprise' to use corporate gateways
LLM_PROVIDER=enterprise

# =====================================
# Authentication Settings
# =====================================
SERVICE_ACCOUNT=YOUR_SERVICE_ACCOUNT_HERE
SERVICE_ACCOUNT_PASS=YOUR_PASSWORD_HERE
AUTH_URL=https://your-auth-gateway.company.com/token

# =====================================
# Azure OpenAI (Chat)
# =====================================
LLM_API_BASE=https://your-gateway.company.com/genai/openai/gpt41
LLM_DEPLOYMENT_NAME=gpt41_deployment_name_here
LLM_API_VERSION=2024-06-01

# =====================================
# Embeddings Service
# =====================================
EMBEDDING_API_BASE=https://your-gateway.company.com/genai/openai/ada/openai2/deployments
EMBEDDING_DEPLOYMENT_NAME=ada002
EMBEDDING_API_VERSION=2024-06-01

# =====================================
# Gemini/Vertex AI (Optional)
# =====================================
BASE_URL=https://your-gateway.company.com/
CHAT_SUFFIX=genai/vertexai/gemini-2.5-pro/generateContent

# =====================================
# Application Settings
# =====================================
CHROMA_PATH=./chroma_store
COLLECTION_NAME=ai_usecases
ENVIRONMENT=production
```

**📝 REPLACE THE FOLLOWING**:
- `YOUR_SERVICE_ACCOUNT_HERE` → Your actual service account
- `YOUR_PASSWORD_HERE` → Your actual password
- All URLs → Your organization's actual gateway URLs
- Deployment names → Your actual deployment names

✅ **Checkpoint**: Save the `.env` file. Re-check that `LLM_PROVIDER=enterprise`.

### Step 5a: Validate Enterprise Setup

```bash
# Run the validation script
python verify_all.py
```

**Expected Output:**
```
--- 1. Testing Dependencies ---
✅ langchain_core imported
✅ langchain_openai imported
✅ pydantic_settings imported

--- 2. Testing Configuration ---
✅ Settings loaded. Provider: enterprise

--- 3. Testing LLM Interface (Initialization) ---
✅ LLMInterface initialized successfully

--- 4. Testing Service Integration (Mock) ---
✅ services module imported
✅ Pydantic models importable

--- 5. Testing API Import ---
✅ FastAPI app object imported successfully

🎉 ALL CHECKS PASSED
```

If you see errors, go to [Troubleshooting](#troubleshooting).

**🎉 You're done with enterprise setup! Skip to [Validation & Testing](#validation--testing)**

---

## Path B: Local Development Setup

**ℹ️ INFO**: This path is for local development on your personal machine. It requires Ollama.

### Step 4b: Install Ollama

#### macOS

```bash
# Install Ollama
brew install ollama

# Verify installation
ollama --version
```

#### Linux

```bash
# Download and install
curl -fsSL https://ollama.com/install.sh | sh

# Verify
ollama --version
```

#### Windows

Download from: https://ollama.com/download/windows

### Step 5b: Download LLM Models

```bash
# Pull the chat model (this will take 5-10 minutes, ~4GB download)
ollama pull llama3.2

# Pull the embedding model (~300MB download)
ollama pull nomic-embed-text

# Verify models are installed
ollama list
```

**Expected Output:**
```
NAME                    ID              SIZE      MODIFIED
llama3.2:latest         a80c4f17acd5    2.0 GB    X minutes ago
nomic-embed-text:latest 0a109f422b47    274 MB    X minutes ago
```

### Step 6b: Start Ollama Server

**Open a NEW terminal window** (keep this running):

```bash
# Start Ollama server
ollama serve
```

**Expected Output:**
```
Listening on 127.0.0.1:11434
```

✅ **Checkpoint**: Keep this terminal open. Open a NEW terminal for the next steps.

### Step 7b: Configure `.env` for Local Mode

Create a file named `.env` in the project root:

```bash
# =====================================
# LOCAL DEVELOPMENT CONFIGURATION
# =====================================

# Set to 'ollama' for local development
LLM_PROVIDER=ollama

# =====================================
# Ollama Settings
# =====================================
OLLAMA_API_BASE=http://localhost:11434/v1
OLLAMA_CHAT_MODEL=llama3.2
OLLAMA_EMBED_MODEL=nomic-embed-text

# =====================================
# Application Settings
# =====================================
CHROMA_PATH=./chroma_store
COLLECTION_NAME=ai_usecases
ENVIRONMENT=dev
```

✅ **Checkpoint**: Save the `.env` file. Verify `LLM_PROVIDER=ollama`.

### Step 8b: Validate Local Setup

```bash
# In your NEW terminal (with environment activated):
python verify_all.py
```

**Expected Output**: Same as enterprise (see Step 5a above), but showing `Provider: ollama`

**🎉 You're done with local setup! Continue to [Validation & Testing](#validation--testing)**

---

## Validation & Testing

### Terminal 1: Start the API Server

```bash
# Activate your environment (if not already active)
conda activate ai-insights  # or: source venv/bin/activate

# Start the API server
uvicorn api:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Will watch for changes in these directories: ['/Users/.../opportunity-mine']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXXX] using StatReload
INFO:     Started server process [YYYYY]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**✅ Keep this terminal running.**

### Terminal 2: Test the API

Open a NEW terminal:

```bash
# Test health endpoint
curl http://localhost:8000/health
```

**Expected Response:**
```json
{"status":"ok"}
```

✅ **If you see this, your API is working!**

### Terminal 3: Start Streamlit UI

Open a THIRD terminal:

```bash
# Activate environment
conda activate ai-insights  # or: source venv/bin/activate

# Start Streamlit
streamlit run app.py
```

**Expected Output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

✅ **Your browser should automatically open to http://localhost:8501**

---

## Using the Application

### First Time Setup: Import Data

1. **Open Browser**: Navigate to http://localhost:8501
2. **Click**: "📤 Bulk Import" in the sidebar
3. **Upload**: Your Excel file containing AI use cases
4. **Click**: "Ingest to Vector DB"
5. **Wait**: For ingestion to complete

✅ **Your data is now loaded!**

### Using the Dashboard

1. **Click**: "📊 Dashboard" in sidebar
2. **View**: Metrics and charts of your AI portfolio
3. **Search**: Use the search box to find specific projects

### Leader Insights

1. **Click**: "🎯 Leader Insights"
2. **Select**: A use case from the dropdown
3. **Click**: "Get Recommendation"
4. **Review**: Platform and architecture recommendations

---

## API Testing with Postman

### Import Collection

1. **Open Postman**
2. **Click**: File → Import
3. **Select**: `AI_Insights_API.postman_collection.json` from project directory
4. **Click**: Import

### Set Environment Variable

1. **Click**: Environment (⚙️ icon)
2. **Create New**: "AI Insights Local"
3. **Add Variable**:
   - Variable: `base_url`
   - Value: `http://localhost:8000`
4. **Save**

### Run Tests

#### Test 1: Health Check

1. **Select**: "Health Check" request
2. **Click**: Send
3. **Expect**: `{"status":"ok"}`

✅ **API is responsive**

#### Test 2: Chat Query

1. **Select**: "Chat - High ROI Projects"  
2. **Review** the request body:
   ```json
   {
     "question": "Show me AI projects with high ROI",
     "filters": {"environment": "Production"}
   }
   ```
3. **Click**: Send
4. **Expect**: JSON response with `answer` and `explanation` fields

✅ **Chat endpoint is working**

#### Test 3: Leader Q&A

1. **Select**: "Leader Q&A - Prioritization"
2. **Click**: Send
3. **Expect**: Strategic recommendations in JSON format

✅ **All endpoints validated!**

---

## Troubleshooting

### ❌ Error: `ModuleNotFoundError: No module named 'langchain'`

**Cause**: Wrong Python environment or dependencies not installed

**Solution**:
```bash
# Step 1: Verify you're in the correct environment
# Your prompt should show (ai-insights) or (venv)
conda activate ai-insights

# Step 2: Reinstall dependencies
pip install -r requirements.txt

# Step 3: Verify
python -c "import langchain; print('Success')"
```

### ❌ Error: `Connection refused` when testing API

**Cause**: API server not running

**Solution**:
```bash
# In a dedicated terminal, start the API
conda activate ai-insights
uvicorn api:app --reload --port 8000

# Keep this terminal open
```

### ❌ Error: `Vector store is not ready`

**Cause**: Chroma database has wrong configuration

**Solution**:
```bash
# Delete old database
rm -rf ./chroma_store

# Restart Streamlit
streamlit run app.py

# The database will be recreated automatically
```

### ❌ Enterprise Mode: Authentication Fails

**Solution**:
1. Verify credentials in `.env` are correct
2. Test your auth endpoint directly:
   ```bash
   curl -X POST https://your-auth-url/token \
     -H "Content-Type: application/json" \
     -d '{"username":"YOUR_USER","password":"YOUR_PASS"}'
   ```
3. Check `auth.py` matches your organization's API structure
4. Contact your IT admin if issues persist

### ❌ Local Mode: `Ollama connection failed`

**Solution**:
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If no response, start Ollama:
ollama serve

# In another terminal, verify models:
ollama list
```

### ❌ Streamlit opens but shows errors

**Solution**:
```bash
# Check terminal output for specific error messages
# Common issues:

# 1. Port already in use
pkill -f streamlit  # Kill existing Streamlit processes
streamlit run app.py

# 2. Import errors
pip install -r requirements.txt --force-reinstall
```

---

## Quick Reference Commands

```bash
# Start API Server
conda activate ai-insights
uvicorn api:app --reload --port 8000

# Start Streamlit UI
conda activate ai-insights  
streamlit run app.py

# Run Validation
python verify_all.py

# Test API Health
curl http://localhost:8000/health

# View Ollama Models (local only)
ollama list

# Start Ollama Server (local only)
ollama serve
```

---

## Next Steps

After successful setup:

1. ✅ Import your AI use case data via Bulk Import
2. ✅ Explore the Dashboard for portfolio insights
3. ✅ Test API endpoints with Postman
4. ✅ Use Leader Insights for strategic recommendations
5. ✅ Integrate API into your workflows

---

## Support Contact

For technical issues:
- Review this documentation thoroughly
- Check [Troubleshooting](#troubleshooting) section
- Run `python verify_all.py` for diagnostics
- Contact your technical lead with error messages

---

**Version**: 2.0  
**Last Updated**: December 2025  
**Maintained by**: NatWest AI Platform Team

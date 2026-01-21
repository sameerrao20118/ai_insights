# AI Usage Insights - Complete Setup Guide

**Enterprise AI Catalogue & Platform Recommendations for NatWest**

> **📋 Overview**: This guide provides step-by-step instructions for setting up the AI Usage Insights platform. Follow these instructions exactly to ensure successful deployment.

---

## 🎯 What You'll Build

By following this guide, you will have:
- ✅ A fully functional Streamlit web application
- ✅ A REST API server for programmatic access
- ✅ Integration with either local LLMs OR enterprise Azure/Gemini services
- ✅ **Flexible data sources**: Excel files OR MySQL database
- ✅ **Natural Language to SQL**: Query your MySQL database in plain English
- ✅ Vector database for AI use case storage and retrieval
- ✅ **Query observability**: See generated SQL for every query
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
8. [MySQL Integration (Optional)](#mysql-integration)
9. [Troubleshooting](#troubleshooting)

---


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
- Authentication URL (JWT token endpoint)
- Azure OpenAI LLM gateway base URL
- Azure OpenAI embedding gateway base URL
- LLM deployment name
- Embedding deployment name

#### 4a.2: Understand `auth.py` (Already Implemented)

The `auth.py` file is **already implemented** with:
- ✅ JWT token fetching from your auth endpoint
- ✅ Token caching with file persistence
- ✅ Automatic token refresh on expiry
- ✅ Error handling and retry logic

**No changes needed to `auth.py`** - it works with standard JWT authentication endpoints.

#### 4a.3: Configure `.env` File

Create a file named `.env` in the project root directory with your enterprise settings:

```bash
# =====================================
# ENTERPRISE MODE CONFIGURATION
# =====================================

# Set to 'enterprise' to use corporate gateways
LLM_PROVIDER=enterprise

# =====================================
# Authentication Settings (JWT)
# =====================================
SERVICE_ACCOUNT=YOUR_SERVICE_ACCOUNT
SERVICE_ACCOUNT_PASS=YOUR_PASSWORD
AUTH_URL=https://your-gateway.company.com/token

# =====================================
# Azure OpenAI - Chat LLM
# =====================================
# IMPORTANT: Base URL should be WITHOUT /openai/deployments/
# The AzureChatOpenAI client will add this automatically
# 
# Example: If your full endpoint is:
#   https://gateway.com/genai/openai/gpt/openai/deployments/gpt_model_name/chat/completions
# Then set:
#   LLM_API_BASE=https://gateway.com/genai/openai/gpt
#   LLM_DEPLOYMENT_NAME=gpt_model_name
# 
LLM_API_BASE=https://your-gateway.company.com/genai/openai/gpt
LLM_DEPLOYMENT_NAME=your_gpt_deployment_name
LLM_API_VERSION=2024-06-01

# =====================================
# Azure OpenAI - Embeddings
# =====================================
# Same pattern as LLM - base URL without /openai/deployments/
# 
# Example: If your full endpoint is:
#   https://gateway.com/genai/openai/ada/openai/deployments/ada002_2/embeddings
# Then set:
#   EMBEDDING_API_BASE=https://gateway.com/genai/openai/ada
#   EMBEDDING_DEPLOYMENT_NAME=ada002_2
# 
EMBEDDING_API_BASE=https://your-gateway.company.com/genai/openai/ada
EMBEDDING_DEPLOYMENT_NAME=your_embedding_deployment_name
EMBEDDING_API_VERSION=2024-06-01

# =====================================
# Application Settings
# =====================================
CHROMA_PATH=./chroma_store
COLLECTION_NAME=ai_usecases
ENVIRONMENT=production
```

**📝 REPLACE WITH YOUR ACTUAL VALUES**:
- `YOUR_SERVICE_ACCOUNT` → Your enterprise service account (e.g., Service-12345-aaas)
- `YOUR_PASSWORD` → Your service account password
- `AUTH_URL` → Your organization's JWT token endpoint
- `LLM_API_BASE` → Your Azure OpenAI chat gateway base URL (WITHOUT /openai/deployments/)
- `LLM_DEPLOYMENT_NAME` → Your chat model deployment name
- `EMBEDDING_API_BASE` → Your embedding gateway base URL (WITHOUT /openai/deployments/)
- `EMBEDDING_DEPLOYMENT_NAME` → Your embedding deployment name

> **🔍 URL Pattern Tip**: Test your URLs with curl to verify the correct structure:
> ```bash
> # This should return 200 OK with embeddings
> curl --location --request POST \
>   "https://your-gateway.com/genai/openai/ada/openai/deployments/ada002_2/embeddings?api-version=2024-06-01" \
>   --header "Authorization: Bearer YOUR_TOKEN" \
>   --header "Content-Type: application/json" \
>   --data '{"input": "test"}'
> ```
>
> If this works, then:
> - `EMBEDDING_API_BASE=https://your-gateway.com/genai/openai/ada`
> - `EMBEDDING_DEPLOYMENT_NAME=ada002_2`

✅ **Checkpoint**: Save the `.env` file. Verify `LLM_PROVIDER=enterprise`.

### Step 5a: Test Enterprise Setup

Use the provided test scripts to validate each component:

#### Test Authentication
```bash
python test_auth.py
```
**Expected**: ✅ Token obtained (584 characters)

#### Test LLM Interface
```bash
python test_llm.py
```
**Expected**: ✅ LLM initialized, ⚠️ Embedding may fail (this is OK for now)

#### Test Vector DB
```bash
python test_vectordb.py
```
**Expected**: ✅ VectorDB initialized with X documents


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

## Sample Questions for Testing

Use these curated questions to test and demonstrate the system's capabilities across different interaction modes.

### 📊 Leader Insights Questions

These questions help leadership make strategic decisions about AI initiatives.

#### Question 1: Portfolio Prioritization
```
Which AI initiatives should we prioritize for Q1 2025 based on ROI and strategic alignment?
```
**Expected Answer Quality**: Strategic recommendations with specific project names, ROI calculations, risk assessments, and timeline considerations.

#### Question 2: Risk Assessment
```
What are the highest-risk AI projects currently in production, and what mitigation strategies should we implement?
```
**Expected Answer Quality**: Identified high-risk projects with specific risk factors (governance, compliance, technical), concrete mitigation steps, and stakeholder responsibilities.

#### Question 3: Cost Optimization
```
How can we optimize our AI portfolio to reduce costs while maintaining business value?
```
**Expected Answer Quality**: Specific cost-saving opportunities, ROI analysis of current projects, recommendations for consolidation or decommissioning, budget reallocation suggestions.

#### Question 4: Team Capacity Planning
```
Which teams are over-allocated on AI initiatives, and how should we rebalance resources across the portfolio?
```
**Expected Answer Quality**: Team-by-team breakdown, utilization metrics, specific rebalancing recommendations, and impact on project timelines.

#### Question 5: Compliance & Governance
```
Are there any AI initiatives that require immediate governance review or compliance updates?
```
**Expected Answer Quality**: List of non-compliant or at-risk projects, specific regulatory requirements, remediation steps, and urgency assessment.

---

### 💬 Chat with Catalogue Questions

These questions help users explore and analyze the AI use case catalogue.

#### Question 1: High-Impact Projects
```
Show me all production AI projects with estimated ROI above 200% and budget under £500,000.
```
**Filters to Apply**:
```json
{
  "environment": "Production",
  "budget_max": 500000
}
```
**Expected Answer Quality**: Filtered list with project details, actual ROI calculations, team ownership, and success metrics.

#### Question 2: Technology Stack Analysis
```
What are the most common AI technologies and platforms being used across our Generative AI initiatives?
```
**Filters to Apply**:
```json
{
  "ai_type": "Generative AI"
}
```
**Expected Answer Quality**: Technology breakdown, usage patterns, platform recommendations, and standardization opportunities.

#### Question 3: Early-Stage Opportunities
```
Which AI projects are still in POC or pilot phase that show promise for production deployment?
```
**Filters to Apply**:
```json
{
  "status": "POC",
  "environment": "Lower"
}
```
**Expected Answer Quality**: Projects ready for scale-up, business case strength, technical readiness assessment, and recommended next steps.

#### Question 4: Budget Utilization
```
How is our AI budget distributed across different teams and initiative types?
```
**Expected Answer Quality**: Budget breakdown by team/type, spend efficiency analysis, over/under-budget projects, and reallocation recommendations.

#### Question 5: Success Stories
```
What are our most successful AI deployments in the last 12 months, and what made them successful?
```
**Filters to Apply**:
```json
{
  "environment": "Production"
}
```
**Expected Answer Quality**: Top performers with success factors, lessons learned, best practices, and replication opportunities.

---

### 🎯 Platform Recommendations Questions

These questions help architects make technical platform decisions.

#### Question 1: Kubernetes vs Serverless
```
For a customer service chatbot handling 10,000 requests/day with variable load, should we use Kubernetes or Serverless?
```
**Use Case Details**:
- **AI Type**: Generative AI
- **Expected Volume**: 10,000 requests/day
- **Load Pattern**: Variable (peak hours)
- **Budget**: £250,000

**Expected Answer Quality**: Platform comparison with cost analysis, scalability assessment, operational complexity, specific recommendations with rationale.

#### Question 2: Data Processing Pipeline
```
What platform architecture should we use for a real-time fraud detection model processing 50,000 transactions/hour?
```
**Use Case Details**:
- **AI Type**: Machine Learning
- **Volume**: 50,000 transactions/hour
- **Latency Requirement**: <100ms
- **Data Sources**: Multiple databases

**Expected Answer Quality**: Architecture diagram recommendations, technology stack, data flow patterns, latency optimization strategies, cost estimates.

#### Question 3: Legacy Integration
```
How should we integrate a new AI recommendation engine with our existing mainframe banking systems?
```
**Use Case Details**:
- **AI Type**: ML/Recommendations
- **Legacy System**: Mainframe
- **Integration Points**: Customer data, transaction history
- **Compliance**: PCI-DSS, GDPR

**Expected Answer Quality**: Integration patterns, middleware recommendations, security considerations, phased migration plan, risk mitigation.

#### Question 4: Multi-Model Deployment
```
We need to deploy 15 different ML models that share common infrastructure. What's the best platform approach?
```
**Use Case Details**:
- **Number of Models**: 15
- **Update Frequency**: Weekly
- **Teams**: 3 different teams
- **SLA**: 99.9% uptime

**Expected Answer Quality**: Model serving platform options (KServe, SageMaker, etc.), CI/CD strategy, governance framework, cost optimization for shared infrastructure.

#### Question 5: POC to Production
```
Our chatbot POC was successful with 100 users. How do we scale to 100,000 production users?
```
**Use Case Details**:
- **Current**: POC on laptop (100 users)
- **Target**: Production (100,000 users)
- **Budget**: £400,000
- **Timeline**: 3 months

**Expected Answer Quality**: Scaling strategy, infrastructure requirements, cost breakdown, performance testing plan, phased rollout approach, risk assessment.

---

## Testing These Questions

### Via Streamlit UI

1. **Navigate** to the appropriate section (Leader Insights / Dashboard / Recommendations)
2. **Enter** the question exactly as shown
3. **Apply** any specified filters
4. **Review** the answer quality against expected criteria

### Via API with curl

```bash
# Leader Q&A Example
curl -X POST "http://localhost:8000/leader-qa" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Which AI initiatives should we prioritize for Q1 2025 based on ROI and strategic alignment?"
  }'

# Chat with Catalogue Example
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me all production AI projects with estimated ROI above 200% and budget under £500,000",
    "filters": {
      "environment": "Production",
      "budget_max": 500000
    }
  }'
```

### Via Postman

1. **Import** the collection: `AI_Insights_API.postman_collection.json`
2. **Create** new requests using the sample questions above
3. **Compare** API responses with UI responses for consistency

### Quality Check Criteria

For each answer, verify:
- ✅ **Accuracy**: Information is factually correct
- ✅ **Completeness**: All aspects of the question are addressed
- ✅ **Actionability**: Provides concrete next steps or recommendations
- ✅ **Context**: Uses actual data from your catalogue
- ✅ **Structure**: Well-formatted with clear sections

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

## MySQL Integration


⚡ **NEW**: Use MySQL as your data source instead of Excel files!

### Why Use MySQL?

- **Live Data**: Connect to live databases instead of static Excel files
- **Natural Language Queries**: Ask questions in plain English, get SQL automatically
- **Query Observability**: See exactly what SQL is generated and executed
- **Scalability**: Handle larger datasets efficiently
- **Enterprise Ready**: Integrate with existing data infrastructure

### Quick Start

#### 1. Set up MySQL Database

```bash
# Run the schema setup script
mysql -u root -p < scripts/setup_mysql_schema.sql
```

#### 2. Configure Data Source

Edit your `.env` file:

```bash
DATA_SOURCE=mysql  # Switch from 'excel' to 'mysql'

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=ai_insights
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_TABLE=ai_usecases
```

#### 3. Migrate Data (Optional)

If you have existing Excel data:

```bash
python scripts/migrate_excel_to_mysql.py
```

#### 4. Start Using Natural Language Queries

Navigate to **💬 Natural Language Query** tab in the web UI and ask questions like:

- "Show me all projects with ROI greater than 200%"
- "What is the average budget by team?"
- "List all production projects"

### Features

| Feature | Excel | MySQL |
|---------|-------|-------|
| Data Storage | Static files | Live database |
| Natural Language Queries | ❌ | ✅ |
| SQL Generation | ❌ | ✅ |
| Query Observability | ❌ | ✅ |
| Large Datasets | Limited | ✅ |
| Real-time Updates | ❌ | ✅ |
| Dashboard & Analytics | ✅ | ✅ |
| Leader Insights | ✅ | ✅ |

### Complete Guide

For detailed documentation, see **[MySQL Setup Guide](docs/MYSQL_SETUP.md)**:

- Database schema setup
- Connection configuration
- Data migration
- Natural language query examples
- Troubleshooting
- Security best practices

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

## Additional Documentation

### 📐 Architecture Details

For detailed information about the system architecture and LLM selection mechanism, see:

**[ARCHITECTURE.md](ARCHITECTURE.md)** - Complete technical architecture documentation including:
- How LLM selection works (Ollama vs Enterprise)
- Call flow diagrams
- Scripts that make LLM calls
- Configuration reference
- Mode switching guides

---

## Support Contact

For technical issues:
- Review this documentation thoroughly
- Check [Troubleshooting](#troubleshooting) section
- Run `python verify_all.py` for diagnostics
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- Contact your technical lead with error messages

---

**Version**: 2.0  
**Last Updated**: December 2025  
**Maintained by**: NatWest AI Platform Team

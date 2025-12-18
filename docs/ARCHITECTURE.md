# Architecture: AI Usage Insights Platform

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Core Design Decisions](#core-design-decisions)
3. [Question Answering Architecture](#question-answering-architecture)
4. [LLM Selection & Configuration](#llm-selection--configuration)
5. [Data Flow](#data-flow)
6. [Setup Guide (Local & Enterprise)](#setup-guide)

---

## 🎯 System Overview

**AI Usage Insights** is an enterprise platform for managing AI initiatives with intelligent question-answering capabilities powered by LLMs.

**Key Components**:
- **Streamlit UI** - Interactive dashboard for executives and analysts
- **FastAPI Backend** - REST API for programmatic access
- **Vector Database (ChromaDB)** - Semantic search over AI use cases
- **LLM Interface** - Unified abstraction over local (Ollama) and enterprise (Azure OpenAI) models
- **Analytics Engine** -Pre-computed aggregations for fast insights

**Technology Stack**:
- Python 3.12
- Streamlit (UI)
- FastAPI (API)
- ChromaDB (Vector DB)
- LangChain (LLM orchestration)
- Pandas (Data processing)

---

## 🔑 Core Design Decisions

### Decision 1: Pre-Computed Analytics vs SQL Generation

**The Fundamental Choice**: How should the system answer analytical questions about AI use cases?

#### Option A: SQL Generation (Agentic Approach)
*Example: [ai-data-science-team](https://github.com/business-science/ai-data-science-team)*

```python
# Agentic SQL approach
User Question: "Which platform has highest ROI?"
    ↓
LLM generates SQL: 
    SELECT platform, SUM(benefit)/SUM(cost) as ROI 
    FROM use_cases 
    GROUP BY platform 
    ORDER BY ROI DESC 
    LIMIT 1
    ↓
Execute SQL against database
    ↓
Return results
```

**Pros**:
- ✅ Handles arbitrary questions
- ✅ No need to pre-compute analytics
- ✅ Can answer unpredictable queries

**Cons**:
- ❌ Slower (LLM generation + SQL execution each time)
- ❌ Unpredictable SQL quality
- ❌ Risk of SQL injection
- ❌ Requires database access
- ❌ Inconsistent results (SQL varies)

#### Option B: Pre-Computed Analytics + Hybrid Q&A (Our Choice ✅)

```python
# Our hybrid approach
User Question: "Which platform has highest ROI?"
    ↓
Pattern Matching:
    - classify_question_intent() → 'strongest_investment'
    ↓
Direct Answer:
    - format_strongest_investment(pre_computed_analytics)
    - Returns: "Aiden is delivering strongest results with £X ROI"
    ↓  
Fast, deterministic result (no LLM needed for common patterns)

# For complex/unique questions:
User Question: "Should we shutdown platforms with low adoption in Q1?"
    ↓
No pattern match → Send to LLM with formatted analytics
    ↓
LLM analyzes pre-formatted data
    ↓
Strategic recommendation
```

**Why We Chose This Approach**:

1. **Speed** ⚡
   - Common questions: Instant (pattern matching)
   - Complex questions: Fast (pre-computed data sent to LLM)
   - No SQL generation delay

2. **Determinism** 🎯
   - Same question always returns same answer for same data
   - No variability in SQL generation
   - Predictable behavior for executives

3. **Security** 🔒
   - No SQL injection risk
   - No dynamic SQL execution
   - Controlled data access

4. **Accuracy** ✅
   - Pre-computed analytics verified upfront
   - Direct answers for common patterns (no LLM hallucination)
   - LLM only interprets pre-formatted data (not generating code)

5. **Executive Focus** 👔
   - Portfolio analytics are predictable (ROI, counts, costs, benefits)
   - Most questions fit common patterns
   - Rare questions handled by LLM with context

**Trade-offs**:
- ⚠️ Must anticipate common question patterns
- ⚠️ Pre-computation required on data changes
- ⚠️ Less flexible for completely novel queries

**Conclusion**: For an **executive dashboard** with **predictable analytics**, pre-computed + hybrid is optimal. For **ad-hoc data science** with **unpredictable queries**, SQL generation might be better.

---

### Decision 2: Hybrid Question Answering

**Implementation**: [llm/question_helpers.py](file:///Users/sameera/code/AiInsights_V2/llm/question_helpers.py)

```python
def get_direct_answer(question: str, analytics: Dict) -> Optional[str]:
    # Step 1: Classify intent
    intent = classify_question_intent(question)
    
    # Step 2: If pattern matches, return direct answer
    if intent == 'strongest_investment':
        return format_strongest_investment(analytics)
    elif intent == 'total_count':
        return f"Total use cases: {analytics['total_use_cases']}"
    # ... more patterns
    
    # Step 3: No match - return None (falls through to LLM)
    return None
```

**Patterns Supported**:
- `users_per_platform` - "How many users per platform?"
- `total_count` - "How many total use cases?"
- `best_roi` - "Which platform has best ROI?"
- `strongest_investment` - "Which investment delivering strongest results?"
- `cost_comparison` - "Compare costs across platforms"
- `platform_distribution` - "How are use cases distributed?"

**For Unmatched Questions**: Falls back to LLM with formatted analytics context.

---

### Decision 3: Filter-First Approach for Catalogue Chat

**Architecture**: [services.py - chat_with_catalogue](file:///Users/sameera/code/AiInsights_V2/services.py#L206)

```python
def chat_with_catalogue(question, df, usecases, user_filters, ...):
    # Step 1: Apply filters FIRST
    filtered_df = apply_filters(df, user_filters)
    
    # Step 2: Compute aggregates on FILTERED data
    agg_benefit = filtered_df.groupby("AIType")["Benefit"].sum()
    agg_budget = filtered_df.groupby("AIType")["Budget"].sum()
    agg_use_cases = filtered_df.groupby("AIType").size()
    
    # Step 3: Create explicit filter summary
    active_filters_summary = "AIType='AI Gateway' AND Environment='Production'"
    
    # Step 4: Send to LLM with filtered aggregates
    payload = {
        "active_filters_summary": active_filters_summary,
        "aggregates": {...},  # Only filtered data
        "metrics": {"filtered_count": X, "unfiltered_count": Y},
        "sample_usecases": [...]  # Only filtered records
    }
```

**Why Filter-First**:
- ✅ LLM sees only relevant data scope
- ✅ Prevents confusion from unfiltered aggregates
- ✅ Explicit `active_filters_summary` prevents LLM from misreading filters
- ✅ Can suggest alternatives if filters too restrictive

---

## 📊 Question Answering Architecture

### Component Breakdown

```
┌──────────────────────────────────────────────────────────────┐
│                     User Question                             │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│              services.py (Orchestration Layer)                │
│  - answer_leader_question() or chat_with_catalogue()         │
└────────────────────────┬─────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │ HYBRID DECISION POINT         │
         └───────────────┬───────────────┘
                         │
         ┌───────────────┴────────────────┐
         │                                │
         ▼                                ▼
┌──────────────────┐          ┌──────────────────────┐
│ Direct Answer    │          │ LLM Analysis         │
│ (Pattern Match)  │          │ (Complex Questions)  │
└────────┬─────────┘          └────────┬─────────────┘
         │                              │
         │ classify_question_intent()   │ format_analytics_for_llm()
         │ format_strongest_investment()│ LLMInterface.chat_completion_json()
         │                              │
         ▼                              ▼
┌──────────────────┐          ┌──────────────────────┐
│ Instant Result   │          │ Strategic Analysis   │
│ (No LLM call)    │          │ (LLM-powered)        │
└──────────────────┘          └──────────────────────┘
```

### Data Sources

**1. Pre-Computed Analytics** ([storage/analytics_queries.py](file:///Users/sameera/code/AiInsights_V2/storage/analytics_queries.py))

```python
def get_comprehensive_analytics(vdb: VectorDBManager):
    return {
        "total_use_cases": vdb.get_total_count(),
        "users_per_platform": get_users_per_platform(vdb),
        "use_cases_per_platform": get_count_per_platform(vdb),
        "budget_by_platform": get_budget_by_platform(vdb),
        "benefit_by_platform": get_benefit_by_platform(vdb),
        "roi_by_platform": get_roi_by_platform(vdb),
        "environment_distribution": get_environment_distribution(vdb),
        "cost_analysis": get_cost_analysis(vdb)
    }
```

**2. Formatted Analytics String**

```python
def format_analytics_for_llm(analytics: Dict) -> str:
    return """
    === OVERALL TOTALS ===
    Total Use Cases: {total}
    Total Users: {users}
    Total Budget: £{budget}
    
    === PLATFORM BREAKDOWN ===
    AI Gateway:
      - Use Cases: {count}
      - Budget: £{budget}
      - ROI: {roi}x
      ...
    """
```

**3. Strategic Priorities** (Decision Factors)

```python
{
    "description": "These are STRATEGIC WEIGHTS for decision-making, NOT platform scores",
    "weights": {
        "financial_benefit": 0.5,
        "cost_efficiency": 0.2,
        "governance_risk": 0.1,
        ...
    }
}
```

---

## 🔄 LLM Selection & Configuration

### The Decision Point

**[llm/lm_interface.py](file:///Users/sameera/code/AiInsights_V2/llm/lm_interface.py)** is the central abstraction that:
1. Reads configuration to determine which LLM to use
2. Initializes the appropriate LLM client
3. Provides a unified API for all LLM calls

### Configuration (.env)

```bash
# Option 1: Local Development
LLM_PROVIDER=ollama
OLLAMA_API_BASE=http://localhost:11434/v1
OLLAMA_CHAT_MODEL=llama3.2
OLLAMA_EMBED_MODEL=nomic-embed-text

# Option 2: Enterprise Deployment
LLM_PROVIDER=enterprise
LLM_API_BASE=https://your-gateway.com/genai/openai/gpt
LLM_DEPLOYMENT_NAME=gpt41_deployment_name
EMBEDDING_API_BASE=https://your-gateway.com/genai/openai/ada
EMBEDDING_DEPLOYMENT_NAME=ada002
```

### Initialization Flow

```python
# llm/lm_interface.py
class LLMInterface:
    def _initialize_client(self):
        if settings.llm_provider.lower() == "ollama":
            # Local Mode
            self.client_llm = ChatOpenAI(
                base_url=settings.ollama_api_base,
                model=settings.ollama_chat_model,
                api_key="ollama"  # Dummy key
            )
        else:
            # Enterprise Mode
            token = get_cached_or_new_token()  # JWT from auth.py
            self.client_llm = AzureChatOpenAI(
                azure_endpoint=settings.llm_api_base,
                openai_api_key=token,
                deployment_name=settings.llm_deployment_name
            )
```

### Switching Modes

1. Edit `.env`: Change `LLM_PROVIDER=ollama` to `LLM_PROVIDER=enterprise`
2. Restart application
3. No code changes required ✅

---

## 📦 Data Flow

### Complete Call Flow

```
┌─────────────────┐
│   User/API      │
│   Request       │
└────────┬────────┘
         │
         ▼
┌──────────────────┐
│  app_ui.py or    │  ← UI or API layer
│  api.py          │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  services.py     │  ← Business logic
│  - Loads data    │     • Get use cases from vector DB
│  - Filters       │     • Apply user filters
│  - Pre-computes  │     • Calculate aggregates
└────────┬─────────┘     • Format analytics
         │
         ▼
┌──────────────────┐
│ question_helpers │  ← Pattern matching (optional)
│  .py             │
└────────┬─────────┘
         │
    ┌────┴────┐
    │ Match?  │
    └────┬────┘
         │
    Yes  │  No
    │    │
    ▼    ▼
┌────┐  ┌────────────┐
│Done│  │LLMInterface│  ← LLM abstraction
└────┘  │ __init__   │
        └─────┬──────┘
              │
              ▼
        ┌──────────────┐
        │ _initialize_ │  ← Checks settings.llm_provider
        │   client()   │
        └─────┬────────┘
              │
         ┌────┴─────┐
         │          │
         ▼          ▼
    ┌─────────┐  ┌──────────────┐
    │ Ollama  │  │  Enterprise  │
    │localhost│  │ (Azure/Gem)  │
    └─────────┘  └──────────────┘
```

---

## 🚀 Setup Guide

### Prerequisites

**All Environments**:
- Python 3.12
- Git

**Local Development Only**:
- Ollama

### Quick Start: Local Mode

```bash
# 1. Clone repository
git clone <REPO_URL> ai-insights
cd ai-insights

# 2. Create environment
conda create -n ai-insights python=3.12 -y
conda activate ai-insights

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install & start Ollama
brew install ollama
ollama serve  # In separate terminal
ollama pull llama3.2
ollama pull nomic-embed-text

# 5. Configure .env
echo "LLM_PROVIDER=ollama" > .env
echo "OLLAMA_API_BASE=http://localhost:11434/v1" >> .env
echo "OLLAMA_CHAT_MODEL=llama3.2" >> .env
echo "OLLAMA_EMBED_MODEL=nomic-embed-text" >> .env

# 6. Validate setup
python verify_all.py

# 7. Run application
# Terminal 1:
uvicorn api:app --reload --port 8000

# Terminal 2:
streamlit run app.py
```

### Quick Start: Enterprise Mode

```bash
# Steps 1-3: Same as local

# 4. Configure .env for enterprise
cat > .env << EOF
LLM_PROVIDER=enterprise

# Authentication
SERVICE_ACCOUNT=your_service_account
SERVICE_ACCOUNT_PASS=your_password
AUTH_URL=https://your-gateway.com/token

# LLM Configuration
LLM_API_BASE=https://your-gateway.com/genai/openai/gpt
LLM_DEPLOYMENT_NAME=gpt41_deployment
EMBEDDING_API_BASE=https://your-gateway.com/genai/openai/ada
EMBEDDING_DEPLOYMENT_NAME=ada002
EOF

# 5. Validate
python verify_all.py

# 6. Run (same as local)
```

**Detailed Setup**: See [README.md](file:///Users/sameera/code/AiInsights_V2/README.md)

---

## 🔑 Key Design Principles

1. **Pre-Computed > Dynamic SQL**
   - Executive dashboards have predictable questions
   - Speed and determinism prioritized
   - Security through controlled data access

2. **Hybrid Answering**
   - Direct answers for common patterns (fast)
   - LLM for complex analysis (flexible)
   - Best of both worlds

3. **Filter-First Architecture**
   - Apply user filters before aggregation
   - Explicit filter context for LLM
   - Prevents scope confusion

4. **Single Source of Truth**
   - `.env` controls all configuration
   - No code changes to switch LLM modes
   - Unified interface abstracts provider details

5. **Separation of Concerns**
   - `services.py` = Business logic
   - `llm/lm_interface.py` = LLM abstraction
   - `llm/question_helpers.py` = Pattern matching
   - `storage/analytics_queries.py` = Data aggregation

---

## 📚 Related Documentation

- **[README.md](file:///Users/sameera/code/AiInsights_V2/README.md)** - Complete setup and usage guide
- **[API Collection](file:///Users/sameera/code/AiInsights_V2/AI_Insights_API.postman_collection.json)** - Postman collection for API testing
- **[Question Helpers](file:///Users/sameera/code/AiInsights_V2/llm/question_helpers.py)** - Pattern matching implementation
- **[Analytics Queries](file:///Users/sameera/code/AiInsights_V2/storage/analytics_queries.py)** - Pre-computation logic

# Architecture: How LLM Selection Works

## 🎯 Overview

The application uses a **unified interface** that automatically switches between local (Ollama) and enterprise (Azure/Gemini) LLMs based on a single configuration setting.

## 🔑 The Decision Point

**[llm/lm_interface.py](file:///Users/sameera/code/opportunity-mine_antigravity_version/llm/lm_interface.py)** is the central script that:
1. Reads configuration to determine which LLM to use
2. Initializes the appropriate LLM client
3. Provides a unified API for all LLM calls

## 📊 How the Choice is Made

### Step 1: Configuration File (.env)

The `.env` file contains a single control variable:

```bash
# Option 1: Local Development
LLM_PROVIDER=ollama

# Option 2: Enterprise Deployment  
LLM_PROVIDER=enterprise
```

### Step 2: Settings Loading

`config/settings.py` loads the `.env` file using Pydantic:

```python
# config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")
    # ... other settings
    
settings = Settings()  # Auto-loads from .env
```

### Step 3: LLM Interface Initialization

`llm/lm_interface.py` checks the provider and initializes accordingly:

```python
# llm/lm_interface.py (simplified)
from config.settings import settings

class LLMInterface:
    def _initialize_client(self):
        if settings.llm_provider.lower() == "ollama":
            # Local Mode: Use Ollama
            self.client_llm = ChatOpenAI(
                base_url=settings.ollama_api_base,      # http://localhost:11434/v1
                model=settings.ollama_chat_model,       # llama3.2
                api_key="ollama"                        # Dummy key for Ollama
            )
        else:
            # Enterprise Mode: Use Azure/Gemini
            token = get_cached_or_new_token()           # From auth.py
            self.client_llm = AzureChatOpenAI(
                azure_endpoint=settings.llm_api_base,   # Corporate gateway
                openai_api_key=token,                   # JWT token
                deployment_name=settings.llm_deployment_name
            )
```

## 🔄 Complete Call Flow

```
┌─────────────────┐
│   User/API      │
│   Request       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  services.py    │  ← Business logic layer
│  Line ~147      │     • Filters data
└────────┬────────┘     • Calculates metrics
         │              • Prepares payload
         ▼
┌─────────────────┐
│ LLMInterface()  │  ← Creates instance
│  __init__       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│_initialize_     │  ← Checks settings.llm_provider
│   client()      │
└────────┬────────┘
         │
    ┌────┴─────┐
    │          │
    ▼          ▼
┌─────────┐  ┌──────────────┐
│ Ollama  │  │  Enterprise  │
│         │  │  (Azure/     │
│localhost│  │   Gemini)    │
└─────────┘  └──────────────┘
```

## 📂 Scripts That Make LLM Calls

### 1. **services.py** (Primary Caller)
```python
# services.py, Line ~147
from llm.lm_interface import LLMInterface

def answer_leader_question(question: str, ...):
    llm = LLMInterface()  # Creates instance based on .env
    result = llm.chat_completion_json(
        system_prompt=system,
        payload={"question": question, "context": context},
        answer_model=LeaderInsightAnswer
    )
    return result
```

**What it does:**
- Processes business logic (filtering, calculations)
- Creates LLMInterface instance
- Makes structured LLM calls
- Returns parsed results

### 2. **api.py** (Uses services.py)
```python
# api.py
import services

@app.post("/chat")
def chat_with_catalogue(req: ChatRequest):
    # Indirectly uses LLMInterface via services
    result = services.chat_with_catalogue(
        question=req.question,
        df=df,
        usecases=usecases,
        user_filters=filters,
        decision_factors=decision_factors
    )
    return result
```

**What it does:**
- Exposes REST API endpoints
- Delegates to services.py
- Never directly calls LLM (uses service layer)

### 3. **storage/vector_db_manager.py** (For Embeddings)
```python
# storage/vector_db_manager.py, Line ~18
from llm.lm_interface import LLMInterface

class CustomEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        self.llm = LLMInterface()  # For embedding generation
    
    def __call__(self, input: Documents) -> Embeddings:
        return self.llm.embed_texts(input)  # Calls appropriate embedding service
```

**What it does:**
- Generates embeddings for vector database
- Uses same LLMInterface for consistency
- Automatically uses correct embedding service (Ollama or Enterprise)

### 4. **app_ui.py** (Streamlit UI)
```python
# app_ui.py (indirectly via services)
def render_leader_insights():
    # Uses services.py which uses LLMInterface
    answer = services.answer_leader_question(...)
```

**What it does:**
- Renders UI components
- Calls services.py for LLM operations
- Never directly instantiates LLMInterface

## 🎛️ Configuration Reference

### Local Mode (.env)
```bash
LLM_PROVIDER=ollama
OLLAMA_API_BASE=http://localhost:11434/v1
OLLAMA_CHAT_MODEL=llama3.2
OLLAMA_EMBED_MODEL=nomic-embed-text
```

### Enterprise Mode (.env)
```bash
LLM_PROVIDER=enterprise
LLM_API_BASE=https://your-gateway.com/genai/openai/gpt41
LLM_DEPLOYMENT_NAME=gpt41_deployment_name
EMBEDDING_API_BASE=https://your-gateway.com/genai/openai/ada/openai2/deployments
EMBEDDING_DEPLOYMENT_NAME=ada002
```

## 🔄 Switching Modes

To switch between local and enterprise:

1. **Edit `.env` file**:
   ```bash
   # Change this line:
   LLM_PROVIDER=ollama      # For local
   # OR
   LLM_PROVIDER=enterprise  # For enterprise
   ```

2. **Restart the application**:
   ```bash
   # Stop current processes (Ctrl+C)
   
   # Restart API
   uvicorn api:app --reload --port 8000
   
   # Restart Streamlit
   streamlit run app.py
   ```

3. **Verify the mode**:
   ```bash
   python verify_all.py
   # Should show: "✅ Settings loaded. Provider: [ollama|enterprise]"
   ```

## 🧪 Testing Different Modes

```bash
# Test Local Mode
echo "LLM_PROVIDER=ollama" > .env.local
cp .env.local .env
python verify_all.py

# Test Enterprise Mode (requires credentials)
echo "LLM_PROVIDER=enterprise" > .env.enterprise
# ... add all enterprise settings
cp .env.enterprise .env
python verify_all.py
```

## 📝 Key Design Principles

1. **Single Source of Truth**: `.env` file controls everything
2. **Unified Interface**: Same code works with both LLMs
3. **No Code Changes**: Switch modes by changing configuration only
4. **Separation of Concerns**: 
   - `services.py` = Business logic
   - `llm/lm_interface.py` = LLM abstraction
   - `api.py` = API layer
5. **Consistent Behavior**: Same API regardless of LLM provider

---

**Related Documentation:**
- [Setup Guide](README.md) - Complete installation and usage instructions
- [API Reference](AI_Insights_API.postman_collection.json) - Postman collection for API testing

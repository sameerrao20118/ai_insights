from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import services
from finops.finops_config import load_finops_config

app = FastAPI(title="AI Usage Insights API")

class ChatRequest(BaseModel):
    question: str
    filters: Optional[Dict[str, Any]] = None

class LeaderQARequest(BaseModel):
    question: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/chat")
def chat_with_catalogue(req: ChatRequest):
    try:
        usecases = services.load_all_usecases()
        df = services.usecases_to_df(usecases)
        
        # Load default decision factors from config
        decision_factors = load_finops_config()
        
        # Default empty filters if None
        filters = req.filters or {}
        
        result = services.chat_with_catalogue(
            question=req.question,
            df=df,
            usecases=usecases,
            user_filters=filters,
            decision_factors=decision_factors
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/leader-qa")
def answer_leader_question(req: LeaderQARequest):
    try:
        usecases = services.load_all_usecases()
        df = services.usecases_to_df(usecases)
        decision_factors = load_finops_config()
        
        raw_answer = services.answer_leader_question(
            question=req.question,
            df=df,
            usecases=usecases,
            decision_factors=decision_factors
        )
        # Parse if it returns JSON string, though api usually returns dict
        # The service returns a string (raw response from LLM), so we parse it
        parsed = services.parse_llm_json(raw_answer)
        return parsed
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

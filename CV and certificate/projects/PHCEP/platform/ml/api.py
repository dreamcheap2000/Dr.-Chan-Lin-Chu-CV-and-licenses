"""
PHCEP ML Microservice — FastAPI application.

Endpoints:
  POST /encode  — encode text with FastSR (semantic + global + fragment)
  POST /query   — retrieve top-k answers for a patient query from longitudinal context;
                  returns synthesised answer, per-match ranked list, confidence, and
                  escalation flag so the frontend can render dynamic result cards
  GET  /health  — liveness check
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from encoder import PhcepEncoder
from query_engine import QueryEngine

app = FastAPI(title="PHCEP ML Service", version="0.2.0")

encoder = PhcepEncoder()
query_engine = QueryEngine(encoder)


# ─── Request / Response schemas ───────────────────────────────────────────────

class EncodeRequest(BaseModel):
    text: str


class EncodeResponse(BaseModel):
    semantic: List[float]
    global_ctx: List[float]
    fragment: List[float]


class QueryRequest(BaseModel):
    pseudonymous_token: str
    query_text: str
    top_k: int = 3
    entry_types: Optional[List[str]] = None  # e.g. ["ICD10", "SYMPTOM"]


class MatchItem(BaseModel):
    rank: int
    text: str
    confidence: float
    citation: str
    source: str       # "observation" | "ebm"
    url: str


class QueryResponse(BaseModel):
    answer: str
    citations: str
    confidence: float
    matches: List[MatchItem]
    escalated: bool   # True when best confidence < threshold


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/encode", response_model=EncodeResponse)
def encode(req: EncodeRequest):
    """Encode text using FastSR semantic, global, and fragment encoders."""
    try:
        result = encoder.encode(req.text)
        return EncodeResponse(
            semantic=result["semantic"],
            global_ctx=result["global"],
            fragment=result["fragment"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    """
    Retrieve top-k answers for a query using the patient's longitudinal context.
    Combines FastSR semantic retrieval with EBM knowledge base.
    Returns a per-match ranked list so the frontend can display dynamic result
    cards (top 1–5, configurable) alongside an overall synthesised answer.
    """
    try:
        result = query_engine.answer(
            pseudonymous_token=req.pseudonymous_token,
            query_text=req.query_text,
            top_k=req.top_k,
            entry_types=req.entry_types,
        )
        return QueryResponse(
            answer=result["answer"],
            citations=result["citations"],
            confidence=result["confidence"],
            matches=[MatchItem(**m) for m in result["matches"]],
            escalated=result["escalated"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8081, reload=True)

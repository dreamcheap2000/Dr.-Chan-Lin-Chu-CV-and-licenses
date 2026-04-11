"""
PHCEP ML Microservice — FastAPI application.

Endpoints:
  POST /encode  — encode text with FastSR (semantic + global + fragment)
  POST /query   — retrieve top-k answers for a patient query from longitudinal context
  GET  /health  — liveness check
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn

from encoder import PhcepEncoder
from query_engine import QueryEngine

app = FastAPI(title="PHCEP ML Service", version="0.1.0")

encoder = PhcepEncoder()
query_engine = QueryEngine(encoder)


# ─── Request / Response schemas ───────────────────────────────────────────────

class EncodeRequest(BaseModel):
    text: str


class EncodeResponse(BaseModel):
    semantic: list[float]
    global_ctx: list[float]
    fragment: list[float]


class QueryRequest(BaseModel):
    pseudonymous_token: str
    query_text: str
    top_k: int = 5


class QueryResponse(BaseModel):
    answer: str
    citations: str
    confidence: float


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
    """
    try:
        result = query_engine.answer(
            pseudonymous_token=req.pseudonymous_token,
            query_text=req.query_text,
            top_k=req.top_k,
        )
        return QueryResponse(
            answer=result["answer"],
            citations=result["citations"],
            confidence=result["confidence"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8081, reload=True)

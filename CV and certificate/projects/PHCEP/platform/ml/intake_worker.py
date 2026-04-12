"""
PHCEP Intake Worker — FastAPI microservice for Workflow A.

Exposes:
  POST /intake/embed   — encode raw clinical text with FastSR and return
                         the semantic vector (called async by Spring Boot
                         immediately after a new ClinicalEntry is persisted)
  GET  /intake/health  — liveness check
"""

import sys
import os
import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn

# Reuse the shared PhcepEncoder from the platform/ml directory
_THIS_DIR = os.path.dirname(__file__)
_ML_DIR = os.path.abspath(os.path.join(_THIS_DIR, "../ml"))
if _ML_DIR not in sys.path:
    sys.path.insert(0, _ML_DIR)

from encoder import PhcepEncoder  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PHCEP Intake Worker", version="1.0.0")
encoder = PhcepEncoder()


# ─── Request / Response schemas ───────────────────────────────────────────────

class EmbedRequest(BaseModel):
    text: str


class EmbedResponse(BaseModel):
    semantic: List[float]
    global_ctx: List[float]
    fragment: List[float]


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/intake/health")
def health():
    return {"status": "ok"}


@app.post("/intake/embed", response_model=EmbedResponse)
def embed(req: EmbedRequest):
    """
    Encode a raw clinical text snippet with FastSR.

    Called async by Spring Boot's IntakeEmbedService after a new
    ClinicalEntry is created.  Returns all three embedding channels
    (semantic / global / fragment) so the caller can store whichever
    representations it needs.
    """
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")
    try:
        result = encoder.encode(req.text)
        return EmbedResponse(
            semantic=result["semantic"],
            global_ctx=result["global"],
            fragment=result["fragment"],
        )
    except Exception as e:
        logger.error("Embedding failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.environ.get("INTAKE_WORKER_PORT", "8082"))
    uvicorn.run("intake_worker:app", host="0.0.0.0", port=port, reload=True)

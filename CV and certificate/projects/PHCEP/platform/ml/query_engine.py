"""
PHCEP Query Engine — retrieves and synthesises answers from:
  1. The patient's longitudinal health observations (individual context)
  2. The EBM knowledge base (generalised evidence)
  3. Workflow A clinical entries (doctor-entered ICD-10, symptoms, EBM summaries)

Uses cosine similarity between FastSR embeddings to rank candidates,
then constructs a synthesised answer string and exposes per-match scores
so that the frontend can render dynamic top-K result cards.
"""

import json
import logging
import os
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


def cosine_similarity(a: List[float], b: List[float]) -> float:
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    norm_a = np.linalg.norm(va)
    norm_b = np.linalg.norm(vb)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(va, vb) / (norm_a * norm_b))


class QueryEngine:
    """
    Retrieval-augmented answer synthesis using FastSR embeddings.

    In Phase 1 the engine calls the backend database via HTTP to retrieve
    candidate records (observations + EBM entries + clinical entries).
    In Phase 2 a dedicated vector store (pgvector or Qdrant) will be used
    for sub-millisecond ANN search.
    """

    CONFIDENCE_THRESHOLD = 0.60

    def __init__(self, encoder, backend_url: Optional[str] = None):
        self.encoder = encoder
        self.backend_url = backend_url or os.environ.get(
            "PHCEP_BACKEND_URL", "http://localhost:8080"
        )

    def answer(
        self,
        pseudonymous_token: str,
        query_text: str,
        top_k: int = 5,
        entry_types: Optional[List[str]] = None,
    ) -> Dict:
        """
        Main retrieval + synthesis pipeline:
          1. Encode the query
          2. Retrieve candidates from observations, EBM entries, and clinical entries
          3. Rank by cosine similarity (semantic channel)
          4. Synthesise answer from top-k
          5. Return answer string + citations + confidence score +
             individual ranked matches + escalation flag
        """
        query_emb = self.encoder.encode(query_text)
        query_vec = query_emb["semantic"]

        candidates = self._retrieve_candidates(
            pseudonymous_token, query_vec, top_k, entry_types
        )

        if not candidates:
            return {
                "answer": (
                    "No relevant records found for this query. "
                    "A healthcare professional has been notified."
                ),
                "citations": "",
                "confidence": 0.0,
                "matches": [],
                "escalated": True,
            }

        top = candidates[0]
        confidence = top["score"]
        escalated = confidence < self.CONFIDENCE_THRESHOLD

        answer_parts = ["Based on your health records and evidence-based sources:"]
        citations = []

        for c in candidates[:top_k]:
            answer_parts.append(f"• {c['text']}")
            if c.get("citation"):
                citations.append(c["citation"])

        # Build structured match list for frontend display
        matches = [
            {
                "rank": idx + 1,
                "text": c["text"],
                "confidence": round(c["score"], 4),
                "citation": c.get("citation", ""),
                "source": c.get("source", "observation"),
                "url": c.get("url", ""),
            }
            for idx, c in enumerate(candidates[:top_k])
        ]

        return {
            "answer": "\n".join(answer_parts),
            "citations": "; ".join(citations),
            "confidence": confidence,
            "matches": matches,
            "escalated": escalated,
        }

    def _retrieve_candidates(
        self,
        pseudonymous_token: str,
        query_vec: List[float],
        top_k: int,
        entry_types: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Retrieve and rank candidate records from:
          - Patient observations
          - EBM knowledge base
          - Workflow A clinical entries (filtered by entry_types when provided)

        Phase 1: HTTP calls to Spring Boot backend.
        Phase 2: Direct pgvector / Qdrant query.
        """
        try:
            import httpx
        except ImportError:
            logger.warning("httpx not available; returning empty candidates")
            return []

        scored: List[Dict] = []

        # --- Patient observations ---
        try:
            resp = httpx.get(
                f"{self.backend_url}/api/patient/observations",
                params={"pseudonymous_token": pseudonymous_token},
                timeout=10,
            )
            if resp.status_code == 200:
                for rec in resp.json():
                    emb_json = rec.get("semanticEmbeddingJson")
                    score = (
                        cosine_similarity(query_vec, json.loads(emb_json))
                        if emb_json
                        else 0.0
                    )
                    scored.append({
                        "text": rec.get("observationText", ""),
                        "score": score,
                        "citation": rec.get("loincCode", ""),
                        "source": "observation",
                        "url": "",
                    })
        except Exception as e:
            logger.warning("Observation retrieval failed: %s", e)

        # --- EBM knowledge base ---
        try:
            resp = httpx.get(
                f"{self.backend_url}/api/ebm",
                timeout=10,
            )
            if resp.status_code == 200:
                for entry in resp.json():
                    emb_json = entry.get("semanticEmbeddingJson")
                    score = (
                        cosine_similarity(query_vec, json.loads(emb_json))
                        if emb_json
                        else 0.0
                    )
                    scored.append({
                        "text": entry.get("statement", ""),
                        "score": score,
                        "citation": entry.get("pmid", ""),
                        "source": "ebm",
                        "url": entry.get("articleUrl", ""),
                    })
        except Exception as e:
            logger.warning("EBM retrieval failed: %s", e)

        # --- Workflow A: Clinical entries ---
        try:
            params: Dict = {
                "pseudonymousToken": pseudonymous_token,
                "size": 200,
                "page": 0,
            }
            if entry_types:
                # Pass the first entry_type as a filter (API supports one at a time)
                params["entryType"] = entry_types[0]

            resp = httpx.get(
                f"{self.backend_url}/api/entries",
                params=params,
                timeout=10,
            )
            if resp.status_code == 200:
                page_data = resp.json()
                # Spring Page returns { content: [...], ... }
                content = page_data.get("content", page_data) if isinstance(page_data, dict) else page_data
                for entry in content:
                    emb_json = entry.get("semanticEmbeddingJson")
                    # Filter by entry_types if more than one was requested
                    if entry_types and entry.get("entryType") not in entry_types:
                        continue
                    score = (
                        cosine_similarity(query_vec, json.loads(emb_json))
                        if emb_json
                        else 0.0
                    )
                    text = entry.get("rawText", "")
                    if entry.get("ebmStatement"):
                        text = entry["ebmStatement"]
                    scored.append({
                        "text": text,
                        "score": score,
                        "citation": entry.get("icd10Code", ""),
                        "source": "clinical_entry",
                        "url": entry.get("sourceUrl", ""),
                        "gemini_category": entry.get("geminiCategory", ""),
                        "entry_type": entry.get("entryType", ""),
                    })
        except Exception as e:
            logger.warning("Clinical entry retrieval failed: %s", e)

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]


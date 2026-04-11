"""
PHCEP Query Engine — retrieves and synthesises answers from:
  1. The patient's longitudinal health observations (individual context)
  2. The EBM knowledge base (generalised evidence)

Uses cosine similarity between FastSR embeddings to rank candidates,
then constructs a synthesised answer string.
"""

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
    candidate records (observations + EBM entries).  In Phase 2 a
    dedicated vector store (pgvector or Qdrant) will be used for
    sub-millisecond ANN search.
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
    ) -> Dict:
        """
        Main retrieval + synthesis pipeline:
          1. Encode the query
          2. Retrieve candidate observations + EBM entries
          3. Rank by cosine similarity (semantic channel)
          4. Synthesise answer from top-k
          5. Return answer string + citations + confidence score
        """
        query_emb = self.encoder.encode(query_text)
        query_vec = query_emb["semantic"]

        # In a full deployment, candidates come from the vector store.
        # For the scaffold, we return a structured placeholder.
        candidates = self._retrieve_candidates(pseudonymous_token, query_vec, top_k)

        if not candidates:
            return {
                "answer": (
                    "No relevant records found for this query. "
                    "A healthcare professional has been notified."
                ),
                "citations": "",
                "confidence": 0.0,
            }

        top = candidates[0]
        confidence = top["score"]
        answer_parts = [f"Based on your health records and evidence-based sources:"]
        citations = []

        for c in candidates[:top_k]:
            answer_parts.append(f"• {c['text']}")
            if c.get("citation"):
                citations.append(c["citation"])

        return {
            "answer": "\n".join(answer_parts),
            "citations": "; ".join(citations),
            "confidence": confidence,
        }

    def _retrieve_candidates(
        self,
        pseudonymous_token: str,
        query_vec: List[float],
        top_k: int,
    ) -> List[Dict]:
        """
        Retrieve and rank candidate records.
        Phase 1: HTTP call to Spring Boot backend.
        Phase 2: Direct pgvector / Qdrant query.
        """
        try:
            import httpx
            resp = httpx.get(
                f"{self.backend_url}/api/patient/observations",
                params={"pseudonymous_token": pseudonymous_token},
                timeout=10,
            )
            if resp.status_code != 200:
                return []
            records = resp.json()
            scored = []
            for rec in records:
                emb_json = rec.get("semanticEmbeddingJson")
                if emb_json:
                    import json
                    vec = json.loads(emb_json)
                    score = cosine_similarity(query_vec, vec)
                else:
                    score = 0.0
                scored.append({
                    "text": rec.get("observationText", ""),
                    "score": score,
                    "citation": rec.get("loincCode", ""),
                })
            scored.sort(key=lambda x: x["score"], reverse=True)
            return scored[:top_k]
        except Exception as e:
            logger.warning("Candidate retrieval failed: %s", e)
            return []

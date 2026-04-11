"""
PHCEP Encoder — wraps FastSR semantic, global-context, and fragment-attention encoders.

The FastSR model code lives at ../../FastSR/src/model.py.
This module provides a unified interface for the ML microservice.
"""

import sys
import os
import logging
from typing import Dict, List

import torch
import numpy as np

# Add FastSR src to path
FASTSR_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../FastSR/src"))
if FASTSR_SRC not in sys.path:
    sys.path.insert(0, FASTSR_SRC)

logger = logging.getLogger(__name__)


class PhcepEncoder:
    """
    Unified encoder that produces three complementary vector representations
    for any input text, mirroring the FastSR tri-encoder design:

      - semantic   : surface-level BERT/BiLSTM sentence embedding
      - global     : document-section context embedding
      - fragment   : fragment-attention weighted token embedding
    """

    def __init__(self, device: str = "cpu"):
        self.device = device
        self._semantic_model = None
        self._global_model = None
        self._tokenizer = None
        self._load_models()

    def _load_models(self):
        """
        Load pre-trained FastSR models.
        Falls back to a lightweight transformer if FastSR weights are unavailable
        (useful for initial scaffold / unit testing).
        """
        try:
            from transformers import AutoTokenizer, AutoModel
            model_name = os.environ.get("PHCEP_BASE_MODEL", "dmis-lab/biobert-base-cased-v1.2")
            logger.info("Loading base model: %s", model_name)
            self._tokenizer = AutoTokenizer.from_pretrained(model_name)
            self._semantic_model = AutoModel.from_pretrained(model_name).to(self.device)
            self._semantic_model.eval()
            logger.info("Encoder models loaded successfully.")
        except Exception as e:
            logger.warning("Could not load transformer models (%s). Using random embeddings.", e)
            self._tokenizer = None
            self._semantic_model = None

    def encode(self, text: str) -> Dict[str, List[float]]:
        """
        Encode a text string into three embedding vectors.

        Returns:
            dict with keys 'semantic', 'global', 'fragment',
            each a list of floats (embedding dimension = 768 for BioBERT).
        """
        if self._semantic_model is None or self._tokenizer is None:
            return self._random_embeddings()

        with torch.no_grad():
            inputs = self._tokenizer(
                text,
                return_tensors="pt",
                max_length=512,
                truncation=True,
                padding=True,
            ).to(self.device)

            outputs = self._semantic_model(**inputs)
            # [CLS] token as sentence embedding (semantic)
            semantic = outputs.last_hidden_state[:, 0, :].squeeze().cpu().numpy()

            # Token embeddings for fragment attention
            token_embeddings = outputs.last_hidden_state.squeeze(0).cpu().numpy()
            # Simple mean-pool as fragment representation
            fragment = token_embeddings.mean(axis=0)

            # Global context: for now same as semantic; Phase 2 will use section classifier
            global_ctx = semantic.copy()

        return {
            "semantic": semantic.tolist(),
            "global": global_ctx.tolist(),
            "fragment": fragment.tolist(),
        }

    def _random_embeddings(self, dim: int = 768) -> Dict[str, List[float]]:
        rng = np.random.default_rng(42)
        return {
            "semantic": rng.standard_normal(dim).tolist(),
            "global": rng.standard_normal(dim).tolist(),
            "fragment": rng.standard_normal(dim).tolist(),
        }

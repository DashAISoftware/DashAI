"""Shared utilities for RAG services.

Provides deterministic parameter normalisation and hashing used
across Prompt, LLM, and other RAG services.
"""

import hashlib
import json
from typing import Any


def normalize_params(params: dict[str, Any]) -> dict[str, Any]:
    """Recursively sort all dict keys for deterministic serialization.

    Uses a JSON round-trip with ``sort_keys=True`` to ensure identical
    JSON text for semantically equivalent parameter dicts, even when
    they contain nested dicts with non-deterministic key ordering.

    Args:
        params: Parameter dict to normalize.

    Returns:
        A new dict with all keys (including nested) in sorted order.
    """
    return json.loads(json.dumps(params, sort_keys=True))


def build_parameters_hash(params: dict[str, Any]) -> str:
    """Build a deterministic SHA-256 hash of the parameters dict.

    Uses ``json.dumps`` with ``sort_keys=True`` for recursive key
    sorting, matching the hash computation used in the migration.

    Args:
        params: Parameter dict to hash.

    Returns:
        Hex digest of the SHA-256 hash.
    """
    return hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()

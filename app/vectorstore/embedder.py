"""
embedder.py — Embedding Model Wrapper
======================================
WHAT THIS FILE DOES:
    Provides a single function that returns a configured embedding model.
    All other modules import from here — so if we ever swap embedding
    providers, we only change this one file.

TWO MODES (controlled by EMBEDDING_MODE in .env):
    "openai"  → Calls OpenAI's /embeddings API (costs money, 1536 dims)
                 Requires OPENAI_API_KEY to be set with billing credits.
    "local"   → Uses sentence-transformers running on your own machine
                 (free, no API key needed, 384 dims, ~80MB model download)

    For development and learning, "local" is recommended.
    For production, switch to "openai" for higher quality embeddings.

WHY A SEPARATE FILE FOR THIS?
    Dependency Inversion principle: nothing in our system directly
    instantiates a specific embedding class. They all call get_embedding_model().
    If we swap providers, we change ONE function here and nothing else changes.
"""

import os
import httpx
from dotenv import load_dotenv

# Load .env so OPENAI_API_KEY is available in os.environ
# override=True ensures .env always wins over any system-level env vars
load_dotenv(override=True)


def get_embedding_model():
    """
    Returns a configured embedding model based on EMBEDDING_MODE in .env.

    Mode "local"  → HuggingFaceEmbeddings (sentence-transformers, free)
    Mode "openai" → OpenAIEmbeddings (requires API key + billing credits)

    Returns:
        An embedding model compatible with LangChain's vectorstore interface.
    """
    mode = os.getenv("EMBEDDING_MODE", "local").lower()

    if mode == "local":
        return _get_local_embedding_model()
    else:
        return _get_openai_embedding_model()


def _get_local_embedding_model():
    """
    Returns a local sentence-transformers embedding model.

    MODEL: all-MiniLM-L6-v2
        - Produces 384-dimensional vectors
        - Downloads ~80MB on first use (cached locally after that)
        - Fast on CPU, no GPU required
        - Free, no API key needed
        - Great for development and learning

    The model is downloaded automatically from HuggingFace on first call
    and cached in your home directory (~/.cache/huggingface/).
    """
    import urllib3
    import requests
    from langchain_community.embeddings import HuggingFaceEmbeddings

    # ── Corporate proxy SSL bypass ────────────────────────────────
    # HuggingFace uses the `requests` library to download models.
    # On corporate networks the proxy intercepts HTTPS with a self-signed
    # cert that Python doesn't trust. We patch requests.Session to always
    # pass verify=False — the same way we used --trusted-host for pip.
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    _orig = requests.Session.request
    def _no_verify(self, method, url, **kwargs):
        kwargs.setdefault("verify", False)
        return _orig(self, method, url, **kwargs)
    requests.Session.request = _no_verify

    # Suppress the tokenizers parallelism warning (harmless, just noisy)
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    model_name = os.getenv("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},   # use "cuda" if you have a GPU
        encode_kwargs={"normalize_embeddings": True},  # cosine similarity ready
    )


def _get_openai_embedding_model():
    """
    Returns an OpenAI embedding model.

    Requires:
        - OPENAI_API_KEY set in .env with valid billing credits
        - Internet access (SSL may need corporate proxy bypass)
    """
    from langchain_openai import OpenAIEmbeddings

    # Guard: fail fast and clearly if the API key is missing or still the placeholder
    # This is better than getting a cryptic 401 error from the API later
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.strip() == "sk-...":
        raise ValueError(
            "OPENAI_API_KEY is not set.\n"
            "Please copy .env.example to .env and add your real API key.\n"
            "Or set EMBEDDING_MODE=local in .env to use a free local model."
        )

    model_name = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    # Corporate proxy environments intercept HTTPS and use a self-signed cert.
    # We pass a custom httpx.Client with verify=False to bypass SSL verification.
    # This is the same reason we use --trusted-host with pip on this network.
    # NOTE: only do this in a trusted corporate network — not in production.
    http_client = httpx.Client(verify=False)

    # OpenAIEmbeddings is a LangChain class that wraps OpenAI's /embeddings API.
    # It handles batching (sending multiple texts in one API call) automatically.
    return OpenAIEmbeddings(
        model=model_name,
        openai_api_key=api_key,
        http_client=http_client,
    )

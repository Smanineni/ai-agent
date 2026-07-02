"""
llm.py — LLM (Chat Model) Factory
===================================
WHAT THIS FILE DOES:
    Single place to create and configure the chat model used by all engines.
    Every module that needs to call an LLM imports get_llm() from here.

    Supports three providers — selected via LLM_PROVIDER in .env:

    PROVIDER A — openai  (paid, GPT-4o)
        Needs: OPENAI_API_KEY with billing credits
        Config: OPENAI_MODEL=gpt-4o

    PROVIDER B — groq  (free tier, Llama 3 / Mixtral via cloud API)
        Needs: GROQ_API_KEY from console.groq.com (free sign-up)
        Config: GROQ_MODEL=llama-3.3-70b-versatile
        Speed:  Very fast — Groq uses custom LPU hardware

    PROVIDER C — ollama  (fully local, no API key, no internet)
        Needs: Ollama installed + model pulled (ollama pull llama3)
        Config: OLLAMA_BASE_URL=http://localhost:11434, OLLAMA_MODEL=llama3
        Speed:  Depends on your machine's CPU/GPU

WHY A CENTRAL FACTORY?
    If we ever switch providers, we change LLM_PROVIDER in .env.
    Zero code changes required anywhere else.

TEMPERATURE:
    Controls randomness of LLM output.
    - temperature=0   → deterministic (best for SQL generation)
    - temperature=0.7 → more creative (better for free-form answers)
"""

import os
import httpx
from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel

load_dotenv(override=True)

# Valid provider names
PROVIDER_OPENAI = "openai"
PROVIDER_GROQ   = "groq"
PROVIDER_OLLAMA = "ollama"


def get_llm(temperature: float = 0) -> BaseChatModel:
    """
    Returns a configured chat model based on LLM_PROVIDER in .env.

    LLM_PROVIDER options:
        "openai"  — GPT-4o via OpenAI API (paid)
        "groq"    — Llama 3 via Groq cloud API (free tier)
        "ollama"  — Any model running locally via Ollama (free, offline)

    Args:
        temperature: 0 = deterministic (SQL), 0.7 = creative (answers)

    Returns:
        BaseChatModel: a LangChain chat model. All three return the same
        interface — the rest of the codebase does not need to know which
        provider is active.

    Raises:
        ValueError: if the provider is unknown or required keys are missing.
    """
    provider = os.getenv("LLM_PROVIDER", PROVIDER_OPENAI).strip().lower()

    if provider == PROVIDER_OPENAI:
        return _make_openai(temperature)
    elif provider == PROVIDER_GROQ:
        return _make_groq(temperature)
    elif provider == PROVIDER_OLLAMA:
        return _make_ollama(temperature)
    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER='{provider}'. "
            f"Valid options: openai | groq | ollama"
        )


# ── Provider builders ─────────────────────────────────────────────────────────

def _make_openai(temperature: float) -> BaseChatModel:
    """
    PROVIDER A: OpenAI GPT-4o (paid)

    Requires:
        OPENAI_API_KEY  — from platform.openai.com/api-keys
        OPENAI_MODEL    — default: gpt-4o

    SSL bypass via httpx.Client(verify=False) handles corporate proxy.
    """
    from langchain_openai import ChatOpenAI

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key.strip() in ("sk-...", ""):
        raise ValueError(
            "LLM_PROVIDER=openai but OPENAI_API_KEY is missing or placeholder.\n"
            "Set a real key in .env, or switch to LLM_PROVIDER=groq or ollama."
        )

    model_name = os.getenv("OPENAI_MODEL", "gpt-4o")

    # Corporate proxy SSL bypass
    http_client = httpx.Client(verify=False)

    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        max_tokens=1024,
        openai_api_key=api_key,
        http_client=http_client,
    )


def _make_groq(temperature: float) -> BaseChatModel:
    """
    PROVIDER B: Groq cloud API — free tier, very fast (LPU hardware)

    Requires:
        GROQ_API_KEY  — from console.groq.com (free account)
        GROQ_MODEL    — default: llama-3.3-70b-versatile

    Popular free models on Groq:
        llama-3.3-70b-versatile   — best quality
        llama3-8b-8192            — fastest
        mixtral-8x7b-32768        — long context (32k tokens)
    """
    from langchain_groq import ChatGroq

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key or api_key.strip() in ("gsk_...", ""):
        raise ValueError(
            "LLM_PROVIDER=groq but GROQ_API_KEY is missing or placeholder.\n"
            "Get a free key at https://console.groq.com and add it to .env"
        )

    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Corporate proxy SSL bypass — same pattern as OpenAI provider.
    # ChatGroq accepts an httpx_client parameter directly.
    http_client = httpx.Client(verify=False)

    return ChatGroq(
        model=model_name,
        temperature=temperature,
        max_tokens=1024,
        groq_api_key=api_key,
        http_client=http_client,
    )


def _make_ollama(temperature: float) -> BaseChatModel:
    """
    PROVIDER C: Ollama — fully local, no API key, no internet required

    Requires:
        Ollama installed: https://ollama.com/download
        Model pulled:     ollama pull llama3
        Server running:   ollama serve  (starts automatically on Windows)

    Config (.env):
        OLLAMA_BASE_URL=http://localhost:11434   (default)
        OLLAMA_MODEL=llama3                      (default)

    Other popular models: mistral, phi3, gemma2, codellama
    """
    from langchain_ollama import ChatOllama

    base_url  = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model_name = os.getenv("OLLAMA_MODEL", "llama3")

    return ChatOllama(
        model=model_name,
        base_url=base_url,
        temperature=temperature,
    )

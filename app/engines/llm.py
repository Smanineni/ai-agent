"""
llm.py — LLM (Chat Model) Factory
===================================
WHAT THIS FILE DOES:
    Single place to create and configure the OpenAI GPT-4o chat model.
    Every module that needs to call an LLM imports get_llm() from here.

WHY A CENTRAL FACTORY?
    Same reason as embedder.py — if we ever switch from GPT-4o to
    another model (GPT-4o-mini, Claude, local Ollama), we change
    ONE function here. Nothing else in the codebase changes.

WHAT IS A "CHAT MODEL"?
    A chat model takes a list of messages (system + human + AI turns)
    and returns the next AI message. It's different from a "completion
    model" which just continues a text string.

    LangChain's ChatOpenAI wraps OpenAI's /chat/completions endpoint.

TEMPERATURE:
    Controls how "creative" or "random" the LLM's output is.
    - temperature=0   → deterministic, always picks the most likely token
                        Best for SQL generation — we want consistent, correct SQL
    - temperature=0.7 → more varied and creative
                        Better for free-form text answers
    We use temperature=0 for SQL, slightly higher for answer synthesis.
"""

import os
import httpx
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv(override=True)


def get_llm(temperature: float = 0) -> ChatOpenAI:
    """
    Creates and returns a configured ChatOpenAI instance.

    Args:
        temperature: 0 = deterministic (best for SQL), 0.7 = creative (best for answers)

    Returns:
        ChatOpenAI: LangChain wrapper around OpenAI's chat completions API.

    Raises:
        ValueError: if OPENAI_API_KEY is not set or has no billing credits.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.strip() == "sk-...":
        raise ValueError(
            "OPENAI_API_KEY is not set or is still the placeholder value.\n"
            "Please add your real API key to .env"
        )

    model_name = os.getenv("OPENAI_MODEL", "gpt-4o")

    # Corporate proxy SSL bypass — same pattern as embedder.py
    # httpx.Client(verify=False) tells the HTTP client to skip SSL cert
    # verification, which is needed when a corporate proxy intercepts HTTPS.
    http_client = httpx.Client(verify=False)

    # ChatOpenAI is LangChain's wrapper around the OpenAI chat completions API.
    # Key parameters:
    #   model        : which GPT model to call
    #   temperature  : creativity (0 = deterministic, 1 = very creative)
    #   max_tokens   : safety cap on response length (prevents runaway costs)
    #   http_client  : custom client for SSL bypass
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        max_tokens=1024,
        openai_api_key=api_key,
        http_client=http_client,
    )

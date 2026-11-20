"""
Phase 4 — LLM Engine
Handles all prompt construction and Ollama communication for Centsible AI.
This module is intentionally LLM-agnostic: swap the MODEL constant to change models.
Project: Centsible AI
"""

import json
import os
import requests
from typing import Generator

# Ollama runs locally at this endpoint (started via: brew services start ollama)
OLLAMA_BASE_URL  = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
MODEL            = os.getenv('OLLAMA_MODEL', 'mistral')
MAX_CONTEXT_TOKENS = 4096  # Mistral 7B window


# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT — defines the AI's persona, hard rules, and output format
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are Centsible, an AI-powered personal finance advisor for users in the United States.
Your job is to help users understand their spending habits and build better financial health.

STRICT RULES YOU MUST FOLLOW:
1. Base ALL advice on the user's FINANCIAL PROFILE data and the KNOWLEDGE CONTEXT provided. Never invent numbers.
2. Always cite the specific spending category or dollar amount you are referencing (e.g., "Your dining spend of $1,200...").
3. Keep responses under 220 words unless the question genuinely requires more detail.
4. End EVERY response with a single, specific, actionable step the user can take THIS WEEK.
5. Never recommend specific stocks, individual mutual funds by name, or specific insurance products.
6. Use US Dollars ($) for ALL monetary values. Format as $1,234 or $12,345. Never use ₹ or any other currency.
7. Use US financial terminology: 401(k), Roth IRA, HYSA, emergency fund, FICO score, W-2, etc.
8. If you do NOT have enough data to answer confidently, say so clearly and ask one clarifying question.
9. Be warm, direct, and non-judgmental. Financial stress is real — acknowledge it when appropriate.
10. Never fabricate statistics. If a number is not in the profile or context, say you don't have that data."""


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def build_prompt(
    user_question: str,
    financial_profile: dict,
    rag_context: str,
    conversation_history: list[dict],
) -> list[dict]:
    """
    Constructs the full message list for an Ollama chat API call.

    Args:
        user_question: The user's current message.
        financial_profile: The aggregated financial profile dict.
        rag_context: Retrieved knowledge chunks from ChromaDB.
        conversation_history: List of {'role': 'user'/'assistant', 'content': str}
                              — only the last 3 turns are included to stay within context.

    Returns:
        A messages list ready for the Ollama /api/chat endpoint.
    """
    # Summarise the financial profile for injection (concise version)
    s = financial_profile.get('summary', {})
    top_cats = financial_profile.get('top_spending_categories', [])
    bench    = financial_profile.get('benchmark_50_30_20', {})
    cat_totals = financial_profile.get('expenses_by_category', {})

    top_cat_lines = "\n".join(
        f"  - {cat}: ₹{cat_totals.get(cat, 0):,.0f}/month"
        for cat in top_cats
    )

    profile_block = f"""
=== USER FINANCIAL PROFILE (last {s.get('num_months_of_data', '?')} months) ===
Monthly Take-Home Income (avg): ${s.get('avg_monthly_income', 0):,.0f}
Monthly Expenses (avg):         ${s.get('avg_monthly_expenses', 0):,.0f}
Net Savings (avg/month):        ${bench.get('actual_savings', 0):,.0f}
Savings Rate:                   {s.get('savings_rate_pct', 0):.1f}%
Top Spending Categories:
{top_cat_lines}
50/30/20 Savings Target:        ${bench.get('savings_target_20pct', 0):,.0f}/month
50/30/20 Savings Gap:           ${bench.get('savings_gap', 0):,.0f}/month (negative = ahead)
""".strip()

    context_block = f"""
=== KNOWLEDGE CONTEXT ===
{rag_context}
""".strip()

    # Construct the messages list
    messages = [
        {"role": "system", "content": f"{SYSTEM_PROMPT}\n\n{profile_block}\n\n{context_block}"},
    ]

    # Include last 3 turns of conversation history (6 messages = 3 exchanges)
    recent_history = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
    messages.extend(recent_history)

    # Add current user question
    messages.append({"role": "user", "content": user_question})

    return messages


# ─────────────────────────────────────────────────────────────────────────────
# OLLAMA CLIENT
# ─────────────────────────────────────────────────────────────────────────────

def is_ollama_running() -> bool:
    """Check if the Ollama service is up and the model is available."""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        if r.status_code == 200:
            models = [m['name'] for m in r.json().get('models', [])]
            return any(MODEL in m for m in models)
        return False
    except requests.exceptions.ConnectionError:
        return False


def chat(
    messages: list[dict],
    stream: bool = True,
) -> Generator[str, None, None] | str:
    """
    Sends a chat request to Ollama.
    If stream=True, yields text chunks as they arrive (for real-time UI).
    If stream=False, returns the full response string.
    """
    payload = {
        "model":    MODEL,
        "messages": messages,
        "stream":   stream,
        "options":  {
            "temperature":  0.3,   # Low temp = more factual, less creative
            "top_p":        0.9,
            "num_predict":  400,   # Reduced for faster responses
        }
    }

    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json=payload,
        stream=stream,
        timeout=180,   # Increased to 3 min for complex questions on M4
    )
    response.raise_for_status()

    if stream:
        def _token_generator():
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    token = chunk.get('message', {}).get('content', '')
                    if token:
                        yield token
                    if chunk.get('done'):
                        break
        return _token_generator()
    else:
        data = response.json()
        return data.get('message', {}).get('content', '').strip()


# ─────────────────────────────────────────────────────────────────────────────
# HIGH-LEVEL ADVISOR FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def get_advice(
    user_question: str,
    financial_profile: dict,
    rag_context: str,
    conversation_history: list[dict] = None,
    stream: bool = False,
) -> str | Generator:
    """
    Main entry point. Given a user question, returns grounded financial advice.
    Raises RuntimeError if Ollama is not running or model is not pulled.
    """
    if conversation_history is None:
        conversation_history = []

    if not is_ollama_running():
        raise RuntimeError(
            f"Ollama is not running or model '{MODEL}' is not pulled.\n"
            f"Run: brew services start ollama && ollama pull {MODEL}"
        )

    messages = build_prompt(user_question, financial_profile, rag_context, conversation_history)
    return chat(messages, stream=stream)

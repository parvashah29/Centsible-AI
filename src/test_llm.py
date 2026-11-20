"""
Phase 4 — End-to-End Test: 20 Financial Questions
Runs the full Centsible AI pipeline:
  CSV → parse → classify → aggregate → RAG retrieve → LLM → answer
Project: Centsible AI
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(__file__))

from aggregator   import run_full_pipeline
from rag_pipeline import build_vector_store, retrieve_context
from llm_engine   import get_advice, is_ollama_running

BASE_DIR    = os.path.dirname(os.path.dirname(__file__))
CSV_PATH    = os.path.join(BASE_DIR, 'demo_data.csv')
MODEL_PATH  = os.path.join(BASE_DIR, 'models', 'classifier.pkl')

# 20 diverse test questions covering all major financial advice scenarios
TEST_QUESTIONS = [
    "Where is most of my money going each month?",
    "Am I saving enough money?",
    "How can I cut down my food and dining expenses?",
    "What is the 50/30/20 rule and am I following it?",
    "Should I build an emergency fund or invest first?",
    "How many months of expenses should my emergency fund cover?",
    "I want to save ₹1,00,000 in the next 6 months. Is it realistic?",
    "What is my biggest unnecessary expense right now?",
    "Am I spending too much on entertainment?",
    "How do I start investing if I have never invested before?",
    "What is a SIP and how much should I put into one?",
    "Should I pay off my credit card debt before investing?",
    "How do I build a good credit score from scratch?",
    "What does my month-over-month spending trend look like?",
    "How much should I spend on rent ideally?",
    "I want to buy a car in 2 years. How much should I save monthly?",
    "How do I stop impulse buying online?",
    "What is the debt avalanche method?",
    "How can I grow my savings rate from where it is now?",
    "Give me one concrete financial win I can achieve this week.",
]


def run_test():
    print("=" * 65)
    print("🚀 CENTSIBLE AI — Full Pipeline Test (Phase 4)")
    print("=" * 65)

    # Check Ollama
    if not is_ollama_running():
        print("\n⏳ Ollama not ready yet — model may still be downloading.")
        print("   Run this again once 'ollama pull mistral' completes.\n")
        sys.exit(1)
    print("✅ Ollama is running with Mistral 7B\n")

    # Step 1: Parse + classify + aggregate
    print("📂 Running data pipeline...")
    profile, _ = run_full_pipeline(CSV_PATH, MODEL_PATH)
    print(f"   ✅ Profile built | Savings rate: {profile['summary']['savings_rate_pct']}%\n")

    # Step 2: Load RAG index
    print("🔍 Loading RAG vector store...")
    index = build_vector_store(force_rebuild=False)
    print("   ✅ Vector store loaded\n")

    # Step 3: Run each test question
    conversation_history = []
    results = []

    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"[{i:02d}/20] ❓ {question}")
        rag_context = retrieve_context(question, index, top_k=3)

        try:
            answer = get_advice(
                user_question=question,
                financial_profile=profile,
                rag_context=rag_context,
                conversation_history=conversation_history,
                stream=False,
            )
            # Add to conversation history for multi-turn context
            conversation_history.append({"role": "user", "content": question})
            conversation_history.append({"role": "assistant", "content": answer})

            print(f"        💬 {answer[:180].replace(chr(10), ' ')}...")
            results.append({'question': question, 'answer': answer, 'status': 'ok'})

        except Exception as e:
            print(f"        ❌ Error: {e}")
            results.append({'question': question, 'answer': str(e), 'status': 'error'})

        print()

    # Save results to file for review
    out_path = os.path.join(BASE_DIR, 'data', 'llm_test_results.json')
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)

    ok_count  = sum(1 for r in results if r['status'] == 'ok')
    print("=" * 65)
    print(f"✅ {ok_count}/20 questions answered successfully")
    print(f"💾 Full answers saved → {out_path}")
    print("=" * 65)


if __name__ == '__main__':
    run_test()

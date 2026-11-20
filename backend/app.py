"""
Centsible AI — Flask Backend API
Serves the ML pipeline to the React frontend via REST endpoints.
Project: Centsible AI
"""

import os
import sys
import json
import tempfile
import traceback

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

# Resolve src directory
SRC_DIR  = os.path.join(os.path.dirname(__file__), '..', 'src')
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(SRC_DIR))

from aggregator   import run_full_pipeline
from rag_pipeline import build_vector_store, retrieve_context
from llm_engine   import get_advice, is_ollama_running

import joblib

# ── Flask app ──────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, origins=['http://localhost:5173', 'http://localhost:3000'])

# ── Global state (loaded once at startup) ─────────────────────────────────
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'classifier.pkl')
RAG_INDEX  = None
CLASSIFIER = None

def load_globals():
    global RAG_INDEX, CLASSIFIER
    print("⚙️  Loading classifier...")
    CLASSIFIER = joblib.load(MODEL_PATH)
    print("⚙️  Loading RAG vector store...")
    RAG_INDEX = build_vector_store(force_rebuild=False)
    print("✅ Backend ready.")

# ── Demo profile (from pre-generated data) ────────────────────────────────
DEMO_PROFILE_PATH = os.path.join(BASE_DIR, 'data', 'financial_profile.json')

def load_demo_profile():
    with open(DEMO_PROFILE_PATH) as f:
        return json.load(f)

# ── Conversation history (in-memory, per server lifetime) ─────────────────
conversation_history = []


# ══════════════════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════════════════

@app.route('/api/health', methods=['GET'])
def health():
    """Health check — returns status of Ollama and model."""
    return jsonify({
        'status':         'ok',
        'ollama_ready':   is_ollama_running(),
        'model_loaded':   CLASSIFIER is not None,
        'rag_loaded':     RAG_INDEX is not None,
    })


@app.route('/api/demo', methods=['GET'])
def demo():
    """Returns the pre-generated demo financial profile."""
    global conversation_history
    conversation_history = []  # Reset chat for new session
    try:
        profile = load_demo_profile()
        return jsonify({'success': True, 'profile': profile})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/upload', methods=['POST'])
def upload():
    """
    Accepts a CSV or PDF file upload, runs the full pipeline, returns financial profile.
    """
    global conversation_history
    conversation_history = []

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400

    file = request.files['file']
    ext  = os.path.splitext(file.filename)[1].lower()
    if ext not in ('.csv', '.pdf'):
        return jsonify({'success': False, 'error': 'Only CSV and PDF files are accepted'}), 400

    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            file.save(tmp.name)
            profile, _ = run_full_pipeline(tmp.name, MODEL_PATH)
        os.unlink(tmp.name)
        return jsonify({'success': True, 'profile': profile})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Accepts a user message + financial profile,
    streams the Centsible AI response token-by-token (SSE).
    """
    global conversation_history

    data    = request.get_json()
    message = data.get('message', '').strip()
    profile = data.get('profile', {})

    if not message:
        return jsonify({'error': 'Empty message'}), 400

    if not is_ollama_running():
        return jsonify({'error': 'Ollama is not running. Start it with: brew services start ollama'}), 503

    # RAG retrieval
    rag_ctx = retrieve_context(message, RAG_INDEX, top_k=3)

    def generate():
        full_response = ""
        try:
            stream = get_advice(
                user_question=message,
                financial_profile=profile,
                rag_context=rag_ctx,
                conversation_history=conversation_history,
                stream=True,
            )
            for token in stream:
                full_response += token
                yield f"data: {json.dumps({'token': token})}\n\n"

            # Save turn to history after completion
            conversation_history.append({"role": "user",      "content": message})
            conversation_history.append({"role": "assistant", "content": full_response})
            # Keep last 6 turns
            if len(conversation_history) > 12:
                conversation_history[:] = conversation_history[-12:]

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control':               'no-cache',
            'X-Accel-Buffering':           'no',
            'Access-Control-Allow-Origin': '*',
        }
    )


@app.route('/api/reset', methods=['POST'])
def reset():
    """Resets conversation history."""
    global conversation_history
    conversation_history = []
    return jsonify({'success': True})


# ══════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    load_globals()
    # Bind to 127.0.0.1 only — access via http://localhost:5173 through the Vite proxy
    app.run(host='127.0.0.1', port=8000, debug=False)

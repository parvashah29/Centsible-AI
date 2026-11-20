# Centsible AI — Product Requirements Document (PRD)

## Project Overview
Centsible AI is an AI-powered personal finance advisor built entirely on a free tech stack. It allows users to upload their bank transaction CSVs, automatically categorizes spending, and provides a conversational interface for personalized, grounded financial advice based on proven frameworks.

## Tech Stack (100% Free & Open Source)
- **Language:** Python 3.10+
- **Frontend / UI:** React (custom UI, no Streamlit) + HTML/Vanilla CSS for a bespoke, advanced interface
- **Backend API:** Flask or Node.js to serve the machine learning and RAG pipelines
- **Local LLM (100% Lifetime Free):** Ollama + Mistral 7B. (Perfectly optimized for your **Macbook Air M4** using Apple's native Metal framework). We are explicitly avoiding paid/trial APIs like Gemini.
- **RAG Framework:** LlamaIndex (Handles chunking, embedding, retrieval, prompting)
- **Vector Database:** ChromaDB (Local vector store)
- **Embeddings:** `sentence-transformers` (all-MiniLM-L6-v2 runs locally)
- **ML Classifier:** `scikit-learn` (Logistic Regression for transaction categorization)
- **Data Processing:** `pandas` & `numpy`
- **Visualizations:** Plotly Express
- **Synthetic Data Generation:** `Faker` (for training data)
- **String Matching:** `RapidFuzz` (for merchant matching)
- **Testing:** `pytest`
- **Version Control:** Git & GitHub
- **Deployment:** HuggingFace Spaces (Free CPU tier)

## Phase-by-Phase Development Plan

### Phase 1: Foundation (Weeks 1-2) - CURRENT PHASE
**Goal:** Build a bulletproof CSV parser.
- Set up Python environment and Git repository.
- Write a defensive parser (`parser.py`) to auto-detect and clean columns (Date, Description, Amount).
- Handle multiple bank CSV formats, split/combined debit/credit columns, and date formats.
- Build a Week 1 MVP script (`mvp.py`) with hardcoded keyword rules to prove the concept.
- Write unit tests using `pytest` to catch regressions.

### Phase 2: Transaction Classification & Analytics (Weeks 3-5)
**Goal:** Replace keyword rules with an ML model.
- Generate 10,000+ synthetic transactions across ~10 categories using `Faker`.
- Train a `LogisticRegression` model with TF-IDF features (Target F1 > 0.85).
- Build the spending aggregator to compute totals, savings rates, and top merchants.
- Generate a structured Financial Profile JSON for each user.

### Phase 3: RAG Knowledge Base (Weeks 6-7)
**Goal:** Curate financial wisdom for the AI.
- Collect 20-30 free, high-quality personal finance documents.
- Chunk, embed, and store documents in `ChromaDB` using `LlamaIndex`.
- Implement a robust retrieval function.

### Phase 4: LLM Integration (Weeks 8-10)
**Goal:** Connect the RAG pipeline to the LLM.
- Set up `Ollama` locally (or `Gemini API`).
- Design a strict prompt template that forces the AI to use both the user's JSON and the retrieved RAG context.
- Test against 20 standard financial questions to evaluate hallucination rates and accuracy.

### Phase 5: React Web App & Flask Backend (Weeks 11-12)
**Goal:** Build a beautiful, responsive, bespoke web dashboard.
- Create a modern **React** frontend using HTML/CSS for premium aesthetics instead of standard templates.
- Implement a **Flask** backend API to connect our Python ML pipeline with the React UI.
- Implement secure CSV upload, interactive charts, and the AI chat interface.
- Embed a "Demo Mode" button that loads synthetic data instantly.

### Phase 6: Deployment & Polish (Weeks 13-16)
**Goal:** Launch the product publicly.
- Deploy the React frontend and Python backend using lifetime free tiers (e.g., Vercel for frontend, Render/Railway free limits for backend, or heavily local-first approaches).
- Ensure the app provides high value offline using local M4 processing for the end-user.
- Finalize documentation (`README.md`) and record demo video.

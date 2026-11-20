# 💰 Centsible AI — AI-Powered Personal Finance Advisor

> **Your private, offline AI financial advisor.** Upload your bank statement, get instant spending insights, and chat with an AI that knows your actual numbers — all running 100% locally on your device. Free forever.

---

## 🎯 What Does Centsible AI Do?

Centsible AI solves three problems that existing personal finance tools don't:

| Problem | How Centsible AI Solves It |
|---|---|
| Finance apps show charts but don't tell you *what to do* | An AI advisor gives you specific, actionable advice |
| Generic AI chatbots give advice not grounded in your data | Your actual transactions are injected into every AI response |
| Financial advisors cost ₹5,000–₹50,000/hour | Centsible AI is completely free, forever |

---

## 🏗️ System Architecture

The system is built in **three layers**:

```
USER UPLOADS CSV
      │
      ▼
┌─────────────┐    ┌──────────────────┐    ┌───────────────────┐
│  CSV Parser │───▶│  ML Classifier   │───▶│ Spending Aggreg.  │
│  (pandas)   │    │ (scikit-learn)   │    │ (pandas/numpy)    │
└─────────────┘    └──────────────────┘    └────────┬──────────┘
                                                    │
                                          Financial Profile JSON
                                                    │
               USER QUESTION ──────────────▶ Prompt Builder
                                                    │
              ┌─────────────┐                       │
              │  RAG Engine │ ◀─────────────────────┘
              │ (LlamaIndex │     (retrieves relevant
              │ + ChromaDB) │      finance knowledge)
              └──────┬──────┘
                     │ top-3 relevant chunks
                     ▼
              ┌──────────────┐
              │  Mistral 7B  │  ← runs locally via Ollama
              │  (Ollama)    │     zero API cost, zero data sharing
              └──────┬───────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  React Web Dashboard  │
         │  Flask REST API       │
         └───────────────────────┘
```

---

## 🛠️ Full Tech Stack (100% Free & Open Source)

| Layer | Tool | Why |
|---|---|---|
| **Frontend** | React + Vite | Premium custom UI (not Streamlit) |
| **Styling** | Vanilla CSS Modules | Fully custom dark theme |
| **Animations** | Framer Motion | Smooth micro-animations |
| **Charts** | Recharts | Interactive donut & bar charts |
| **Backend API** | Flask + Flask-CORS | Lightweight Python REST server |
| **Local LLM** | Ollama + Mistral 7B | Runs on your M4 Mac via Apple Metal — free forever |
| **RAG Framework** | LlamaIndex | Chunking, embedding, retrieval pipeline |
| **Vector Database** | ChromaDB | Local vector store, no cloud needed |
| **Embeddings** | sentence-transformers (MiniLM-L6-v2) | Local embeddings, no API calls |
| **ML Classifier** | scikit-learn (TF-IDF + LogisticRegression) | Categorises transactions in milliseconds |
| **Data Processing** | pandas + numpy | CSV parsing and financial analytics |
| **Visualisations** | Recharts (in React) | Interactive charts in the browser |
| **Synthetic Data** | Faker | Generates training data and demo CSV |
| **Version Control** | Git + GitHub | Full history maintained |
| **Testing** | pytest | Parser and classifier regression tests |

---

## 📁 Project Structure

```
centsible-ai/
│
├── 📄 PRD.md                        # Product Requirements Document
├── 📄 README.md                     # This file
├── 📄 requirements.txt              # Python dependencies
├── 📄 .gitignore
│
├── 📁 src/                          # Python ML + AI backend logic
│   ├── parser.py                    # Defensive CSV parser (multi-bank)
│   ├── classifier.py                # TF-IDF + LogisticRegression classifier
│   ├── aggregator.py                # Spending aggregator + financial profile builder
│   ├── rag_pipeline.py              # ChromaDB vector store + LlamaIndex retrieval
│   ├── llm_engine.py                # Ollama/Mistral prompt builder + streaming client
│   ├── generate_faker_csv.py        # Demo CSV generator
│   ├── generate_training_data.py    # 10,000 synthetic training transactions
│   └── test_llm.py                  # 20-question end-to-end LLM test suite
│
├── 📁 backend/
│   └── app.py                       # Flask REST API (serves all ML/AI endpoints)
│
├── 📁 frontend/                     # React + Vite web application
│   ├── index.html
│   ├── vite.config.js               # Proxy /api → Flask :8000
│   └── src/
│       ├── main.jsx
│       ├── App.jsx                  # Root: view state management
│       ├── index.css                # Global design system + tokens
│       └── components/
│           ├── Navbar.jsx / .css
│           ├── LandingPage.jsx / .css   # Upload + Demo mode
│           ├── Dashboard.jsx / .css     # Charts + metrics
│           └── ChatAdvisor.jsx / .css   # Streaming AI chat
│
├── 📁 knowledge_base/               # Curated personal finance documents (RAG source)
│   ├── 01_50_30_20_rule.txt
│   ├── 02_emergency_fund.txt
│   ├── 03_debt_strategies.txt
│   ├── 04_spending_reduction.txt
│   ├── 05_investing_basics.txt
│   ├── 06_savings_goals.txt
│   ├── 07_freelancer_finance.txt
│   └── 08_credit_cards.txt
│
├── 📁 data/                         # Generated data files
│   ├── training_data.csv            # 10k synthetic training transactions
│   ├── financial_profile.json       # Latest computed profile (updated on upload)
│   └── llm_test_results.json        # LLM evaluation results
│
├── 📁 models/
│   └── classifier.pkl               # Trained scikit-learn ML model
│
├── 📁 chroma_store/                 # Persisted ChromaDB vector embeddings
└── 📄 demo_data.csv                 # Synthetic demo bank statement
```

---

## ⚙️ Setup Guide — Step by Step

### Prerequisites

Before starting, make sure you have the following installed:

- **macOS** (Apple Silicon M1/M2/M3/M4 recommended)
- **Python 3.10+** — check with `python3 --version`
- **Node.js 18+** — check with `node --version`
- **Homebrew** — install from [brew.sh](https://brew.sh) if not present

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/centsible-ai.git
cd centsible-ai
```

---

### Step 2 — Install Ollama (Local LLM Engine)

```bash
brew install ollama
```

Start the Ollama background service:

```bash
brew services start ollama
```

Pull the Mistral 7B model (~4.4 GB, one-time download):

```bash
ollama pull mistral
```

> ✅ This runs entirely offline on your Mac using Apple's Metal GPU framework. No API key, no cost.

---

### Step 3 — Set Up the Python Environment

```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install all Python dependencies
pip install -r requirements.txt
```

---

### Step 4 — Train the ML Classifier

> Skip this if `models/classifier.pkl` already exists in the repo.

```bash
# Generate 10,000 synthetic training transactions
python src/generate_training_data.py

# Train and save the classifier
python src/classifier.py
```

Expected output:
```
📊 Overall Accuracy: 100.00%
✅ Accuracy target met (>85%)!
💾 Model saved → models/classifier.pkl
```

---

### Step 5 — Build the RAG Knowledge Base

> Skip this if `chroma_store/` already exists in the repo.

```bash
python src/rag_pipeline.py
```

Expected output:
```
🔨 Building vector store from: knowledge_base/
   Loaded 8 documents. Embedding now...
✅ Vector store built and saved → chroma_store/
```

---

### Step 6 — Generate Demo Data

> Skip this if `demo_data.csv` already exists.

```bash
python src/generate_faker_csv.py
```

---

### Step 7 — Start the Flask Backend

Open a **new terminal tab** and run:

```bash
source venv/bin/activate
python backend/app.py
```

Expected output:
```
⚙️  Loading classifier...
⚙️  Loading RAG vector store...
✅ Backend ready.
 * Serving Flask app 'app'
 * Running on http://0.0.0.0:8000
```

> Keep this terminal open. The backend must stay running.

---

### Step 8 — Start the React Frontend

Open **another new terminal tab** and run:

```bash
cd frontend
npm install       # only needed the first time
npm run dev
```

Expected output:
```
  VITE v8.0.3  ready in 1824 ms
  ➜  Local:   http://localhost:5173/
```

---

### Step 9 — Open the App 🎉

Open your browser and go to:

```
http://localhost:5173
```

You should see the Centsible AI landing page. Click **"Try Demo Mode"** to instantly explore the app with synthetic data, or upload your own bank CSV file.

---

## 🔌 API Reference

The Flask backend exposes these endpoints:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Check Ollama + model status |
| `GET` | `/api/demo` | Load pre-generated demo financial profile |
| `POST` | `/api/upload` | Upload a bank CSV → returns financial profile JSON |
| `POST` | `/api/chat` | Send a message → streams AI response via SSE |
| `POST` | `/api/reset` | Clear conversation history |

---

## 🏦 Supported Bank CSV Formats

The parser auto-detects column formats for:

- HDFC Bank (Withdrawal/Deposit split)
- SBI / ICICI / Axis Bank
- Chase, Barclays, Revolut, Monzo
- Any CSV with `Date`, `Description`, `Amount` columns

---

## 🔒 Privacy

- **Your bank data never leaves your device.** The CSV is processed in-memory and discarded after analysis.
- **The AI runs 100% locally** via Ollama. No requests are sent to any external API.
- **No telemetry, no tracking, no accounts required.**

---

## ⚠️ Disclaimer

Centsible AI is an **educational tool only**. It is not regulated financial advice. Always consult a certified financial advisor before making major financial decisions.

---

## 🗺️ Roadmap

- [x] Phase 1 — CSV Parser (multi-bank support)
- [x] Phase 2 — ML Transaction Classifier + Spending Aggregator
- [x] Phase 3 — RAG Knowledge Base (ChromaDB + LlamaIndex)
- [x] Phase 4 — LLM Integration (Mistral 7B via Ollama)
- [x] Phase 5 — React + Flask Web App
- [ ] Phase 6 — Deployment (Vercel + Render free tier)

---

*Built with ❤️ by Parva Shah — Centsible AI*

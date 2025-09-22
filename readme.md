# 💰 AI Cost & Insights Copilot: FinOps Analytics Engine

## Overview & Project Goal

This project implements an **AI-native analytics application** designed to empower a FinOps analyst. The core tool ingests synthetic cloud usage data, computes essential Key Performance Indicators (KPIs), and provides **actionable, data-grounded recommendations** through a low-latency Retrieval-Augmented Generation (RAG) chatbot.

The solution demonstrates a complete, end-to-end stack, meeting high standards for architecture, testing, and AI integration.

***

## 📖 Table of Contents
1. [Motivation & Features](#motivation--features)
2. [Architecture & Decisions](#architecture--design-decisions)
3. [Installation & Setup](#installation--setup)
4. [Usage & Verification](#usage--verification)
5. [Project Structure](#project-structure)
6. [Testing & Evaluation](#testing--evaluation)
7. [Future Work](#future-work)

***

## 1. Motivation & Features

### Motivation
As cloud spending continues to grow, FinOps analysts need automated tools to quickly answer complex questions (e.g., "Why did my Azure spend jump 22% in May?") and generate specific, actionable mitigation steps[cite: 7]. This project solves the problem of integrating structured cloud data with conversational AI to surface these insights instantly[cite: 2].

### Implemented Features
| Feature Category | Deliverables |
| :--- | :--- |
| **ETL & Data** | Ingestion of 3–6 months of synthetic cloud spend data[cite: 64]. Quality checks implemented for nulls and negative costs[cite: 21]. |
| **KPI & Analytics** | Calculates monthly spend, trend vs. last month, savings opportunities, and top 5 cost drivers[cite: 20]. |
| **AI/RAG** | Fast RAG over custom data and `finops_tips.md` using Groq/LangChain/ChromaDB[cite: 23, 24]. |
| **Recommendations** | Implements the **Sudden unit-cost increase** heuristic [cite: 31] to generate 1–3 specific next steps[cite: 8]. |
| **DevOps** | Fully containerized with `Dockerfile` and `docker-compose.yml`, ensuring runs locally with one command[cite: 40, 62]. |
| **Code Quality** | **4 passing unit tests** for ETL, KPI, and API validation[cite: 42]. |

***

## 2. Architecture & Design Decisions

The application is built on a modular microservices-inspired architecture.

| Component | Technology | Rationale and Key Decisions (Trade-Offs) |
| :--- | :--- | :--- |
| **Data Layer** | **SQLite** (File-based) | Chosen for **simplicity and rapid deployment** over PostgreSQL, fitting the local demo constraint. |
| **Backend API** | **FastAPI** (Python) | Provides high-performance, asynchronous endpoints (`/api/kpi`, `/api/ask`). |
| **RAG/LLM** | **Groq API** + **LangChain** | **CRITICAL TRADE-OFF:** Switched from local Ollama for **sub-second inference latency**, prioritizing performance for the demo. |

***

## 3. Installation & Setup

### Prerequisites
1.  **Docker Desktop:** Must be installed and running on your system.
2.  **Groq API Key:** Obtain a key from the [Groq Console](https://console.groq.com/keys).

### Steps
1.  **Clone the repository:**
    ```bash
    git clone [YOUR REPO LINK HERE]
    cd finops-copilot
    ```
2.  **Configure Secrets (`.env.example` $\to$ `.env`)**:
    ```bash
    cp .env.example .env
    # Edit the .env file and paste your GROQ_API_KEY
    ```
3.  **Build and Run (One Command)**: This command rebuilds the image, runs the ETL (data ingestion), starts the FastAPI API, and launches the Streamlit UI.
    ```bash
    docker compose up --build
    ```

### Configuration & Customization
| Variable | File | Description |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | `.env` | Required for RAG inference (must be set). |
| `DATABASE_URL` | `.env` | Currently `sqlite:///./sql_app.db` for the local file-based setup. |
| `OLLAMA_BASE_URL` | `.env` | Left blank, as Groq API is used for LLM inference. |
| `NUM_RECORDS`, `MONTHS_HISTORY` | `app/ingestion.py` | Customize the size and temporal window of the synthetic dataset. |

***

## 4. Usage & Verification

### Access
* **KPI Dashboard UI (Primary):** `http://localhost:8501`
* **FastAPI Docs (Swagger UI):** `http://localhost:8000/docs`

### Demo Examples (RAG Q&A)
Use these queries to demonstrate RAG functionality and grounding:

| Query | Expected Behavior |
| :--- | :--- |
| **"What was total spend in May? Break it down by service."** | Retrieves synthetic billing data and generates a detailed breakdown, showing data grounding[cite: 65]. |
| **"Why did spend increase vs April? Show top 5 contributors."** | Checks the calculated `monthly_trend_percentage` and uses the top 5 cost drivers to explain the change[cite: 66]. |
| **"What are some recommendations for cost optimization?"** | Retrieves text chunks from `data/finops_tips.md` and formats the answer with actionable steps. |
| **"I see my EC2 costs have spiked. What should I do?"** | Triggers the recommendation heuristic and provides specific next steps (1–3 actions)[cite: 8]. |

### Running Unit Tests (Code Quality Check)
After stopping your Docker container (`Ctrl+C`), you can verify the unit tests:

```bash
# Ensure pytest is installed locally (pip install pytest)
pytest tests/

### Project Structure

```bash
finops-copilot/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── kpi.py            # KPI computation logic (Cost, Trends)
│   │       ├── chat.py           # RAG endpoint and response formatter
│   │       └── health.py         # Health check for Docker
│   ├── database.py             # SQLAlchemy/SQLModel engine and session setup
│   ├── models.py               # Defines DB schemas and API response schemas
│   ├── ingestion.py            # ETL: Generates data, performs quality checks, loads DB
│   └── rag_core.py             # RAG setup: Embeddings, ChromaDB, Groq LLM chain
├── data/
│   ├── finops_tips.md          # Reference document for RAG knowledge
├── tests/
│   ├── rag_test_set.json       # Test set for RAG evaluation
│   └── test_api_logic.py       # 4 passing unit tests (API, KPI, ETL)
├── .env.example                # Configuration template
├── Dockerfile                  # Instructions for building the service image
├── docker-compose.yml          # Orchestrates ETL, API, and Streamlit
└── requirements.txt            # Python dependencies
```

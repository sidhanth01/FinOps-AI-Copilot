# 💰 AI Cost & Insights Copilot: FinOps Analytics Engine

## Overview & Project Goal

This project implements an **AI-native analytics application** designed to empower a FinOps analyst. [cite_start]The core tool ingests synthetic cloud usage data, computes essential Key Performance Indicators (KPIs) , and provides **actionable, data-grounded recommendations** through a low-latency Retrieval-Augmented Generation (RAG) chatbot.

The solution demonstrates a complete, end-to-end stack, meeting high standards for architecture, testing, and AI integration.

***


https://github.com/user-attachments/assets/581a379a-81d7-45f1-9639-6072abe0abb7


## 📖 Table of Contents
1. Motivation & Features
2. Architecture & Design Decisions
3. Installation & Setup
4. Usage & Verification
5. Project Structure
6. Testing & Evaluation
7. Contact Support

***

## 1. Motivation & Features

### Motivation
As cloud spending continues to grow, FinOps analysts need automated tools to quickly answer complex questions (e.g., "Why did my Azure spend jump 22% in May?") and generate specific, actionable mitigation steps[cite: 7]. This project solves the problem of integrating structured cloud data with conversational AI to surface these insights instantly.

### Implemented Features
| Feature Category | Deliverables |
| :--- | :--- |
| **ETL & Data** | Ingestion of 3–6 months of synthetic cloud spend data. Quality checks implemented for nulls and negative costs. |
| **KPI & Analytics** | Calculates monthly spend, trend vs. last month, savings opportunities, and top 5 cost drivers. |
| **AI/RAG** | RAG over custom data and `finops_tips.md` using Ollama (Mistral) / LangChain / ChromaDB. |
| **Recommendations** | Implements the **Sudden unit-cost increase** heuristic  to generate 1–3 specific next steps. |
| **DevOps** | Fully containerized with `Dockerfile` and `docker-compose.yml`, runs locally with one command. |
| **Code Quality** | **4 passing unit tests** for ETL, KPI, and API validation. |

***

## 2. Architecture & Design Decisions

The application is built on a modular microservices-inspired architecture.

| Component | Technology | Rationale and Key Decisions (Trade-Offs) |
| :--- | :--- | :--- |
| **Data Layer** | **SQLite** (File-based) | Chosen for **simplicity and rapid deployment** over PostgreSQL, fitting the local demo constraint. |
| **Backend API** | **FastAPI** (Python) | Provides high-performance, asynchronous endpoints (`/api/kpi`, `/api/ask`). |
| **RAG/LLM** | **Ollama (Mistral)** + **LangChain** | Uses a local open-source model via Ollama  for fully private, contained inference. |
| **Vector Store** | **ChromaDB** | Simple, file-based vector store  integrated via LangChain to index both data and knowledge. |

***

## 3. Installation & Setup

### Prerequisites
1.  **Docker Desktop:** Must be installed and running on your system.
2.  **Ollama:** Must be installed on the host machine, and the required model (`mistral`) must be pulled locally.
    ```bash
    ollama pull mistral
    ```

### Steps
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/sidhanth01/FinOps-AI-Copilot
    cd FinOps-AI-Copilot
    ```
2.  **Configure Secrets (`.env.example` $\to$ `.env`)**:
    ```bash
    cp .env.example .env
    # NOTE: OLLAMA_BASE_URL must be set to [http://host.docker.internal:11434](http://host.docker.internal:11434) 
    # in the .env file to allow the container to reach the host service.
    ```
3.  **Build and Run (One Command)**: This command rebuilds the image, runs the ETL (data ingestion), starts the FastAPI API, and launches the Streamlit UI.
    ```bash
    docker compose up --build
    ```

### Configuration & Customization
| Variable | File | Description |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | `.env` | Placeholder (not used, but good for future work). |
| `OLLAMA_BASE_URL` | `.env` | Must be set to `http://host.docker.internal:11434` for container-to-host communication. |
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
| **"What was total spend in May? Break it down by service."** | Retrieves synthetic billing data and generates a detailed breakdown, showing data grounding. |
| **"Why did spend increase vs April? Show top 5 contributors."** | Checks the calculated trend and uses the top 5 cost drivers to explain the change. |
| **"What are some recommendations for cost optimization?"** | Retrieves text chunks from `data/finops_tips.md` and formats the answer with actionable steps. |
| **"I see my EC2 costs have spiked. What should I do?"** | Triggers the recommendation heuristic and provides specific next steps (1–3 actions). |

### Running Unit Tests (Code Quality Check)

After stopping your Docker container (`Ctrl+C`), you can verify the unit tests:

```bash
# Ensure pytest is installed locally: pip install pytest
pytest tests/

test_health_check -	API integrity
test_kpi_endpoint_response - End-to-end API → Data flow (checks for deliberate cost spike)
test_manual_kpi_calculation - Core KPI metric calculation logic
test_data_quality_check	- ETL quality checks (nulls, negative costs)
```

### Project Structure

```bash
finops-copilot/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── chat.py           # RAG endpoint and response formatter
│   │       ├── health.py         # Health check for Docker
│   │       └── kpi.py            # KPI computation logic (Cost, Trends)
│   ├── database.py             # SQLAlchemy/SQLModel engine and session setup
│   ├── ingestion.py            # ETL: Generates data, performs quality checks, loads DB
│   ├── main.py                 # FastAPI application entry point
│   └── models.py               # Defines DB schemas and API response schemas
├── data/
│   ├── finops_tips.md          # Reference document for RAG knowledge
│   └── synthetic_data.csv      # Sample data (created by ingestion script)
├── tests/
│   ├── rag_test_set.json       # Test set for RAG evaluation
│   └── test_api_logic.py       # 4 passing unit tests (API, KPI, ETL)
├── .env.example                # Configuration template
├── .gitignore                  # Lists ignored files (e.g., .env, chroma_db/)
├── Dockerfile                  # Instructions for building the service image
├── docker-compose.yml          # Orchestrates ETL, API, and Streamlit
└── requirements.txt            # Python dependencies
```
### Contact & Support

For any questions, issues, or feedback regarding the architecture or implementation of this project, please use the following methods:

1.  **GitHub Issues:** The preferred method is to open a **new issue** on this repository for any bugs, suggestions, or technical questions.
2.  **Contact Developer:** You can reach the developer directly at:
    * **GitHub Profile:** `https://github.com/sidhanth01`
    * **LinkedIn Profile:** `https://shorturl.at/3ZiCW`

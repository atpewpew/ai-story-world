## 📘 MASTER PROJECT CONTEXT & INSTRUCTION PROMPT

### Project: AI-Driven Interactive Story World

*(Full Context + Implementation Roadmap + Reference Instructions)*

---

### 1. PROJECT OVERVIEW

This project aims to build an **AI-driven interactive story generation system** — an *agentic AI world* where the user interacts through branching text-based narratives that evolve consistently over time.
Each story session maintains **long-term world-state consistency** (characters, items, relationships, locations) through persistent memory and structured knowledge representation.

The system integrates **LLMs (Gemini)** with structured memory layers, a knowledge graph, and semantic retrieval mechanisms to maintain contextual coherence, continuity, and replayability.

The project is implemented in **Python (FastAPI backend)** with an optional **React/Next.js frontend** for the web UI.
Development is optimized for **local laptop use** and **free-tier deployability** (e.g., Render, Railway, Hugging Face Spaces).

---

### 2. CURRENT STATUS

* ✅ CLI prototype built (verifies all major services).
* ✅ FastAPI backend working with endpoints:

  * `/create_session`
  * `/take_action`
  * `/get_session`
* ✅ Session memory (`story_memory.json`) persists across interactions.
* ✅ Local **Gemini integration** via `google-genai` Python SDK (`v1.41.0`).
* ✅ Basic heuristic fact extraction implemented.
* ✅ `world` field in session object stores characters, items, and locations.

Next goal: evolve into a **full production-grade web application** with modular backend, hybrid memory, graph-based world modeling, frontend UI, safety systems, and deployable containers.
### Quickstart

Run locally:

```bash
uvicorn ai_story.main:app --reload --port 8000
```

Or with script:

```bash
bash scripts/run_local.sh
```

Docker:

```bash
docker build -t ai-story .
docker run -p 8000:8000 ai-story
```

Docker Compose:

```bash
docker-compose up --build
```

Metrics available at `/metrics`. Health at `/health`.


---

### 3. ARCHITECTURE OVERVIEW (Conceptual)

**Core components:**

```
User → Web UI (React/Next) → FastAPI Backend
     → Memory Layer (Session JSON + Vector Store + Graph DB)
     → Gemini Model Layer (via google-genai SDK)
     → Fact Extraction + World Model Updater
     → Persistent Storage (local files or cloud DB)
```

Key layers:

* **Frontend:** Interactive story interface (stateful, branching, replayable).
* **Backend:** Orchestrates model calls, world updates, and memory retrieval.
* **Memory System:** Hybrid model (short-term + long-term + structured).
* **Knowledge Graph:** Represents entities and relationships (characters, items, locations).
* **LLM Layer:** Gemini model for text generation and structured reasoning.
* **Deployment Layer:** Containerized for local and free-tier cloud hosting.
* **Safety Layer:** Filters, rate-limits, content moderation, logging.

---

### 4. FEATURE PRIORITIES (1–10)

| Priority | Feature                                                  | Value  | Complexity | Goal                   |
| -------- | -------------------------------------------------------- | ------ | ---------- | ---------------------- |
| 1        | Hybrid Memory System (session buffer + semantic + graph) | High   | Medium     | World continuity       |
| 2        | Fact Extraction Pipeline                                 | High   | Medium     | Structured updates     |
| 3        | Prompt Orchestration + RAG                               | High   | High       | Context-grounded story |
| 4        | Web Frontend (React/Next.js)                             | High   | Medium     | User experience        |
| 5        | Deployment (Docker + Render/Railway)                     | High   | Medium     | Production readiness   |
| 6        | Safety, Moderation & Privacy Layer                       | High   | Medium     | Trust & compliance     |
| 7        | Monitoring & Logging                                     | Medium | Medium     | Observability          |
| 8        | Session Restoration & Branching                          | Medium | Medium     | Replayability          |
| 9        | API Key Rotation & Cost Control                          | Medium | Low        | Reliability            |
| 10       | CI/CD & Automated Testing                                | Medium | High       | Scalability            |

---

### 5. PHASED IMPLEMENTATION PLAN

#### **Phase 1: Core Backend & Story Engine (Completed / Refinement Stage)**

* Finalize FastAPI structure with modular routers.
* Extend `story_memory.json` → structured schema (characters, items, relationships).
* Add persistence abstraction for local and future DB integration.
* Implement model interface layer (`gemini_client.py`) for text + structured calls.
* Unit tests for endpoints and story generation consistency.

#### **Phase 2: Hybrid Memory Architecture**

* Add **short-term session memory** (recent dialogue buffer).
* Add **semantic memory** using vector store (ChromaDB preferred for local, Qdrant optional).
* Add **knowledge graph memory** (Neo4j or JSON-based graph structure).
* Define schema for entities:

  * `Character {name, role, traits, location, items}`
  * `Item {name, type, owner}`
  * `Location {name, description, occupants}`
* Enable Cypher-like queries or equivalent for reasoning.
* Add embedding generation (local `sentence-transformers` or API-based fallback).
* Create retrieval pipeline combining semantic + structured queries.

#### **Phase 3: Fact Extraction & World Updates**

* Two-path design:

  * **A. LLM-based structured output** via Gemini function calling.
  * **B. Lightweight NLP/NER + rule-based fallback.**
* Extract facts after each story segment.
* Update knowledge graph and session memory automatically.
* Define JSON schema for extracted facts:

  ```json
  { "type": "relation", "subject": "Alice", "predicate": "owns", "object": "key", "certainty": 0.9 }
  ```
* Validate correctness and non-duplication.

#### **Phase 4: Prompt Engineering & Retrieval-Augmented Generation (RAG)**

* Create composable prompt structure:

  * System message → world summary → retrieved facts → recent history → user input.
* Implement RAG retrieval flow:

  * Select top-k relevant facts from memory before every generation.
* Compare story quality before/after RAG.
* Add prompt versioning for experimentation.

#### **Phase 5: Web Frontend (React/Next.js)**

* Build story viewer + input UI.
* Add visual state for world summary (characters, items, map view).
* Implement full session restoration (reload previous story and state).
* Add branching story save slots.
* Integrate REST endpoints for all core functions.
* Add basic WebSocket for real-time updates (future multi-user support).

#### **Phase 6: Deployment & Operations**

* Add Dockerfile and docker-compose (FastAPI + Chroma + Neo4j).
* Local run with `docker-compose up`.
* Deploy to:

  * (A) Local (laptop)
  * (B) Render/Railway (free-tier)
* Use `.env` files for configuration and secrets.
* Set up health checks and API rate limits.
* Add API key rotation system (primary + fallback).

#### **Phase 7: Safety, Privacy & Monitoring**

* Input sanitization (regex or filtering layer).
* Toxicity and unsafe content detection (OpenAI moderation API or Detoxify local).
* Rate-limiting per user/session.
* Logging of key events (generation times, cost, errors).
* Add monitoring with:

  * **Sentry** (errors)
  * **Prometheus + Grafana** (performance)
  * **Structured logs** for actions and responses.
* Future: user consent screen, retention policy configuration.

#### **Phase 8: Testing, CI/CD & Regression**

* Add regression tests with sample story cases.
* Verify memory consistency after multiple turns.
* Create test suite for fact extraction accuracy.
* GitHub Actions pipeline for build + tests + container validation.
* Continuous deployment to Render/Railway.

#### **Phase 9: Documentation, Portfolio & Demo**

* README: clear usage instructions + screenshots.
* Add project badges and roadmap.
* Record demo walkthrough video.
* Portfolio bullet points:

  * “Designed and implemented a hybrid-memory, LLM-driven interactive storytelling engine maintaining long-term world consistency using FastAPI and Gemini.”
  * “Integrated semantic memory, graph reasoning, and RAG-based contextual prompts for dynamic branching narratives.”
  * “Deployed using Docker and free-tier cloud with full monitoring, safety, and reproducible development workflow.”

#### **Phase 10: 6-Week Milestone Plan**

| Week | Goal                        | Deliverables                      |
| ---- | --------------------------- | --------------------------------- |
| 1    | Memory layer implementation | Vector store + schema finalized   |
| 2    | Fact extraction engine      | Working structured facts pipeline |
| 3    | Prompt + RAG integration    | Enhanced story generation         |
| 4    | Web frontend (MVP)          | UI + session restoration          |
| 5    | Dockerization + deployment  | Working free-tier demo            |
| 6    | Safety + monitoring + docs  | Polished portfolio-ready version  |

---

### 6. DESIGN GUIDELINES & DECISIONS

* **Backend Language:** Python (FastAPI)
* **Frontend:** React or Next.js
* **LLM Interface:** `google-genai` SDK (Gemini, v1.41.0)
* **Memory Stack:**

  * Session: JSON buffer
  * Semantic: ChromaDB (local) / Qdrant (cloud)
  * Graph: Neo4j (local Docker or JSONGraph fallback)
* **Embeddings:** `sentence-transformers` (`all-MiniLM-L6-v2`)
* **Prompting Strategy:** Modular template + RAG
* **Deployment Tools:** Docker + docker-compose
* **Cloud Hosting:** Render, Railway, Hugging Face Spaces (free-tier)
* **Monitoring:** Sentry + Prometheus + Grafana
* **Safety Tools:** Detoxify / Perspective API / Regex filter
* **Authentication:** Simple session token, extendable to JWT
* **Storage:** Local JSON for dev, future Postgres/Neo4j hybrid
* **Version Control:** GitHub with Actions for CI/CD

---

### 7. FUTURE EXTENSIONS (Post-MVP)

* Multi-user shared story worlds (WebSockets + state sync)
* Visual map + character UI
* Fine-tuned domain LLM (fiction-style)
* Ontology-driven knowledge reasoning
* Voice-based interaction (Speech-to-Text + TTS)
* Persistent user profiles with cross-session memory

---

### 8. APPENDICES (Reference Docs)

* [FastAPI Docs](https://fastapi.tiangolo.com/)
* [google-genai SDK Docs](https://ai.google.dev/docs)
* [Chroma Docs](https://docs.trychroma.com/)
* [Neo4j Docs](https://neo4j.com/docs/)
* [LangChain Docs](https://python.langchain.com/)
* [sentence-transformers](https://www.sbert.net/)
* [Render Deployment Guide](https://render.com/docs)
* [Railway Deployment Guide](https://docs.railway.app/)
* [Docker Docs](https://docs.docker.com/)
* [Sentry](https://docs.sentry.io/)

---

### 9. HOW FUTURE CHATGPT SESSIONS SHOULD USE THIS CONTEXT

Any future session should:

* Treat this as the **single source of truth** for architecture and priorities.
* Follow the phase order (don’t skip ahead unless instructed).
* When adding code or features, refer back to this plan for compatibility.
* Maintain reproducibility (local-first, laptop-friendly).
* Use Gemini SDK (`google-genai`, v1.41.0) for all model-related work.
* Ensure all code aligns with Dockerized, deployable design.
* Keep memory consistency and safety features as mandatory design principles.

---

===================================================================================

## 🎯 Goal Recap

We are building the **AI-Driven Interactive Story World**, moving from:

> Local CLI (single user, JSON storage)
> → Modular Backend (FastAPI + local memory)
> → Full Web App (React frontend + RAG + Knowledge Graph backend)

---

## 🧩 **Stage C – Local Development Architecture (Offline / Learning Phase)**

### **Overview Diagram**

```
 ┌───────────────────────────────────────────┐
 │                CLI / FastAPI              │
 │         (play.py or local web client)     │
 └───────────────────────────────────────────┘
                     │
                     ▼
        ┌──────────────────────────┐
        │        main.py           │
        │  ─ FastAPI backend       │
        │  ─ Routes for story gen  │
        │  ─ Gemini API connector  │
        └──────────────────────────┘
                     │
                     ▼
     ┌───────────────────────────────────┐
     │           Core Modules            │
     │  app/core/model.py  → LLM logic   │
     │  app/core/session.py → state mgmt │
     │  app/memory/storage.py → JSON     │
     │  app/memory/vector.py → Chroma    │
     │  app/memory/graph.py  → Dummy KG  │
     └───────────────────────────────────┘
                     │
                     ▼
      ┌──────────────────────────────────┐
      │  Local Memory Store (disk JSON) │
      │  story_memory_xxxxx.json        │
      │  + Chroma DB folder             │
      │  + world_state.json             │
      └──────────────────────────────────┘
                     │
                     ▼
     ┌────────────────────────────────────┐
     │       Gemini Model (via SDK)       │
     │   - Text generation                │
     │   - Fact extraction (JSON)         │
     │   - Summary compression            │
     └────────────────────────────────────┘
```

### 🧠 Key Concepts Learned Here:

* Prompt engineering for contextual generation
* Local vector search (Chroma / FAISS)
* Session persistence via JSON files
* Modular design (separation of LLM, memory, and logic)
* Testing and debugging API endpoints locally

### ⚙️ Example Commands

```bash
uvicorn main:app --reload
python play.py  # optional CLI
```

---

## 🌐 **Stage D – Cloud / Industry-Level Deployment Architecture**

### **Overview Diagram**

```
               ┌───────────────────────────────┐
               │        Web Frontend           │
               │  (React / Next.js + Tailwind) │
               │  - Story Interface            │
               │  - Choices / World View       │
               │  - Auth + Session Load        │
               └───────────────────────────────┘
                              │
                              ▼
             ┌─────────────────────────────────┐
             │        FastAPI Backend          │
             │  app/api/routes_story.py        │
             │  app/api/routes_memory.py       │
             │  app/api/routes_graph.py        │
             │  app/core/model.py (Gemini)     │
             │  app/core/rag_pipeline.py       │
             │  app/core/state_manager.py      │
             └─────────────────────────────────┘
                              │
    ┌─────────────────────────┴────────────────────────┐
    │                         │                        │
    ▼                         ▼                        ▼
┌─────────────┐     ┌────────────────┐        ┌──────────────────────┐
│ Vector DB   │     │ Knowledge Graph│        │ Gemini API (LLM)     │
│ (Pinecone or│     │ (Neo4j Aura)   │        │ - generation         │
│ Weaviate)   │     │ - characters,  │        │ - fact extraction    │
│ - recall    │     │   items, links │        │ - summarization      │
└─────────────┘     └────────────────┘        └──────────────────────┘
    │                      │                          │
    ▼                      ▼                          ▼
┌────────────────────────────────────────────────────────────┐
│        Storage + Infra                                     │
│   - PostgreSQL (for users/sessions)                        │
│   - Redis (for caching / async tasks)                      │
│   - Render / Railway (FastAPI hosting)                     │
│   - Vercel / Netlify (Frontend hosting)                    │
│   - Docker + CI/CD (GitHub Actions)                        │
└────────────────────────────────────────────────────────────┘
```

---

### ⚡ Improvements Over Local Setup

| Component     | Local            | Industry / Cloud                        |
| ------------- | ---------------- | --------------------------------------- |
| Memory        | JSON + Chroma    | Pinecone / Qdrant                       |
| Graph         | Dummy JSON       | Neo4j Aura Free                         |
| LLM           | Gemini via SDK   | Gemini via managed backend key rotation |
| Storage       | Disk             | PostgreSQL (sessions)                   |
| Auth          | None             | JWT / OAuth2                            |
| Frontend      | CLI / basic HTML | React / Next.js                         |
| Deployment    | Localhost        | Render (backend) + Vercel (frontend)    |
| Monitoring    | Console          | Sentry / OpenTelemetry                  |
| Collaboration | Single user      | Multi-user session API                  |

---

## 🧭 How We’ll Transition (Step-by-Step)

| Phase | Local                                                         | Transition Goal                |
| ----- | ------------------------------------------------------------- | ------------------------------ |
| **1** | Wrap up CLI with proper summarization + structured extraction | Done (Now)                     |
| **2** | Modularize memory and add Chroma vector memory                | Local RAG                      |
| **3** | Add dummy KG module                                           | Connect facts and entities     |
| **4** | Move to FastAPI backend + endpoints                           | Prepare for frontend           |
| **5** | Build React UI + API integration                              | Visual storytelling            |
| **6** | Migrate local stores → Neo4j + Pinecone (cloud)               | Industry setup                 |
| **7** | Containerize + deploy                                         | Full industry-level completion |

---

## 🧱 Folder Structure


```
ai_story/
│
├── app/
│   ├── api/
│   │   ├── routes_story.py
│   │   ├── routes_memory.py
│   │   └── routes_graph.py
│   │
│   ├── core/
│   │   ├── model.py          # Gemini API logic
│   │   ├── session.py        # session mgmt, short-term memory
│   │   ├── rag_pipeline.py   # retrieval-augmented generation logic
│   │   └── state_manager.py  # world & memory updates
│   │
│   ├── memory/
│   │   ├── storage.py        # disk/JSON persistence
│   │   ├── vector.py         # Chroma/FAISS interface
│   │   └── graph.py          # Neo4j / dummy KG interface
│   │
│   └── utils/
│       └── logger.py         # logging helper
│
├── main.py                   # FastAPI app entry
├── play.py                   # CLI (legacy/local testing)
├── requirements.txt
├── .env
└── README.md
```

---

===================================================================================

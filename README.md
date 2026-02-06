# AI Story World - Interactive Storytelling Platform

An AI-powered interactive storytelling application that generates dynamic narratives with persistent world state, knowledge graphs, and context-aware responses using Google's Gemini API.

## Features

- 🎭 **Dynamic Story Generation**: Contextual story continuations with 2-3 unique action choices
- 🧠 **Knowledge Graph**: Neo4j-powered entity tracking (characters, items, locations, relationships)
- 📚 **RAG Pipeline**: Vector search retrieval for narrative consistency
- 🔄 **Session Management**: Persistent story sessions with complete history
- 🛡️ **Safety & Rate Limiting**: Content filtering and API protection
- 🔑 **API Key Rotation**: Automatic failover across multiple Gemini API keys

## Tech Stack

**Backend:**
- FastAPI (Python)
- Google Gemini 2.5 Flash API
- Neo4j (Knowledge Graph)
- Redis (Caching & Rate Limiting)
- Qdrant/Chroma (Vector Storage)

**Frontend:**
- React + Vite
- React Router
- Framer Motion
- Lucide Icons

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (for full stack)
- Google Gemini API key(s)

### Local Development

1. **Clone and setup environment:**
```bash
git clone <repository-url>
cd ai-story
cp env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

2. **Option A: Run with Docker Compose (Recommended)**
```bash
docker-compose up -d
```
The API will be available at `http://localhost:8000`

3. **Option B: Run locally**

Backend:
```bash
# Create conda environment
conda create -n lang python=3.11
conda activate lang

# Install dependencies
pip install -r requirements.txt

# Start backend
cd ai_story
uvicorn main:app --reload --port 8000
```

Frontend:
```bash
cd web
npm install
npm run dev
```
Frontend will be available at `http://localhost:5173`

### Configuration

**Required environment variables:**
```env
GOOGLE_API_KEY=your_gemini_api_key_here
API_TOKEN=your_api_secret_token
```

**Optional - Multiple API keys for rotation:**
```env
GEMINI_API_KEY_1=key1
GEMINI_API_KEY_2=key2
GEMINI_API_KEY_3=key3
```

**Optional - Services:**
```env
REDIS_URL=redis://localhost:6379
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
VECTOR_BACKEND=chroma  # or qdrant
```

## API Endpoints

### Core Endpoints

- `POST /create_session` - Create new story session
- `GET /get_session/{session_id}` - Retrieve session
- `POST /start_story` - Begin story for session
- `POST /take_action` - Take action in story
- `GET /health` - Health check

### Authentication

All endpoints (except `/health`) require:
```
Authorization: Bearer <API_TOKEN>
```

## Deployment

### Docker Production

1. **Build and deploy:**
```bash
docker-compose up -d
```

2. **With Qdrant vector storage:**
```bash
docker-compose --profile qdrant up -d
```

3. **Environment variables:**
Ensure `.env` file is configured with production credentials.

### Manual Deployment

1. Set up Neo4j, Redis (optional but recommended)
2. Configure environment variables
3. Run backend: `uvicorn ai_story.main:app --host 0.0.0.0 --port 8000`
4. Build frontend: `cd web && npm run build`
5. Serve frontend with nginx/Apache

## Project Structure

```
ai-story/
├── ai_story/           # Backend FastAPI application
│   ├── app/
│   │   ├── api/        # API routes
│   │   ├── core/       # Core logic (model, RAG, key manager)
│   │   ├── memory/     # Graph & vector storage
│   │   ├── utils/      # Auth, safety, rate limiting
│   │   └── schemas/    # Pydantic models
│   └── main.py         # FastAPI entry point
├── web/                # Frontend React application
│   ├── src/
│   │   ├── components/ # React components
│   │   ├── pages/      # Page components
│   │   └── services/   # API client
│   └── vite.config.js
├── data/               # Persistent data (sessions, KG)
├── docker-compose.yml  # Docker orchestration
├── Dockerfile          # Backend container
└── requirements.txt    # Python dependencies
```

## Key Features Explained

### Structured Output
Uses Gemini function calling to generate:
- Story continuation text
- 2-3 contextual action choices
- Extracted world facts (entities, relationships)

### System Prompt Filtering
Multi-layer validation prevents system instructions from leaking to users.

### Knowledge Graph
Tracks:
- **Characters**: NPCs and their relationships
- **Items**: Possessions and locations
- **Locations**: Places and connections
- **Actions**: Player activities

## Development

### Running Tests
```bash
# Backend still works if session creation succeeds
curl -X POST http://localhost:8000/create_session \
  -H "Authorization: Bearer 123456" \
  -H "Content-Type: application/json" \
  -d '{"character_name":"Alice","genre":"fantasy","tone":"adventurous"}'
```

### Code Structure
- **Relative imports**: All app modules use relative imports for consistency
- **Key rotation**: Automatic failover across multiple API keys with circuit breaker
- **Session persistence**: JSON-based with future DB migration support

## Troubleshooting

**Import errors when starting backend:**
- Ensure you're in the `ai_story` directory
- Run: `cd ai_story && uvicorn main:app --reload`

**No API key found:**
- Check `.env` file exists and has `GOOGLE_API_KEY`
- Restart services after updating `.env`

**Frontend can't connect to backend:**
- Ensure backend is running on port 8000
- Check CORS settings in `main.py`
- Verify Vite proxy config in `web/vite.config.js`

## License

MIT

## Contact

For questions or support, please open an issue.

# Deployment Guide

## Local Development

### Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp env.example .env
# Edit .env with your API keys

# Run locally
uvicorn ai_story.main:app --reload --port 8000
```

### With Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

## Production Deployment

### Render.com Deployment

1. **Create Render Account** and connect your GitHub repo

2. **Create Web Service**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn ai_story.main:app --host 0.0.0.0 --port $PORT`
   - Environment: Python 3.11

3. **Set Environment Variables**:
   ```
   GOOGLE_API_KEY=your_key_here
   GEMINI_API_KEY_1=key1
   GEMINI_API_KEY_2=key2
   GEMINI_API_KEY_3=key3
   API_TOKEN=your_api_token
   MODEL=gemini-2.5-flash
   VECTOR_BACKEND=memory
   ```

4. **Add Redis Service** (optional):
   - Create Redis service in Render
   - Set `REDIS_URL` environment variable

### Railway Deployment

1. **Connect GitHub** to Railway

2. **Deploy Service**:
   - Railway will auto-detect Python
   - Add `requirements.txt` and `Dockerfile`

3. **Set Environment Variables**:
   ```
   GOOGLE_API_KEY=your_key_here
   GEMINI_API_KEY_1=key1
   GEMINI_API_KEY_2=key2
   GEMINI_API_KEY_3=key3
   API_TOKEN=your_api_token
   ```

4. **Add Redis** (optional):
   - Add Redis service in Railway
   - Railway will provide `REDIS_URL`

### Self-Hosted with Docker

```bash
# Build image
docker build -t ai-story .

# Run with environment
docker run -p 8000:8000 \
  -e GOOGLE_API_KEY=your_key \
  -e GEMINI_API_KEY_1=key1 \
  -e GEMINI_API_KEY_2=key2 \
  -e GEMINI_API_KEY_3=key3 \
  -e API_TOKEN=your_token \
  ai-story
```

## Environment Variables

### Required
- `GOOGLE_API_KEY` or `GEMINI_API_KEY`: Primary Gemini API key
- `API_TOKEN`: API authentication token

### Optional
- `GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, `GEMINI_API_KEY_3`: Additional keys for rotation
- `MODEL`: Gemini model (default: gemini-2.5-flash)
- `EMBED_MODEL`: Embedding model (default: sentence-transformers/all-MiniLM-L6-v2)
- `VECTOR_BACKEND`: Vector store backend (chroma, pinecone, qdrant, memory)
- `REDIS_URL`: Redis URL for key rotation counters
- `NEO4J_URI`: Neo4j connection string
- `NEO4J_USERNAME`: Neo4j username
- `NEO4J_PASSWORD`: Neo4j password

## Backup and Restore

### Chroma Vector Store
```bash
# Backup
cp -r data/chroma data/chroma_backup_$(date +%Y%m%d)

# Restore
cp -r data/chroma_backup_20240101 data/chroma
```

### Neo4j Database
```bash
# Backup
docker exec neo4j_container neo4j-admin dump --database=neo4j --to=/tmp/backup.dump

# Restore
docker exec neo4j_container neo4j-admin load --database=neo4j --from=/tmp/backup.dump
```

### Session Data
```bash
# Backup
tar -czf sessions_backup_$(date +%Y%m%d).tar.gz data/sessions/

# Restore
tar -xzf sessions_backup_20240101.tar.gz
```

## Monitoring

### Health Checks
- `GET /health`: Basic health check
- `GET /metrics`: Prometheus metrics

### Key Metrics
- `gemini_requests_total`: API request count by key
- `gemini_errors_total`: Error count by key and type
- `gemini_circuit_breaker_state`: Circuit breaker status
- `session_operations_total`: Session operation counts

### Logs
```bash
# View application logs
docker-compose logs -f api

# View specific service logs
docker-compose logs -f neo4j
docker-compose logs -f redis
```

## Troubleshooting

### Common Issues

1. **API Key Rotation Not Working**
   - Check Redis connection
   - Verify multiple keys are set
   - Check circuit breaker status in metrics

2. **Neo4j Connection Failed**
   - Verify NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
   - Check Neo4j service is running
   - Test connection: `cypher-shell -u neo4j -p password`

3. **Vector Store Issues**
   - Check VECTOR_BACKEND setting
   - Verify embedding model is installed
   - Check vector store credentials

4. **Memory Issues**
   - Monitor Redis memory usage
   - Check Neo4j heap settings
   - Consider vector store cleanup

### Performance Tuning

1. **Redis Configuration**
   ```bash
   # Increase memory limit
   redis-cli CONFIG SET maxmemory 2gb
   redis-cli CONFIG SET maxmemory-policy allkeys-lru
   ```

2. **Neo4j Configuration**
   ```bash
   # Increase heap size
   export NEO4J_HEAP_SIZE=2G
   export NEO4J_PAGE_CACHE_SIZE=1G
   ```

3. **Vector Store Optimization**
   - Use appropriate embedding model for your use case
   - Consider vector store cleanup policies
   - Monitor embedding generation time

# 🎮 AI Story Agent CLI - User Guide

## Overview

The AI Story Agent CLI provides a powerful command-line interface for interacting with your AI storytelling system. It supports both **standalone mode** (using local files) and **API backend mode** (connecting to the FastAPI server).

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** installed
2. **Required packages**: `pip install requests python-dotenv`
3. **Optional**: API backend running (`uvicorn ai_story.main:app --reload`)

### Basic Usage

```bash
# Interactive mode (standalone)
python cli.py

# Interactive mode (API backend)
python cli.py --api

# Create a new session
python cli.py --create "My Adventure"

# List all sessions
python cli.py --list-sessions

# Take a single action
python cli.py --session-id 12345 --action "walk north"
```

## 📋 Command Reference

### Core Commands

| Command | Description | Example |
|---------|-------------|---------|
| `--help` | Show help message | `python cli.py --help` |
| `--api` | Use API backend mode | `python cli.py --api` |
| `--api-url URL` | Set API backend URL | `python cli.py --api --api-url http://localhost:8000` |
| `--api-token TOKEN` | Set API authentication token | `python cli.py --api --api-token your_token` |

### Session Management

| Command | Description | Example |
|---------|-------------|---------|
| `--create NAME` | Create new session | `python cli.py --create "My Story"` |
| `--session-id ID` | Load specific session | `python cli.py --session-id 12345` |
| `--list-sessions` | List all sessions | `python cli.py --list-sessions` |
| `--delete-session ID` | Delete session | `python cli.py --delete-session 12345` |

### Actions

| Command | Description | Example |
|---------|-------------|---------|
| `--action TEXT` | Take single action | `python cli.py --session-id 12345 --action "pick up sword"` |

## 🎯 Usage Examples

### 1. Standalone Mode (No API Required)

```bash
# Start interactive session
python cli.py

# Create and immediately play a session
python cli.py --create "Forest Adventure"
# Then follow the interactive prompts

# Take a quick action
python cli.py --create "Quick Test" --action "explore the cave"
```

### 2. API Backend Mode (Full Features)

```bash
# Start API server first (in another terminal)
uvicorn ai_story.main:app --reload --port 8000

# Use CLI with API backend
python cli.py --api --api-token testtoken123

# Create session via API
python cli.py --api --api-token testtoken123 --create "API Adventure"

# Take action with RAG enhancement
python cli.py --api --api-token testtoken123 --session-id abc123 --action "Alice picks up the key"
```

### 3. Session Management

```bash
# List all available sessions
python cli.py --list-sessions

# Load existing session
python cli.py --session-id 12345

# Delete old session
python cli.py --delete-session 12345
```

## 🎮 Interactive Mode

When you run `python cli.py` without arguments, you enter interactive mode:

```
============================================================
[GAME] AI Story Agent CLI
============================================================

==================================================
Session Management
1. Create new session
2. Load existing session
3. List all sessions
4. Delete session
5. Start playing (if session loaded)
6. Exit

Choose an option (1-6):
```

### Session Creation
- Option 1: Create a new session
- Enter session name (optional)
- Enter seed text (optional)

### Session Loading
- Option 2: Load existing session
- Choose from numbered list of available sessions

### Playing Session
- Option 5: Start playing (requires loaded session)
- Type actions to continue the story
- Use special commands:
  - `info` - Show session information
  - `history [n]` - Show last n history entries
  - `save` - Save current session
  - `exit` - Return to main menu

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# API Configuration
API_TOKEN=your_api_token_here

# Gemini API Keys (for standalone mode)
GEMINI_API_KEY=your_gemini_key_here
GOOGLE_API_KEY=your_google_key_here

# Model Configuration
MODEL=gemini-2.5-flash
```

### API Backend Setup

1. **Start the API server**:
   ```bash
   uvicorn ai_story.main:app --reload --port 8000
   ```

2. **Set API token** (if required):
   ```bash
   export API_TOKEN=your_token_here
   # or add to .env file
   ```

3. **Use API mode**:
   ```bash
   python cli.py --api --api-token your_token
   ```

## 📁 File Structure

The CLI creates and manages sessions in these locations:

```
ai-story/
├── sessions/           # New session storage (recommended)
│   └── story_memory_*.json
├── story_memory/       # Legacy session storage
│   └── story_memory_*.json
└── cli.py             # CLI script
```

## 🚨 Troubleshooting

### Common Issues

1. **"Cannot connect to API"**
   - Make sure the API server is running: `uvicorn ai_story.main:app --reload`
   - Check the API URL: `python cli.py --api --api-url http://localhost:8000`

2. **"Invalid API token"**
   - Check your API token in `.env` file
   - Verify token is correct: `python cli.py --api --api-token your_token`

3. **"Session not found"**
   - List available sessions: `python cli.py --list-sessions`
   - Check session ID is correct

4. **Unicode/Character Issues**
   - The CLI uses ASCII-safe symbols for cross-platform compatibility
   - If you see encoding errors, ensure your terminal supports UTF-8

### Debug Mode

For debugging, you can check the session files directly:

```bash
# View session file
cat sessions/story_memory_12345.json

# Check API health
curl http://localhost:8000/health
```

## 🔄 Integration with Web Frontend

The CLI and web frontend share the same API backend:

1. **Start API server**: `uvicorn ai_story.main:app --reload`
2. **Use CLI**: `python cli.py --api`
3. **Use web frontend**: `cd web && npm run dev`
4. **Sessions are shared** between CLI and web interface

## 📊 Features Comparison

| Feature | Standalone Mode | API Mode |
|---------|----------------|----------|
| Session Management | ✅ Local files | ✅ API + Local |
| Story Generation | ✅ Basic | ✅ Full AI |
| RAG Enhancement | ❌ | ✅ |
| Fact Extraction | ❌ | ✅ |
| Vector Memory | ❌ | ✅ |
| Knowledge Graph | ❌ | ✅ |
| Metrics | ❌ | ✅ |
| Multi-user | ❌ | ✅ |

## 🎯 Best Practices

1. **Use API mode** for full features and production use
2. **Use standalone mode** for quick testing or offline use
3. **Save sessions regularly** using the `save` command
4. **Use descriptive session names** for easy identification
5. **Check API health** before using API mode: `curl http://localhost:8000/health`

## 🚀 Advanced Usage

### Batch Operations

```bash
# Create multiple sessions
python cli.py --create "Adventure 1"
python cli.py --create "Adventure 2"
python cli.py --create "Adventure 3"

# List all sessions
python cli.py --list-sessions

# Delete old sessions
python cli.py --delete-session old_session_id
```

### Scripting

```bash
#!/bin/bash
# Create session and take initial action
SESSION_ID=$(python cli.py --api --create "Scripted Adventure" | grep "Created session:" | cut -d' ' -f3)
python cli.py --api --session-id $SESSION_ID --action "explore the forest"
```

### Integration with Other Tools

```bash
# Use with curl for API testing
curl -X POST "http://localhost:8000/create_session" \
  -H "Content-Type: application/json" \
  -H "X-API-Token: testtoken123" \
  -d '{"session_name": "API Test"}'

# Use CLI to interact with the session
python cli.py --api --session-id abc123 --action "continue story"
```

This CLI provides a complete interface for your AI Story Agent system, supporting both casual users and power users who want to script interactions with the system.

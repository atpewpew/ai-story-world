Run API locally:

```bash
uvicorn ai_story.main:app --reload --port 8000
```

```bash
cd web
npm run dev
```

Demo steps:
1) POST /create_session {"session_name":"demo"}
2) POST /take_action with "Alice picks up a small key."
3) GET /get_session to inspect world/items and kg snapshot under data/kg.



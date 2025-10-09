from fastapi import FastAPI, Depends, Request
from .app.api.routes_session import router as session_router
from .app.api.routes_story import router as story_router
from .app.utils.auth import require_api_token
from .app.utils.rate_limit import ip_rate_limit
from prometheus_fastapi_instrumentator import Instrumentator


app = FastAPI(title="AI Story World")
app.include_router(session_router, dependencies=[Depends(require_api_token), Depends(ip_rate_limit)])
app.include_router(story_router, dependencies=[Depends(require_api_token), Depends(ip_rate_limit)])


@app.get("/health")
def health():
    return {"status": "ok"}


# Metrics
Instrumentator().instrument(app).expose(app)



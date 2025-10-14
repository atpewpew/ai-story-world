import logging

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from .app.api.routes_session import router as session_router
from .app.api.routes_story import router as story_router
from .app.utils.auth import require_api_token
from .app.utils.rate_limit import ip_rate_limit
from prometheus_fastapi_instrumentator import Instrumentator

# Load environment variables
load_dotenv()

# Reset the key manager global instance to ensure it loads keys after environment is set
import ai_story.app.core.key_manager as km_module
km_module._key_manager = None

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("ai_story.main")

app = FastAPI(title="AI Story World")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add demo endpoint without authentication first
from .app.api.routes_story import demo_action
app.add_api_route("/demo_action", demo_action, methods=["POST"])

# Add authenticated routers
app.include_router(session_router, dependencies=[Depends(require_api_token), Depends(ip_rate_limit)])
app.include_router(story_router, dependencies=[Depends(require_api_token), Depends(ip_rate_limit)])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    try:
        body = await request.json()
    except Exception:
        body = "<unavailable>"
    logger.warning(
        "Validation error for request %s %s: body=%s errors=%s",
        request.method,
        request.url,
        body,
        exc.errors(),
    )
    return JSONResponse(
        status_code=422,
        content={
            "ok": False,
            "error": "validation_error",
            "detail": exc.errors(),
            "body": body,
        },
    )


# Metrics
Instrumentator().instrument(app).expose(app)



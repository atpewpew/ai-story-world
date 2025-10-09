import os
from fastapi import Header, HTTPException


async def require_api_token(x_api_token: str | None = Header(default=None)) -> None:
    required = os.getenv("API_TOKEN")
    if not required:
        return
    if x_api_token != required:
        raise HTTPException(status_code=401, detail="Invalid or missing API token")



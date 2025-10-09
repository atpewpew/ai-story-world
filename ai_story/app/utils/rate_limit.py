import time
from fastapi import HTTPException, Request


_bucket: dict[str, list[float]] = {}


async def ip_rate_limit(request: Request, max_per_minute: int = 60) -> None:
    ip = request.client.host if request and request.client else "unknown"
    now = time.time()
    window_start = now - 60
    hits = _bucket.setdefault(ip, [])
    # drop old
    _bucket[ip] = [t for t in hits if t >= window_start]
    if len(_bucket[ip]) >= max_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    _bucket[ip].append(now)



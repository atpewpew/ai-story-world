from fastapi import HTTPException


BANNED = [
    "kill",
    "murder",
    "hate",
    "racist",
    "sexual",
]


def ensure_safe(user_text: str) -> None:
    t = (user_text or "").lower()
    if any(b in t for b in BANNED):
        raise HTTPException(status_code=400, detail="Input rejected by safety filter")



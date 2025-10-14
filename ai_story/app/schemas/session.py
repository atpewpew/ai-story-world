from typing import Optional, Dict, Any, Annotated
from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    session_name: Annotated[
        str,
        Field(..., strip_whitespace=True, min_length=1, description="Human friendly session name"),
    ]
    seed_text: Optional[str] = Field("", description="Optional initial seed text for the story")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional session settings")

    class Config:
        schema_extra = {
            "example": {
                "session_name": "MyFirstStory",
                "seed_text": "Once upon a time...",
                "settings": {"tone": "whimsical", "difficulty": "medium"},
            }
        }

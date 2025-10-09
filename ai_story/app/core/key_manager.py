import os
import time
import asyncio
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import redis
from google import genai
from google.genai import types


class KeyState(Enum):
    ACTIVE = "active"
    CIRCUIT_OPEN = "circuit_open"
    COOLDOWN = "cooldown"
    DISABLED = "disabled"


@dataclass
class KeyInfo:
    key_id: str
    api_key: str
    state: KeyState
    last_used: float
    error_count: int
    success_count: int
    circuit_breaker_threshold: int = 5
    cooldown_duration: int = 300  # 5 minutes
    max_concurrent: int = 10
    current_concurrent: int = 0


class KeyManager:
    def __init__(self, redis_url: Optional[str] = None):
        self.keys: List[KeyInfo] = []
        self.redis_client = None
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
            except Exception:
                pass
        self._load_keys()
        self._semaphore = asyncio.Semaphore(100)  # Global concurrency limit

    def _load_keys(self):
        """Load API keys from environment variables"""
        key_patterns = ["GOOGLE_API_KEY", "GEMINI_API_KEY", "GEMINI_API_KEY_"]
        
        for pattern in key_patterns:
            if pattern.endswith("_"):
                # Handle numbered keys like GEMINI_API_KEY_1, GEMINI_API_KEY_2
                for i in range(1, 10):  # Support up to 9 keys
                    key_value = os.getenv(f"{pattern}{i}")
                    if key_value:
                        self.keys.append(KeyInfo(
                            key_id=f"key_{i}",
                            api_key=key_value,
                            state=KeyState.ACTIVE,
                            last_used=0,
                            error_count=0,
                            success_count=0
                        ))
            else:
                key_value = os.getenv(pattern)
                if key_value:
                    self.keys.append(KeyInfo(
                        key_id=pattern.lower(),
                        api_key=key_value,
                        state=KeyState.ACTIVE,
                        last_used=0,
                        error_count=0,
                        success_count=0
                    ))

    async def get_available_key(self) -> Optional[KeyInfo]:
        """Get the best available key using round-robin with least-used priority"""
        async with self._semaphore:
            available_keys = [k for k in self.keys if k.state == KeyState.ACTIVE and k.current_concurrent < k.max_concurrent]
            
            if not available_keys:
                return None
            
            # Sort by last_used (least recently used first)
            available_keys.sort(key=lambda k: k.last_used)
            return available_keys[0]

    async def acquire_key(self, key_info: KeyInfo) -> bool:
        """Acquire a key for use (increment concurrent counter)"""
        if key_info.current_concurrent >= key_info.max_concurrent:
            return False
        key_info.current_concurrent += 1
        return True

    def release_key(self, key_info: KeyInfo):
        """Release a key after use"""
        key_info.current_concurrent = max(0, key_info.current_concurrent - 1)
        key_info.last_used = time.time()

    def record_success(self, key_info: KeyInfo):
        """Record successful API call"""
        key_info.success_count += 1
        key_info.error_count = 0  # Reset error count on success
        if key_info.state == KeyState.CIRCUIT_OPEN:
            key_info.state = KeyState.ACTIVE

    def record_error(self, key_info: KeyInfo, error_type: str):
        """Record API error and handle circuit breaker"""
        key_info.error_count += 1
        
        if error_type in ["rate_limit", "quota_exceeded"]:
            key_info.state = KeyState.CIRCUIT_OPEN
            key_info.last_used = time.time() + key_info.cooldown_duration
        elif key_info.error_count >= key_info.circuit_breaker_threshold:
            key_info.state = KeyState.CIRCUIT_OPEN
            key_info.last_used = time.time() + key_info.cooldown_duration

    def check_circuit_breaker(self, key_info: KeyInfo) -> bool:
        """Check if circuit breaker should be reset"""
        if key_info.state == KeyState.CIRCUIT_OPEN:
            if time.time() > key_info.last_used:
                key_info.state = KeyState.ACTIVE
                return True
        return key_info.state == KeyState.ACTIVE

    async def get_metrics(self) -> Dict[str, any]:
        """Get metrics for all keys"""
        metrics = {}
        for key in self.keys:
            metrics[f"key_{key.key_id}"] = {
                "state": key.state.value,
                "success_count": key.success_count,
                "error_count": key.error_count,
                "current_concurrent": key.current_concurrent,
                "last_used": key.last_used
            }
        return metrics

    async def generate_with_key(self, key_info: KeyInfo, prompt: str, model: str = "gemini-2.5-flash") -> Tuple[Optional[str], Optional[str]]:
        """Generate text using specific key with error handling"""
        if not self.check_circuit_breaker(key_info):
            return None, "circuit_breaker_open"
        
        if not await self.acquire_key(key_info):
            return None, "concurrency_limit"
        
        try:
            client = genai.Client(api_key=key_info.api_key)
            content = types.Content(parts=[types.Part(text=prompt)])
            response = client.models.generate_content(
                model=model,
                contents=[content],
                config=types.GenerateContentConfig(
                    temperature=0.8,
                    max_output_tokens=500,
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            )
            
            text = getattr(response, "text", None)
            if isinstance(text, str) and text.strip():
                self.record_success(key_info)
                return text.strip(), None
            else:
                self.record_error(key_info, "empty_response")
                return None, "empty_response"
                
        except Exception as e:
            error_type = "unknown"
            if "quota" in str(e).lower() or "limit" in str(e).lower():
                error_type = "quota_exceeded"
            elif "429" in str(e) or "rate" in str(e).lower():
                error_type = "rate_limit"
            elif "403" in str(e):
                error_type = "forbidden"
            
            self.record_error(key_info, error_type)
            return None, error_type
        finally:
            self.release_key(key_info)

    async def generate_with_rotation(self, prompt: str, model: str = "gemini-2.5-flash") -> str:
        """Generate text with automatic key rotation and fallback"""
        # Try each available key
        for _ in range(len(self.keys)):
            key_info = await self.get_available_key()
            if not key_info:
                break
            
            result, error = await self.generate_with_key(key_info, prompt, model)
            if result:
                return result
            
            # If we get here, the key failed
            if error in ["circuit_breaker_open", "concurrency_limit"]:
                continue  # Try next key
            elif error in ["quota_exceeded", "rate_limit"]:
                # These errors suggest we should try a different key
                continue
        
        # All keys failed, return fallback
        return "The story continues with the wind rustling through the trees. [Fallback response - all API keys unavailable]"


# Global instance
_key_manager: Optional[KeyManager] = None

def get_key_manager() -> KeyManager:
    global _key_manager
    if _key_manager is None:
        redis_url = os.getenv("REDIS_URL")
        _key_manager = KeyManager(redis_url)
    return _key_manager

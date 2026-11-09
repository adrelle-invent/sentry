import hashlib
import hmac
import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from core.cache import cache

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def generate_access_key() -> tuple[str, str, str]:
    """
    Returns (full_key, prefix, key_hash).
    full_key is only available at seed time — log it once, never stored.
    """
    token = secrets.token_urlsafe(32)
    full_key = f"sk_{token}"
    prefix = full_key[:8]
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    return full_key, prefix, key_hash


async def verify_api_key(api_key: str = Security(api_key_header)) -> dict:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key",
        )

    # 1. Extract prefix (assuming prefix is the first 8 characters, e.g., 'sk_12345')
    if len(api_key) < 8:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key format",
        )
    
    prefix = api_key[:8]
    redis_key = f"apikey:prefix:{prefix}"

    # 2. Fetch the stored hash from Redis
    stored_hash = await cache.get(redis_key)
    if not stored_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )

    # 3. Hash the incoming key to compare against the stored hash
    incoming_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # 4. Use constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(incoming_hash, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )

    # Optional: Fetch associated metadata (e.g., user_id, scopes) from Redis if stored as a hash or JSON
    return {"prefix": prefix, "status": "authenticated"}
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

from core.config import settings

password_hash = PasswordHash(
    (
        Argon2Hasher(),
        BcryptHasher(),
    )
)

ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> tuple[bool, str | None]:
    return password_hash.verify_and_update(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """Encodes a signed JWT access token containing the subject and expiration."""
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    return jwt.encode(
        to_encode,
        settings.APP_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """Encodes a signed JWT refresh token with an extended expiration period."""
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    return jwt.encode(
        to_encode,
        settings.APP_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict[str, Any] | None:
    """Decodes and verifies a JWT token signature and expiration.

    Returns the payload dictionary if valid, or None if invalid/expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.APP_KEY.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.PyJWTError:
        return None


def verify_token_type(payload: dict[str, Any], expected_type: str) -> bool:
    """Ensures a decoded token payload matches the expected token type ('access' or 'refresh')."""
    return payload.get("type") == expected_type
"""Authentication service — user management, password hashing, JWT tokens."""

from __future__ import annotations

import hashlib
import hmac
import os
import uuid
from datetime import datetime, timedelta, timezone

import jwt

from immigration_compliance.models.auth import TokenData, UserCreate, UserOut, UserRole

# JWT configuration — use env var in production, fallback for dev
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "verom-dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def _hash_password(password: str) -> str:
    """Hash a password with a random salt using SHA-256. Production should use bcrypt."""
    salt = os.urandom(16).hex()
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"{salt}:{hashed}"


def _verify_password(password: str, stored: str) -> bool:
    """Verify a password against a stored hash."""
    salt, expected = stored.split(":", 1)
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return hmac.compare_digest(actual, expected)


class AuthService:
    """In-memory user store with password hashing and JWT tokens."""

    def __init__(self) -> None:
        self._users: dict[str, dict] = {}  # user_id -> user data (with hashed password)
        self._email_index: dict[str, str] = {}  # email -> user_id

    def create_user(self, data: UserCreate) -> UserOut:
        email_lower = data.email.lower()
        if email_lower in self._email_index:
            raise ValueError("An account with this email already exists")

        user_id = str(uuid.uuid4())
        hashed = _hash_password(data.password)

        user_record = {
            "id": user_id,
            "email": email_lower,
            "hashed_password": hashed,
            "first_name": data.first_name,
            "last_name": data.last_name,
            "role": data.role,
            "bar_number": data.bar_number,
            "jurisdiction": data.jurisdiction,
            "years_experience": data.years_experience,
            "specializations": data.specializations,
        }
        self._users[user_id] = user_record
        self._email_index[email_lower] = user_id

        return self._to_user_out(user_record)

    def authenticate(self, email: str, password: str) -> UserOut | None:
        email_lower = email.lower()
        user_id = self._email_index.get(email_lower)
        if user_id is None:
            return None
        user = self._users[user_id]
        if not _verify_password(password, user["hashed_password"]):
            return None
        return self._to_user_out(user)

    def get_user(self, user_id: str) -> UserOut | None:
        user = self._users.get(user_id)
        if user is None:
            return None
        return self._to_user_out(user)

    def create_access_token(self, user: UserOut) -> str:
        expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        payload = {
            "sub": user.id,
            "role": user.role.value,
            "exp": expire,
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> TokenData | None:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str | None = payload.get("sub")
            role: str | None = payload.get("role")
            if user_id is None or role is None:
                return None
            return TokenData(user_id=user_id, role=UserRole(role))
        except jwt.PyJWTError:
            return None

    @staticmethod
    def _to_user_out(record: dict) -> UserOut:
        return UserOut(
            id=record["id"],
            email=record["email"],
            first_name=record["first_name"],
            last_name=record["last_name"],
            role=record["role"],
            bar_number=record["bar_number"],
            jurisdiction=record["jurisdiction"],
            years_experience=record["years_experience"],
            specializations=record["specializations"],
        )

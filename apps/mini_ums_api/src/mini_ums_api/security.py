"""Password hashing and session tokens.

Passwords: scrypt from the standard library with a per-user salt, stored as
`scrypt$n$r$p$salt$hash`. Session tokens: random, URL-safe; only their SHA-256 is stored,
so a database dump cannot be replayed as live sessions.
"""

import base64
import hashlib
import hmac
import secrets

_N, _R, _P = 2**14, 8, 1


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32)
    return "$".join(["scrypt", str(_N), str(_R), str(_P), _b64(salt), _b64(digest)])


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt, digest = stored.split("$")
        if scheme != "scrypt":
            return False
        candidate = hashlib.scrypt(
            password.encode(), salt=_unb64(salt), n=int(n), r=int(r), p=int(p), dklen=32
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(candidate, _unb64(digest))


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))

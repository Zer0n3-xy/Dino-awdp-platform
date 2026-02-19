import base64
import datetime as dt
import hashlib
import hmac
import json
import secrets

from app.core.config import settings


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    pad = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + pad)


def get_password_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"pbkdf2_sha256${_b64url_encode(salt)}${_b64url_encode(digest)}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        scheme, salt_b64, digest_b64 = hashed_password.split("$", 2)
    except ValueError:
        return False
    if scheme != "pbkdf2_sha256":
        return False
    salt = _b64url_decode(salt_b64)
    expected = _b64url_decode(digest_b64)
    actual = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 120_000)
    return hmac.compare_digest(actual, expected)


def create_access_token(subject: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    expire = int((dt.datetime.utcnow() + dt.timedelta(minutes=settings.access_token_expire_minutes)).timestamp())
    payload = {"sub": subject, "exp": expire}

    header_part = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_part = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_part}.{payload_part}".encode("ascii")
    signature = hmac.new(settings.secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_part}.{payload_part}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> str:
    try:
        header_part, payload_part, signature_part = token.split(".", 2)
    except ValueError as exc:
        raise ValueError("Invalid token") from exc

    signing_input = f"{header_part}.{payload_part}".encode("ascii")
    expected_sig = hmac.new(settings.secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    provided_sig = _b64url_decode(signature_part)

    if not hmac.compare_digest(expected_sig, provided_sig):
        raise ValueError("Invalid token")

    payload = json.loads(_b64url_decode(payload_part))
    subject = payload.get("sub")
    exp = payload.get("exp")
    if not subject or not isinstance(exp, int):
        raise ValueError("Invalid token payload")
    if int(dt.datetime.utcnow().timestamp()) >= exp:
        raise ValueError("Token expired")
    return subject

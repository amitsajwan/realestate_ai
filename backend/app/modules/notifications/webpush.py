"""Web Push to a phone's browser: message encryption (RFC 8291, aes128gcm) and the server's signature (VAPID, RFC 8292).

Written here rather than taken from pywebpush, which would add aiohttp, py-vapid and http-ece for about eighty lines on top of
`cryptography`, which we already have; the send is one httpx POST. tests/modules/notifications/test_webpush.py checks the
encryption against the worked example in RFC 8291 (section 5 and appendix A), byte for byte.

Keys are base64url without padding, as browsers and every Web Push library write them: the public key is the 65-byte uncompressed
P-256 point (what Studio passes to pushManager.subscribe), the private key the 32-byte secret number.
"""
import base64
import json
import os
import struct
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
from urllib.parse import urlsplit

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

RECORD_SIZE = 4096
VAPID_LIFETIME = timedelta(hours=12)   # RFC 8292 allows up to 24 hours


def b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def unb64u(text: str) -> bytes:
    text = "".join(text.split())
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _hkdf(salt: bytes, ikm: bytes, info: bytes, length: int) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=length, salt=salt, info=info).derive(ikm)


def _public_bytes(key: ec.EllipticCurvePublicKey) -> bytes:
    return key.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)


def _private_key(raw: bytes) -> ec.EllipticCurvePrivateKey:
    return ec.derive_private_key(int.from_bytes(raw, "big"), ec.SECP256R1())


def generate_keys() -> Tuple[str, str]:
    """A new VAPID key pair: (public, private), base64url. deploy/gcp: `python scripts/vapid_keys.py` prints them for .env."""
    key = ec.generate_private_key(ec.SECP256R1())
    return b64u(_public_bytes(key.public_key())), b64u(key.private_numbers().private_value.to_bytes(32, "big"))


def encrypt(plaintext: bytes, ua_public: str, auth_secret: str, as_private: Optional[bytes] = None,
            salt: Optional[bytes] = None) -> bytes:
    """The aes128gcm body for one subscription (one record: our payloads are far under 4 KB). `ua_public` and `auth_secret` are the
    subscription's keys.p256dh and keys.auth. `as_private` and `salt` are fresh for every message; the tests pass the RFC's."""
    ua_pub = unb64u(ua_public)
    auth = unb64u(auth_secret)
    sender = _private_key(as_private) if as_private else ec.generate_private_key(ec.SECP256R1())
    as_pub = _public_bytes(sender.public_key())
    salt = salt if salt is not None else os.urandom(16)
    ecdh = sender.exchange(ec.ECDH(), ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), ua_pub))
    ikm = _hkdf(auth, ecdh, b"WebPush: info\x00" + ua_pub + as_pub, 32)
    cek = _hkdf(salt, ikm, b"Content-Encoding: aes128gcm\x00", 16)
    nonce = _hkdf(salt, ikm, b"Content-Encoding: nonce\x00", 12)
    if len(plaintext) + 1 + 16 > RECORD_SIZE:
        raise ValueError("push payload too large for one record")
    body = AESGCM(cek).encrypt(nonce, plaintext + b"\x02", None)   # 0x02: the last (and only) record
    return salt + struct.pack("!IB", RECORD_SIZE, len(as_pub)) + as_pub + body


def vapid_headers(endpoint: str, public_key: str, private_key: str, subject: str, now: datetime) -> Dict[str, str]:
    """Authorization for the push service at `endpoint`: a short-lived ES256 token naming us (`subject`, a mailto: or https: URL)."""
    parts = urlsplit(endpoint)
    claims = {"aud": f"{parts.scheme}://{parts.netloc}", "exp": int((now + VAPID_LIFETIME).timestamp()), "sub": subject}
    header = b64u(json.dumps({"typ": "JWT", "alg": "ES256"}, separators=(",", ":")).encode())
    payload = b64u(json.dumps(claims, separators=(",", ":")).encode())
    signing_input = f"{header}.{payload}".encode()
    der = _private_key(unb64u(private_key)).sign(signing_input, ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(der)
    token = f"{header}.{payload}.{b64u(r.to_bytes(32, 'big') + s.to_bytes(32, 'big'))}"
    return {"Authorization": f"vapid t={token}, k={public_key}"}


def request(subscription: dict, payload: dict, public_key: str, private_key: str, subject: str, ttl: int = 3600,
            now: Optional[datetime] = None) -> Tuple[str, Dict[str, str], bytes]:
    """(url, headers, body) of the POST that delivers `payload` (JSON) to one subscription {endpoint, keys: {p256dh, auth}}."""
    keys = subscription.get("keys") or {}
    body = encrypt(json.dumps(payload, ensure_ascii=False).encode("utf-8"), keys["p256dh"], keys["auth"])
    headers = vapid_headers(subscription["endpoint"], public_key, private_key, subject, now or datetime.now(timezone.utc))
    # high: a buyer is waiting, so the phone is woken even when it is saving battery
    headers.update({"TTL": str(ttl), "Content-Encoding": "aes128gcm", "Content-Type": "application/octet-stream", "Urgency": "high"})
    return subscription["endpoint"], headers, body

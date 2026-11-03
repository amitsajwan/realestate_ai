"""Web Push encryption and VAPID signing (app/modules/notifications/webpush.py), against RFC 8291's worked example."""
import json
from datetime import datetime, timezone

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.modules.notifications import webpush

NOW = datetime(2026, 11, 3, 9, 0, tzinfo=timezone.utc)

# RFC 8291 section 5 and appendix A
PLAINTEXT = b"When I grow up, I want to be a watermelon"
AUTH = "BTBZMqHH6r4Tts7J_aSIgg"
UA_PUBLIC = "BCVxsr7N_eNgVRqvHtD0zTZsEc6-VV-JvLexhqUzORcxaOzi6-AYWXvTBHm4bjyPjs7Vd8pZGH6SRpkNtoIAiw4"
UA_PRIVATE = "q1dXpw3UpT5VOmu_cf_v6ih07Aems3njxI-JWgLcM94"
AS_PRIVATE = "yfWPiYE-n46HLnH0KqZOF1fJJU3MYrct3AELtAQ-oRw"
SALT = "DGv6ra1nlYgDCS1FRnbzlw"
BODY = ("DGv6ra1nlYgDCS1FRnbzlwAAEABBBP4z9KsN6nGRTbVYI_c7VJSPQTBtkgcy27ml"
        "mlMoZIIgDll6e3vCYLocInmYWAmS6TlzAC8wEqKK6PBru3jl7A_yl95bQpu6cVPT"
        "pK4Mqgkf1CXztLVBSt2Ks3oZwbuwXPXLWyouBWLVWGNWQexSgSxsj_Qulcy4a-fN")


def _decrypt(body: bytes, ua_private: str, auth: str) -> bytes:
    """What the phone's browser does with a push: the receiving side of RFC 8291, written apart from the sender."""
    salt, rs, idlen = body[:16], int.from_bytes(body[16:20], "big"), body[20]
    as_pub, ciphertext = body[21:21 + idlen], body[21 + idlen:]
    assert rs == 4096
    me = ec.derive_private_key(int.from_bytes(webpush.unb64u(ua_private), "big"), ec.SECP256R1())
    ua_pub = me.public_key().public_bytes(webpush.serialization.Encoding.X962, webpush.serialization.PublicFormat.UncompressedPoint)
    ecdh = me.exchange(ec.ECDH(), ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), as_pub))
    hk = lambda salt_, ikm, info, n: HKDF(algorithm=hashes.SHA256(), length=n, salt=salt_, info=info).derive(ikm)  # noqa: E731
    ikm = hk(webpush.unb64u(auth), ecdh, b"WebPush: info\x00" + ua_pub + as_pub, 32)
    plain = AESGCM(hk(salt, ikm, b"Content-Encoding: aes128gcm\x00", 16)).decrypt(hk(salt, ikm, b"Content-Encoding: nonce\x00", 12), ciphertext, None)
    assert plain.endswith(b"\x02")
    return plain[:-1]


def test_the_rfc_8291_example_encrypts_to_the_published_body_byte_for_byte():
    body = webpush.encrypt(PLAINTEXT, UA_PUBLIC, AUTH, as_private=webpush.unb64u(AS_PRIVATE), salt=webpush.unb64u(SALT))
    assert webpush.b64u(body) == BODY


def test_a_message_with_fresh_keys_opens_on_the_phone_and_never_repeats():
    a = webpush.encrypt(b'{"title":"New lead"}', UA_PUBLIC, AUTH)
    b = webpush.encrypt(b'{"title":"New lead"}', UA_PUBLIC, AUTH)
    assert a != b   # a new sender key and salt each time
    assert _decrypt(a, UA_PRIVATE, AUTH) == b'{"title":"New lead"}'


def test_the_vapid_token_names_the_push_service_and_us_and_verifies_with_our_public_key():
    public, private = webpush.generate_keys()
    h = webpush.vapid_headers("https://fcm.googleapis.com/fcm/send/abc:xyz", public, private, "mailto:hello@avasetu.in", NOW)
    scheme, rest = h["Authorization"].split(" ", 1)
    assert scheme == "vapid"
    fields = dict(part.strip().split("=", 1) for part in rest.split(","))
    assert fields["k"] == public
    head, claims, sig = fields["t"].split(".")
    assert json.loads(webpush.unb64u(claims)) == {"aud": "https://fcm.googleapis.com", "exp": int(NOW.timestamp()) + 12 * 3600,
                                                   "sub": "mailto:hello@avasetu.in"}
    assert json.loads(webpush.unb64u(head)) == {"typ": "JWT", "alg": "ES256"}
    raw = webpush.unb64u(sig)
    key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), webpush.unb64u(public))
    key.verify(encode_dss_signature(int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big")),
               f"{head}.{claims}".encode(), ec.ECDSA(hashes.SHA256()))   # raises if the signature is wrong


def test_a_push_request_carries_the_encrypted_json_and_the_headers_push_services_need():
    public, private = webpush.generate_keys()
    sub = {"endpoint": "https://web.push.apple.com/QGuQyavXutnMH", "keys": {"p256dh": UA_PUBLIC, "auth": AUTH}}
    url, headers, body = webpush.request(sub, {"title": "New lead", "body": "Rohit enquired"}, public, private, "mailto:x@y.in", ttl=600, now=NOW)
    assert url == sub["endpoint"]
    assert headers["TTL"] == "600" and headers["Content-Encoding"] == "aes128gcm" and headers["Urgency"] == "high"
    assert headers["Authorization"].startswith("vapid t=")
    assert json.loads(_decrypt(body, UA_PRIVATE, AUTH)) == {"title": "New lead", "body": "Rohit enquired"}


def test_generated_keys_are_a_p256_pair_in_the_form_browsers_take():
    public, private = webpush.generate_keys()
    assert len(webpush.unb64u(public)) == 65 and webpush.unb64u(public)[0] == 4
    assert len(webpush.unb64u(private)) == 32
    assert "=" not in public + private

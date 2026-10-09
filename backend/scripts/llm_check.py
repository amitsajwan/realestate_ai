"""Ask every configured text provider for one JSON answer and print which work: python scripts/llm_check.py [path/to/.env]"""
import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_env(path: str) -> None:
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


async def main() -> int:
    load_env(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", ".env"))
    from app.platform.llm import ModelHealth, text_providers

    providers = text_providers()
    if not providers:
        print("No LLM key set (GROQ_API_KEY, OPENROUTER_API_KEYS, GEMINI_API_KEY, NVIDIA_API_KEY, CLOUDFLARE_API_TOKEN...)")
        return 1
    ok = 0
    for p in providers:
        p.health = ModelHealth()   # each check starts fresh, so one busy model does not hide another provider
        start = time.monotonic()
        out = await p.json('Reply with the JSON object {"ok": true}.', "Check")
        took = time.monotonic() - start
        works = isinstance(out, dict) and out.get("ok") is True
        ok += works
        print(f"{'OK  ' if works else 'FAIL'} {p.host:<45} key …{p.api_key[-4:]}  {p.model}  {took:.1f}s")
    print(f"{ok}/{len(providers)} providers answered")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

"""Which WhatsApp features are on, and what is missing for the rest. Read-only; prints no token or secret.

    cd backend && PYTHONPATH=. python scripts/whatsapp_status.py
    (on the VM: sudo docker compose exec -T -e PYTHONPATH=. backend python scripts/whatsapp_status.py)

Everything is switched on by deploy/gcp/whatsapp_connect.ps1 (docs/WHATSAPP_SETUP.md, section H: the day the number arrives).
"""
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.modules.whatsapp.config import load  # noqa: E402


def lines() -> list:
    cfg = load()
    out, todo = [], []

    def row(name: str, on: bool, detail: str) -> None:
        out.append(f"{'ON ' if on else 'off'}  {name:<30} {detail}")

    inbound = cfg.enabled and bool(cfg.phone_number_id) and cfg.can_send and bool(cfg.app_secret) and bool(cfg.verify_token)
    missing = [n for n, ok in (("WHATSAPP_ENABLED", cfg.enabled), ("WHATSAPP_PHONE_NUMBER_ID", cfg.phone_number_id),
                               ("WHATSAPP_ACCESS_TOKEN", cfg.access_token), ("WHATSAPP_APP_SECRET", cfg.app_secret),
                               ("WHATSAPP_VERIFY_TOKEN", cfg.verify_token)) if not ok]
    row("Buyer assistant (webhook)", inbound, "number id " + (cfg.phone_number_id or "-") + (f"; missing {', '.join(missing)}" if missing else ""))
    row("Replies really sent", inbound and not cfg.dry_run, "WHATSAPP_DRY_RUN=" + ("true (test mode: replies stored, not sent)" if cfg.dry_run else "false"))
    if missing:
        todo.append("run deploy/gcp/whatsapp_connect.ps1 -PhoneNumberId <id> (sections A-E of docs/WHATSAPP_SETUP.md)")
    elif cfg.dry_run:
        todo.append("after testing, run it again with -Live so replies are sent")
    row("Owner (unrouted chats)", bool(cfg.owner_agent_id), cfg.owner_agent_id or "none: chats that name no agent create no lead")
    row("Agents' own numbers", bool(cfg.number_agents), f"{len(cfg.number_agents)} mapped (WHATSAPP_NUMBER_AGENTS)")

    from app.modules.propertyfacts.identity import whatsapp_label
    label = whatsapp_label()
    row("WhatsApp line on posts", bool(label), (f"{label}: Facebook tap-to-chat, Instagram 'send: interested in CODE'" if label
                                                 else "WHATSAPP_PUBLIC_NUMBER not set: posts carry only the interest link"))
    if not label:
        todo.append("when the real number is live, run whatsapp_connect.ps1 again with -PublicNumber 91XXXXXXXXXX (posts + website)")
    elif not inbound:
        todo.append("posts show a WhatsApp number but the assistant is not connected: chats would go unanswered")

    from app.modules.onboarding.trial import enabled as trial_on
    row("Free-trial codes on 'TRIAL'", inbound and trial_on(), "TRIAL_CLAIMS=" + (os.environ.get("TRIAL_CLAIMS") or "on (default)"))
    out.append("     Website buttons (NEXT_PUBLIC_WHATSAPP_NUMBER) are set when the frontend is built; -PublicNumber rebuilds it.")
    if todo:
        out.append("")
        out += ["To do:"] + [f"  - {t}" for t in todo]
    return out


if __name__ == "__main__":
    print("\n".join(lines()))

# Pilot runbook (invite-only agents)

Agents sign up with their phone number plus a **personal 6-digit invite code** that you send them on WhatsApp.
No SMS provider, business registration or Meta approval is needed. You choose who gets in.

## Turn it on
Backend environment (`backend/.env`):
```
JOIN_MODE=invite          # default is "otp" (development: OTP printed in the server log / returned as dev_code)
JOIN_TOKEN_DAYS=30        # how long an agent stays signed in on their phone
PUBLIC_SITE_URL=https://<your app url>
```

## Invite an agent
```
cd backend
PYTHONPATH=. .venv/Scripts/python.exe scripts/invite.py issue 98765 43210 --label "Rahul, Baner"
```
It prints the code and a ready-to-paste WhatsApp message. Re-running `issue` for the same number creates a NEW code,
invalidates the old one and clears any lockout (use this when an agent forgets or gets locked).

## Remove access
```
PYTHONPATH=. .venv/Scripts/python.exe scripts/invite.py revoke 9876543210
```

## Rules the system enforces
- A number without an active invite gets "Signup is by invitation during the pilot".
- 5 wrong codes lock that number for 30 minutes; 15 wrong codes in total block it until you re-issue.
- Codes are stored hashed; the plaintext is shown once, when issued.
- The code is reusable (it is the agent's personal access code) until revoked.

## Later
When there is a business entity: register with an SMS provider (DLT) or WhatsApp authentication templates and switch
`JOIN_MODE=otp`. The app flow is identical for the agent.

---

# Running the pilot on the GCP server

Live address: https://34-180-39-243.sslip.io (a real domain replaces this later: point an A record at 34.180.39.243 and change `SITE_HOST` in `deploy/gcp/.env`).
VM `pune-property` in project `trader-502012`, zone `asia-south1-a`. Only ports 80/443 are open to the world; MongoDB is private; secrets live only in `deploy/gcp/.env` on the VM.

## Ship a new version
Commit your changes, then from the repo root:
```
.\deploy\gcp\deploy.ps1 -DryRun     # shows every step, contacts nothing
.\deploy\gcp\deploy.ps1             # bundle git HEAD -> copy to the VM -> docker compose up -d --build -> health check
```
Only TRACKED files are shipped (no .env, no node_modules, no uploads). The VM's `.env` is never overwritten.

## Invite an agent (on the VM)
```
gcloud compute ssh pune-property --zone asia-south1-a --project trader-502012
cd app/deploy/gcp
sudo docker compose exec -T -e PYTHONPATH=. backend python scripts/invite.py issue 98765 43210 --label "Rahul, Baner"
sudo docker compose exec -T -e PYTHONPATH=. backend python scripts/invite.py revoke 9876543210
sudo docker compose exec -T -e PYTHONPATH=. backend python scripts/invite_requests.py list          # people who asked for an invite on /request-invite
sudo docker compose exec -T -e PYTHONPATH=. backend python scripts/invite_requests.py mark-invited 9876543210
```
Send the printed code to the agent on WhatsApp. They open the site, tap "Sign in", enter their number and code.

## Look after it
- Logs: `sudo docker compose logs --tail 100 backend` (also `frontend`, `caddy`).
- Backups: a daily disk snapshot is kept for 7 days (policy `pune-daily`). Uploads and MongoDB live on that one disk.
- Public settings (privacy contact etc.) are `NEXT_PUBLIC_*` values, set at BUILD time in the frontend service; change them and redeploy.
- Meta/Instagram/Facebook posting: keep `SOCIAL_DRY_RUN=true` until the first real test post works (see docs/META_SETUP.md).

## Known limits
One VM and one disk: fine for a 10-agent pilot, no high availability. SSH is currently open to the world; restrict it to Google's identity-aware proxy
(`deploy.ps1 -Iap` once done). The VM shares a Google Cloud project with the trading system: consider a separate project.

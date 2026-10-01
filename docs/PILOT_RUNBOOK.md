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

## Concierge (setting up an agent for him)
The owner can set up agents without them touching the app first (see AGENT_INVITE_KIT.md section 9). Studio shows an **Agents** tab only to owner accounts.
- **Who is the owner:** a superuser, or user ids in `CONCIERGE_OWNER_IDS` (comma separated). Closed by default: with neither set, everyone gets 403 and the tab stays hidden. `INTEREST_OWNER_AGENT_ID` / `ENGAGE_OWNER_AGENT_ID` listings are treated as the owner's own (no "Listed by" line).
- **Add an agent:** creates his login, website and invite code in one step. Codes are stored hashed and shown once; "Make a new code" (reissue) invalidates the old one. At most 10 new invites per hour.
- **Consent first:** `POST /concierge/agents/{id}/consent` records the exact wording, time and who recorded it. Posting an agent's listing returns 409 until it is recorded; switching it off blocks posting again.
- **Audit:** every owner change is a row in `concierge_audit` (who, when, action, agent, changed field names, listing id). `db.concierge_audit.find({agent_id: "<id>"}).sort({at: -1})`.
- **What gets posted:** the PUNE Property Page and Instagram only (still dry-run unless real posting is switched on in the social settings). Captions carry "Listed by ..." and the RERA agent number when known, never a phone. Instagram items also appear on `/go`.
- **Phone numbers:** lists and detail show masked numbers (98******10). The full number appears only in the invite response to the owner.
- **Wrong listing or consent withdrawn:** switch consent off in Agents; to take a post down use Facebook/Instagram directly (we do not delete posts from the app).

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
- Database dumps, restore test, health alerts: see "Ops: backups, restore and health checks" below.
- Public settings (privacy contact etc.) are `NEXT_PUBLIC_*` values, set at BUILD time in the frontend service; change them and redeploy.
- Meta/Instagram/Facebook posting: keep `SOCIAL_DRY_RUN=true` until the first real test post works (see docs/META_SETUP.md).

## Ops: backups, restore and health checks
Both jobs run on the VM from cron. Install once, after a `deploy.ps1` that includes these scripts (each supports `-DryRun`, `-Remove`, `-Iap`):
```
.\deploy\gcp\install_backup_cron.ps1     # nightly 03:00 IST (21:30 UTC, the VM clock is UTC); runs one backup straight away
.\deploy\gcp\install_health_cron.ps1     # every 15 minutes; runs one verbose check straight away
```

**Backups.** `backup.sh` dumps the app database (`propertyai`, or `DATABASE_NAME` from `.env`) with `mongodump --archive --gzip` into `~/backups/YYYY-MM-DD.archive.gz`, keeps the newest 14, and logs to `~/backup.log`. It exits non-zero on any failure. The daily disk snapshot stays as a second layer; uploaded photos are NOT in the dump (they are on the disk/snapshot, volume `uploads`).
- Run one by hand: `cd ~/app/deploy/gcp && bash backup.sh` (`--dry-run` shows the plan).
- Prove a backup is usable (do this after installing, then monthly): `bash restore_test.sh`. It restores the newest archive into a throwaway database `restore_test_<time>`, prints collection counts next to the live ones, and drops the throwaway database. Live data is only read. "OK ... restores cleanly" is a pass; "MISSING from backup" or any FAILED line is a fail.
- Copy a backup off the VM (keep at least one copy somewhere that is not this disk):
  ```
  gcloud compute scp --project trader-502012 --zone asia-south1-a pune-property:backups/2026-09-30.archive.gz .
  ```
  (latest: `gcloud compute ssh pune-property --zone asia-south1-a --project trader-502012 --command "ls -1 backups | tail -n 1"` first.) The file holds personal data of leads: store it privately.
- Restore for real (disaster): copy the archive to the VM, then `cd ~/app/deploy/gcp && sudo docker compose exec -T mongo sh -c 'mongorestore --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --archive --gzip --drop' < ~/backups/FILE.archive.gz`. `--drop` replaces the collections in the dump, so only do this on purpose, ideally after copying the current state off first.

**Health.** `health_check.sh` writes to `~/health.log` only when something is wrong (one `FAIL name: detail` line per failing check) and one `OK recovered` line when it clears. Read it: `gcloud compute ssh pune-property --zone asia-south1-a --project trader-502012 --command "tail -n 30 health.log"`. Run it live: `bash health_check.sh --verbose` (prints every check; `--dry-run` also prints the alert instead of sending it). An empty or missing log means everything has been fine.

| Log line starts with | Meaning | What to do |
|---|---|---|
| `FAIL site` | the public address does not answer | `sudo docker compose ps`; check `caddy` logs; is the VM up? |
| `FAIL api` | `/api/v1/health` is not "healthy" | `sudo docker compose logs --tail 100 backend`; mongo down? |
| `FAIL disk` | root disk at or above 90% | clear old images `sudo docker image prune -a`, check `uploads`, resize the disk |
| `FAIL container X` | service X is stopped, missing or unhealthy | `sudo docker compose up -d X` and read its logs |
| `FAIL facebook-token` | Meta rejected the Page token (same cause as the red banner in the Interest tab) | re-run `meta_connect.ps1` (docs/META_SETUP.md H4, causes in H5) |
| `FAIL backup` | no backup, or the newest is older than 36 hours | `tail ~/backup.log`; run `bash backup.sh`; is the backup cron installed (`crontab -l`)? |

Not counted as failures: Meta being unreachable for a moment (skipped silently) and no Page token being configured.

Alerts are optional. Add either line to the VM's `~/app/deploy/gcp/.env` (nothing else to install; the health check reads them each run and never prints them):
- `ALERT_WEBHOOK_URL=https://...` a JSON POST `{"text": "...", "content": "..."}`: works with a Slack or Discord incoming webhook or an ntfy/relay URL.
- `ALERT_EMAIL=you@example.com` uses `mail`, `mailx` or `sendmail` if the VM has one (it has none by default; prefer the webhook).
An alert goes out when the set of failing checks changes, again every 6 hours while it lasts, and once more when it recovers. Test the hook: `bash health_check.sh --test-alert`. Without either setting, `health.log` is the only record, so look at it (or set a webhook).

## Known limits
One VM and one disk: fine for a 10-agent pilot, no high availability. SSH is currently open to the world; restrict it to Google's identity-aware proxy
(`deploy.ps1 -Iap` once done). The VM shares a Google Cloud project with the trading system: consider a separate project.

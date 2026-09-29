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

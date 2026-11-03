---
name: deploy
description: How code reaches avasetu.in - the automatic deploy after green checks on main, a deploy or rollback by hand, checking a release, and turning the automatic deploy off. Use when deploying, when a change is not live yet, when a Deploy run says skipped or failed, or when rolling back.
---

# Deploy

Production is one VM (`pune-property`, project `trader-502012`, zone `asia-south1-a`, folder `~/app`) running the containers in
`deploy/gcp/docker-compose.yml`, plus the Cloud Run Job `renderer` that draws reels. The VM never builds: GitHub builds the
images and the VM only pulls them, tagged with the full commit sha.

## 1. The normal way: push to main

A push to `main` goes live by itself (ON since 2026-10-25):

```
push to main
  ├─ Build app images             (images.yml)        backend + frontend + studio images, tagged <sha>, Artifact Registry
  ├─ Frontend tests and build     (ci.yml)            jest + next build, for the site (frontend/) and Studio (studio/)
  └─ Architecture and backend tests (architecture.yml) lint-imports + pytest
        each one, when it finishes, starts  Deploy (deploy.yml)
           gate:   all three green for <sha>?  and  <sha> still the newest commit on main?
           deploy: ssh to the VM -> deploy/gcp/vm_update.sh <sha> (pull, restart; Caddy only if its routes changed) -> health check (API, and Studio at /join)
                   health fails -> the previous commit is put back and the run fails (GitHub emails the owner)
           then:   the renderer job is pointed at the same image
```

- Three Deploy runs per commit is normal: the first two say "Waiting for <workflow>", the last one deploys.
- A red check: the gate logs `::warning::<workflow> ended 'failure'` and nothing deploys. Fix it and push again
  (the `fix-failing-test` skill). Never deploy a red commit by hand to get around it.
- A newer push before the checks finish: the older commit is skipped ("no longer the newest"); the newer one deploys.
- Takes about 10 minutes from push (the backend suite is the slowest check).
- A deploy restarts every worker: a marketing run in progress is cut off. Tell the other sessions on this machine before
  pushing something risky (ListAgents / SendMessage).

Watch it: `gh run list --workflow Deploy --limit 5`, then `gh run view <id> --log`.

## 2. By hand

Redeploy main, or roll back to an older commit (its images must have been built):

```
gh workflow run deploy.yml                          # the newest commit on main
gh workflow run deploy.yml -f sha=<40-char sha>     # a rollback
gh run watch
```

A run by hand skips the gate (commits before 2026-10-24 never had green tests). Code is rolled back, data is not.

From this PC instead of GitHub (works whether the automatic deploy is on or off), from a CLEAN checkout of the commit:

```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File deploy/gcp/deploy.ps1          # waits for the image build, ~2 min
powershell.exe -NoProfile -ExecutionPolicy Bypass -File deploy/gcp/deploy.ps1 -Tag <sha>   # roll back
```

The main checkout (C:\Users\code\realestate_ai) is shared with other sessions and often has their uncommitted edits: deploy
from a worktree (`git worktree add --detach C:\Users\code\rem-<name> origin/main`), and remove it afterwards. `NativeCommandError`
in PowerShell output is gcloud writing progress to stderr; read the output, not the exit code.

## 3. Check a release

| Check | How | Pass |
|---|---|---|
| Health | the Deploy run's notice, or `curl https://avasetu.in/api/v1/health` | `"status": "healthy"` |
| Images | `gcloud compute ssh pune-property --zone asia-south1-a --command "sudo docker ps --format '{{.Names}} {{.Image}}'"` | every app container on `:<sha>` |
| Workers | same ssh, `sudo docker exec gcp-media-1 python -m app.worker --check --role dispatch` | OK lines (calendar_reels etc. STALE is normal: Cloud Run renders them) |
| The change | open the page it changed, `curl` it and grep for the new text | it is there |

## 4. When the Deploy run says skipped

- Every run skipped (the gate job never started): `gh variable list` has no `AUTO_DEPLOY=true`. Someone turned it off.
- `Cannot reach ... over ssh: nothing was changed`: the VM's address changed, port 22 was closed, or the key was removed.
  Run the setup again (below): it makes a new key and stores the new address.

## 5. Turn it on or off

```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File deploy/gcp/ci_deploy_setup.ps1 -DryRun   # checks, changes nothing
powershell.exe -NoProfile -ExecutionPolicy Bypass -File deploy/gcp/ci_deploy_setup.ps1           # on (a new key each time)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File deploy/gcp/ci_deploy_setup.ps1 -Off      # off, key removed
```

On means: an ssh key made on the VM for user `amits` (comment `github-deploy` in the VM's ssh-keys metadata), its private
half in the GitHub secret `DEPLOY_SSH_KEY`, and the variables `DEPLOY_SSH_USER`, `DEPLOY_SSH_HOST`, `DEPLOY_KNOWN_HOSTS`
(the VM's host key, pinned) and `AUTO_DEPLOY=true`. GitHub connects on port 22 from changing addresses, so ssh stays open to
0.0.0.0/0 (the key is the lock). Turning it on or off is the owner's call.

Files: `.github/workflows/deploy.yml` (gate + deploy), `deploy/gcp/ci_deploy.sh` (ssh, health, rollback),
`deploy/gcp/vm_update.sh` (on the VM), `deploy/gcp/deploy.ps1` (by hand), `deploy/gcp/ci_deploy_setup.ps1` (on/off).

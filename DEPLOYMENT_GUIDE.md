# Deployment guide

This file used to hold a generic template (Redis, local MongoDB, `deploy.sh`) that does not match how Avasetu runs. It is kept in
git history only.

**Use [docs/operator/OPERATOR_GUIDE.md](docs/operator/OPERATOR_GUIDE.md).** It is the one document to:
- bring the system up from nothing on a fresh Google Cloud VM (section 0, then section 2),
- release each new version: pull request checks, deploy, after-release checks, roll back (section 5),
- set every setting and service key (sections 3 and 4: `deploy/gcp/keys.ps1` shows, adds and checks the keys),
- run it day to day: health checks, backups, rotations and common fixes (sections 6 to 9).

A phone-friendly copy: [docs/operator/OPERATOR_GUIDE.html](docs/operator/OPERATOR_GUIDE.html).

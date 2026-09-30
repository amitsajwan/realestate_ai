# P1 Ops - handoff

## Shipped (all in `deploy/gcp/`, run on the VM unless noted)
- `backup.sh`: `mongodump --archive --gzip` of the app DB (`DATABASE_NAME` in .env, default `propertyai`) from the compose `mongo` container into `~/backups/YYYY-MM-DD.archive.gz`; writes to a `.partial` file, validates size and gzip, renames; keeps newest 14; logs to `~/backup.log`; non-zero exit on failure. `--dry-run`. Password is read inside the container from `MONGO_INITDB_ROOT_PASSWORD`, never on the host.
- `restore_test.sh`: restores the newest (or given) archive into `restore_test_<epoch>` via `--nsFrom/--nsTo`, prints restored vs live counts, fails on an empty restore or a live collection with data missing from the backup, always drops the throwaway DB (EXIT trap). `--dry-run`.
- `health_check.sh`: site, `/api/v1/health`, disk (fail at 90%), 4 containers, Meta Page token (python via `docker compose exec -T backend python -`, `debug_token` with the token as both input and access token, prints one status word only), newest backup age (36h). Writes `~/health.log` on failures and recovery; alert de-duplication in `~/.health_state`. Optional hook `ALERT_WEBHOOK_URL` / `ALERT_EMAIL` from `.env`. Flags `--verbose`, `--dry-run`, `--test-alert`.
- `install_backup_cron.ps1`, `install_health_cron.ps1` (Windows, gcloud): tagged idempotent crontab line via scp + ssh of a small script; `-DryRun`, `-Remove`, `-Iap`, `-NoRunNow`. Backup 21:30 UTC (03:00 IST) daily; health every 15 min.
- `docs/PILOT_RUNBOOK.md`: new "Ops: backups, restore and health checks" section plus one pointer bullet.

## Design notes
- Cron user needs docker access: scripts use `docker compose` if permitted, else `sudo -n docker compose`.
- `.env` is parsed with grep, never sourced. No secret is printed, logged or stored.
- Uploads (volume `uploads`) are not in the mongodump; they are covered only by the disk snapshot.
- Dedupe: alert on change of failing set, every 6h while failing, once on recovery. Meta network errors (not code 190/102) are not failures.

## Tested locally (Git Bash, stub `docker` and `curl`)
Syntax (`bash -n`), `--dry-run` of all three, backup happy path and its "mongo not running" failure, health check pass/fail paths, log + state file, de-duplication (second run sends nothing), recovery path not exercised, installers' `-DryRun` output.

## NOT verified (needs the VM)
Real mongodump/mongorestore flags on `mongo:7` (`--nsFrom/--nsTo` with `--nsInclude`, mongosh `process.env.DBN`), `docker compose ps --format '{{.Service}} {{.State}} {{.Health}}'` field output on the VM's compose version, sudo without a password for the ssh user, real Graph `debug_token` answer for the Page token, webhook delivery, crontab install over gcloud ssh, VM timezone (assumed UTC), `stat -c`/`df --output` (GNU, expected on the VM image).
First steps after deploy: run both installers, then `bash restore_test.sh` on the VM, then `bash health_check.sh --verbose` and `--test-alert`.

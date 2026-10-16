# Reel rendering on demand

How reels get drawn: on a Cloud Run Job that starts when work waits and stops when it is done, not on the always-on VM.
Owner's decisions, 2026-10-16: hybrid (small VM for the always-on parts, Cloud Run for drawing), reels drawn in parallel,
"proper design, as an architect". Costs and the VM plan: [MODERNIZATION.md](MODERNIZATION.md) phase 1b.

## Goals
1. **Fast:** N reels take about the time of one (drawn in parallel).
2. **Cheap:** pay only while drawing; the VM stays e2-medium.
3. **Reliable:** no reel lost or drawn twice; a crash is a retry, never a stuck "making".
4. **Simple to run:** one queue, one renderer, one dispatcher, one-line rollback.

## Status
| Part | Status |
|---|---|
| Renderer job `renderer` (Cloud Run, asia-south1, 4 vCPU / 8 GB, 60 min limit, image = the deployed backend image) | **LIVE** 2026-10-16 |
| `python -m app.worker --drain` (`reels/render_job.py`): drains the three existing media queues, exits after a minute idle | **LIVE** |
| VM worker role `dispatch` (`MEDIA_ROLE=dispatch` in the VM's .env): starts the job when work waits and none runs | **LIVE** |
| VM e2-medium with its own service account `pune-vm` (pull images, run/view this job, write logs only) | **LIVE** |
| `render_tasks` queue, one task per reel, leases, parallel copies, budget guard | TARGET (P2) |
| Walkthrough, calendar pre-render, boost and video voice-over in the same queue; old claims deleted | TARGET (P3) |
| One reel drawn in chunks on 8 vCPUs; Cloud Storage instead of NFS | TARGET (P4, optional) |

Measured on the first runs: start to database ready ~25 s; one voiced reel ~4 min 20 s of drawing; the dispatcher started
the job 8 s after a voice-over was asked.

## How it works today (P1)
- **Files:** the job mounts the VM's uploads volume over NFS at `/app/uploads`, the same path as in the VM's containers, so no
  file path changed. The VM exports only that folder, only to the private subnet 10.160.0.0/20.
- **Database:** Mongo is published on the VM's private IP only (`MONGO_BIND=10.160.0.4`), password auth as always; GCP's firewall
  lets only the private ranges reach it. The job's environment is the VM's .env with `MONGODB_URL` on that IP.
- **Dispatcher:** every 20 s, if `render_job.queued()` finds work and the job's latest execution has finished, it starts one
  execution (Cloud Run Admin API, the VM's metadata token). The execution drains everything, so one runs at a time today.
- **Deploy:** `deploy.ps1` points the job at the deployed image, so the VM and the renderer always run the same code.
- **Rollback:** `MEDIA_ROLE=media` in the VM's .env, then `docker compose up -d media`: the VM draws again, as before.

## Target design (P2-P3)
### One task = one reel
Today the work hides in three places with three claims (`marketing_runs` flags such as `voices_queued`, one claim per run;
`reel_jobs`; calendar rows without a video). One claim per run is why four voice-overs went to one worker in a row.

`render_tasks`, one document per reel to draw:
```
{ _id, kind: voice | ad_reel | walkthrough | calendar_reel | boost | video_voice,
  owner: {run_id, angle} | {reel_job_id} | {calendar_row_id},     # where the result goes
  inputs: {...}, status: queued | leased | done | failed,
  lease: {by, until}, attempts, error,
  timings: {queued_at, leased_at, done_at, seconds}, created_at }
```

### Flow
```
 Studio / calendar / marketing run (VM)
        │ 1. enqueue one task per reel (queued); the owner shows "queued" at once
        ▼
 render_tasks (Mongo on the VM)
        ▲                                   ▲
        │ 2. every 10 s: queued − running   │ 3. each copy: lease → draw → finish → next
 Dispatcher (VM) ── starts N copies ──► Cloud Run Job "renderer" (N tasks, ≤ MAX_PARALLEL)
        4. finish: result into its owner, waiting calendar rows updated, timings recorded
        5. fan-in: a run whose reel tasks are all done shows "reels done"
```
1. **Enqueue:** an action that needs reels adds one task per reel.
2. **Dispatch:** queued tasks minus running copies = copies to add, up to `MAX_PARALLEL` (6), as one execution with that task
   count (Cloud Run run overrides).
3. **Lease:** a copy takes the oldest queued task atomically (`queued` → `leased`, 10-minute lease renewed every minute).
4. **Finish:** the video is written under a temporary name and renamed; the result is saved into the owner only if the copy
   still holds the lease. A copy exits after 30 s without a task (billing stops).
5. **Fan-in:** marketing runs keep their writing (LLM, light) on the VM; only their reels become tasks.

### Failures
| What | What happens |
|---|---|
| A copy crashes or reaches 60 min | The lease expires, the task is `queued` again, another copy takes it; after 3 attempts `failed`, with its error in Studio. |
| The renderer cannot reach Mongo or NFS | Tasks stay queued; the dispatcher alerts after 3 starts that did nothing. |
| The VM restarts or redeploys | Tasks wait in Mongo; running copies lose their leases and the tasks are retried. |
| A flood of requests | `MAX_PARALLEL` caps copies; a daily CPU-minute budget (proposed 300 min, about ₹100 a day at most) holds the rest until the next day and alerts. |
| Bad renderer code | `deploy.ps1 -Tag <old sha>` (the job follows the image), or `MEDIA_ROLE=media`. |

### Sizing and cost
- One copy: 4 vCPU / 8 GB, ~3-4 min a reel, ~25 s to start. Four reels in parallel: ~4-5 min in all.
- About ₹2-3 a reel whether in parallel or one by one (billing is per vCPU-second): ~$5 a month at 5 reels a day.
- 8 vCPUs a copy pays only after P4 (one reel drawn in chunks); frame drawing is mostly single-threaded Python.
- GPU: not useful for this CPU-bound drawing; revisit only for AI-generated video.

### Security
- The job reaches Mongo (password, private network) and the NFS share (private subnet); nothing public.
- The VM's account `pune-vm` may only pull images, run and view this one job, and write logs.
- To do: the job's environment into Secret Manager (~$1 a month) instead of plain job variables.

## Phases
| Phase | What | Effort |
|---|---|---|
| P1 | Drain job + dispatcher, one execution at a time; VM to dispatch, e2-medium, own account. | **LIVE 2026-10-16** |
| P2 | `render_tasks`, leases, timings; voice-overs and ad reels as one task per reel; parallel copies; budget guard. | ~1 day |
| P3 | Walkthrough, calendar pre-render, boost, video voice-over into the same queue; old claims deleted; Studio "drawing 2 of 4". | ~1 day |
| P4 | Optional: one reel in chunks on 8 vCPUs; Cloud Storage instead of NFS if the VM disk or NFS becomes a limit. | 1-2 days |

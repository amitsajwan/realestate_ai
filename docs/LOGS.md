# Reading the logs: did marketing work, and if not, why?

The marketing pipeline writes **one log line per step**, always in the same shape (`app/platform/trace.py`):

```
pipeline=reel ref=3f2a9c… step=voice outcome=failed reason="HTTP 403: API key not valid. Please pass a valid API key." audio=music lang=hi
```

| field      | meaning |
|------------|---------|
| `pipeline` | `startup`, `marketing` (a "Start marketing" run), `reel` (a listing reel job), `publish` (a calendar post going to Facebook / Instagram) |
| `ref`      | the run, job or post: `grep "ref=<id>"` gives that run's whole story, in order |
| `step`     | the stage inside the pipeline (below) |
| `outcome`  | `ok` worked · `fallback` worked with less (music without voice, rules script without the LLM) · `skipped` did not run (a setting is off or missing) · `failed` did not work |

`ok` is logged at INFO, `fallback` and `skipped` at WARNING, `failed` at ERROR. Lines never contain keys or tokens.

## Where the logs are

- **Docker:** `docker compose logs backend` (and `worker` when `RUN_BACKGROUND_LOOPS=false`). Add `-f` to follow.
- **Files:** `backend/logs/app.log` (JSON, one object per line; the line above is its `message`), errors also in `logs/error.log`.

## 1. Start here: what can this server do?

At every start the API and the worker log one `pipeline=startup` line per dependency:

```
grep "pipeline=startup" logs/app.log | tail -6
pipeline=startup ref=api step=ffmpeg   outcome=ok
pipeline=startup ref=api step=voice    outcome=skipped reason="GOOGLE_TTS_API_KEY is not set" effect="reels are music only, no voice-over"
pipeline=startup ref=api step=llm      outcome=ok reason="LLM key is set"
pipeline=startup ref=api step=music    outcome=ok
pipeline=startup ref=api step=social   outcome=skipped reason="SOCIAL_DRY_RUN is on" effect="posts are marked published but nothing is sent"
pipeline=startup ref=api step=calendar outcome=skipped reason="CALENDAR_ENABLED is off" effect="approved posts are not sent"
```

Anything not `ok` here explains every later run on this server. Check the **worker**'s lines too: the reels and the
marketing runs run in the worker when `RUN_BACKGROUND_LOOPS=false`, and it needs the same settings as the API.

## 2. A reel with no voice-over

```
grep "pipeline=reel" logs/app.log | grep "step=voice"
```

| what you see | what happened | fix |
|---|---|---|
| `outcome=skipped reason="GOOGLE_TTS_API_KEY is not set"` | the server (the worker, if it renders) has no TTS key | set `GOOGLE_TTS_API_KEY` in the environment of the process that renders, restart |
| `outcome=failed reason="HTTP 403: …API key not valid…"` or `…has not been used in project…` | the key is wrong, or the Text-to-Speech API is not enabled for its Google Cloud project | enable "Cloud Text-to-Speech API" for the key's project; check the key's API restrictions |
| `outcome=failed reason="HTTP 429: …"` | quota exceeded | raise the quota or wait |
| `outcome=failed reason="HTTP 400: …voice…"` | a voice name in `REEL_VOICE_<LANG>` does not exist | remove the override or fix the name |
| `outcome=failed reason="voice service unreachable (ConnectError)"` | no network to `texttospeech.googleapis.com` | check the server's outbound network / proxy |
| `outcome=ok mode=take` / `mode=lines` | voice made (in one take, or line by line after the one take did not cut cleanly) | — |

The reason is also kept on the job in MongoDB: `db.reel_jobs.find({_id: "<id>"}, {audio: 1, note: 1, voice_error: 1})`.
A `voice-over: one take not used (…)` warning just before is not a failure: the voice is then made line by line.

## 3. A whole reel

```
grep "pipeline=reel ref=<job id>" logs/app.log
```

`start` → `photo_tags` (fallback = photos in upload order) → `script` (`made_by=llm`, or `fallback made_by=rules` with the
reason: no LLM key, call failed, broke the fact rules, too pushy) → `voice` → `done`. The `done` line has
`audio=voice+music|music`, the photo count, the seconds it took and the video path; `done outcome=failed` has the error.

## 4. A marketing run ("Start marketing")

```
grep "pipeline=marketing ref=<run id>" logs/app.log
```

`start` → `facts` (usable / held facts, the MahaRERA match, nearby places, notes) → `posts` (how many made, how many by the
LLM, and every dropped angle with why) → `slides_reel` per carousel → `walkthrough_reel` (queued with its reel job id, which
you then follow under `pipeline=reel`, or `skipped` with why, e.g. the daily limit) → `done`.

## 5. Publishing to Facebook / Instagram

```
grep "pipeline=publish" logs/app.log
```

`ref` is the post's slug. `outcome=ok` has the permalink; `outcome=fallback` is a failed attempt that will be retried
(`attempt=1/3`); `outcome=failed` means it gave up; `outcome=skipped` means dry run (nothing was sent).

## Quick checks

```
grep -E "outcome=(failed|fallback|skipped)" logs/app.log | grep -v "pipeline=startup" | tail -50   # everything that went less than well
grep "pipeline=reel" logs/app.log | grep "step=done" | tail -20                                   # last 20 reels and their audio
```

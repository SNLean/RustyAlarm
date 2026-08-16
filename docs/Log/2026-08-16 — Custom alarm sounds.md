---
title: Custom alarm sounds
tags:
  - log
  - rustyalarm
  - saas
date: 2026-08-16
---

# Custom alarm sounds

Users can now pick a sound per alarm; the panel plays it when the alarm fires while the page is open. The owner grows a catalog by uploading more.

## Design

- **`saas/sounds.py`** — catalog over two sources: built-in sounds shipped in the repo (`saas/assets/sounds/`, read-only) and admin uploads (`DATA_DIR/sounds/`, gitignored, so they persist and never get committed). `resolve()` is the single choke point that maps a client-supplied name to a real file; it rejects anything that isn't a bare basename with a `.mp3/.ogg/.wav` extension → no path traversal.
- **Playback is frontend-only.** The monitor is untouched. The panel already polls `/api/alarms` every 2 s; it plays an alarm's sound when that alarm's `trigger_count` increases (first render only initializes, so historical fires don't blast on load). Audio is armed on the first user gesture to satisfy browser autoplay policy; there's a header mute toggle (persisted in localStorage) and the play falls back to the default sound if the chosen one was deleted.
- **Backend**: `sound` column on `alarms` (client field, validated as safe-filename-or-empty; ALTER-TABLE migration for existing DBs). Routes: `GET /api/sounds`, `GET /sounds/{file}` (auth'd `FileResponse`), `POST`/`DELETE /api/admin/sounds` (admin + `same_origin`, 2 MB cap, mp3/ogg/wav, built-ins undeletable).
- **Admin page** got an upload form + a catalog table (preview/delete).
- Four built-in sounds (sirena, bip, buzzer, campana) generated as WAV with numpy.

## Verified

Routes tested end-to-end on a **temp `RUSTALARM_DATA_DIR`** (never the live DB again): catalog, serve, path-traversal → 404, upload with sanitized filename, `.exe` rejected, delete, built-in protected, non-admin → 403. An adversarial review of the upload/serve/playback surface followed.

## References

- [[Subscription service]] — where this plugs in
- [[Security review]] — the escaping/CSRF/traversal invariants this respects

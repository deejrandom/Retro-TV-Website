# Warren C. Bennett's Retro Future

A personal website built like an old TV. **VHF** channels carry my own content (writing, games, pixel art); **UHF** channels carry public-domain cartoons, TV and films.

Live at **https://warrencbennett.com**

## How it fits together

| Part | Where it runs | Files |
|---|---|---|
| Front end (the TV) | Neocities (warrencbennett.com) | `index.html` |
| Backend + admin panel | Render (retro-tv-website.onrender.com) | `backend.py`, `requirements.txt`, `Procfile` |
| Channel lineup (live) | Render's disk at `/data/schedule.json` | edited through `/admin` |

- Merging to `main` redeploys Render automatically, and a GitHub Action uploads `index.html` to Neocities.
- The channel lineup is **not** stored in this repo. Edit channels at `https://retro-tv-website.onrender.com/admin`.

## Live broadcast

Videos play like cable: a channel's video only loads while you're tuned to it, and it starts at the spot a shared "broadcast clock" says it should be at (same for every visitor), looping when it ends. The **VOL** knob cycles MUTE / 1 / 2 / 3 and is remembered per browser.

- **YouTube:** controlled through YouTube's player API.
- **Archive.org:** the admin panel looks up the film's MP4 file on archive.org when you add it (📡 live). Items without a file use archive.org's own player (no sync); click **Make live** to fix them.

## Backups

- **On Render:** every save keeps a copy of the previous lineup in `/data/backups/` (newest 30). Restore or download them from the **Backups** section in `/admin`.
- **Off-site:** a GitHub Action saves the live lineup nightly to the `schedule-backups` branch. Its history is a dated record of every change. To use one, download `schedule.json` from that branch (History → pick a date) and use **Restore from a file** in `/admin`.
- **Crash-safe:** saves are written to a temp file and swapped in, and if the live file is ever damaged the site serves the newest good backup.

## schedule.sample.json

An example of the schedule format, kept for reference only. **The live site never reads it.** Changing it does nothing to the site.

## Settings on Render (Environment)

| Variable | What it's for |
|---|---|
| `SECRET_KEY` | Signs the admin login cookie. Required; the app won't start without it. |
| `ADMIN_PASSWORD` | Password for `/admin`. |
| `CORS_ORIGINS` | Optional. Comma-separated sites allowed to load the schedule. Defaults to warrencbennett.com. |

## GitHub secret

| Secret | What it's for |
|---|---|
| `NEOCITIES_API_TOKEN` | Lets the GitHub Action upload `index.html` to Neocities. |

# Sydney Property Scanner

Runs your search brief against real Domain API data on a schedule, scores results,
and posts new matches to a webhook (Discord/Slack/ntfy). Dashboard reads the same
data file.

## Setup (one-time, ~15 minutes)

1. **Domain API**: sign up at https://developer.domain.com.au, create a Project,
   copy the Client ID and Client Secret.
2. **Create a GitHub repo** and push this folder to it.
3. **Add repo secrets** (Settings → Secrets and variables → Actions):
   - `DOMAIN_CLIENT_ID`
   - `DOMAIN_CLIENT_SECRET`
   - `WEBHOOK_URL` (a Discord/Slack incoming webhook URL, or an ntfy.sh topic URL — free, no signup: pick a unique topic name and use `https://ntfy.sh/your-topic-name`)
4. The workflow in `.github/workflows/sweep.yml` runs daily at 7am Sydney time
   (adjust the cron line for your preference) and:
   - calls the Domain API for each suburb/type in `config/search_areas.json`
   - filters + scores against `config/brief.json`
   - writes `data/listings.json`
   - posts anything new since the last run to your webhook
   - commits the updated data file back to the repo
5. **Dashboard**: enable GitHub Pages (Settings → Pages → deploy from
   `dashboard/` folder after building — see `dashboard/README.md`) or open
   `dashboard/Dashboard.jsx` as a Claude artifact pointed at the raw JSON URL.

## Editing your brief

Edit `config/brief.json` — cap, bed range, parking requirement, scarcity
threshold, transit minutes. Edit `config/search_areas.json` to add/remove
suburbs. Commit; next scheduled run picks it up. No code changes needed.

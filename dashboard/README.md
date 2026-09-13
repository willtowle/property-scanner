# Dashboard

A small Vite + React app. Locally: `npm install && npm run dev`.

## Deploying (free, on GitHub Pages)

1. In your repo: Settings → Pages → Source: "GitHub Actions".
2. Edit `vite.config.js`'s `base` to match your repo name if you're deploying
   to `username.github.io/repo-name` (leave as `'./'` if using a custom
   domain or the repo IS your `username.github.io` root repo).
3. Push to `main` — the `deploy-pages.yml` workflow builds and publishes
   automatically. The `sweep.yml` workflow commits fresh data daily, which
   the dashboard fetches at `./data/listings.json` on each page load — no
   rebuild needed for new data, just a page refresh.

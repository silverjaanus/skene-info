# skene.info

A small, curated, non-commercial calendar of Estonia's underground / alternative
music scene — concerts, festivals, club nights, releases and merch drops. Every
entry links back to its original source, so visitors can go straight to the
organiser, venue or band.

Live:

- **[www.skene.info](https://www.skene.info)** — guitar-based alternative music
  (metal, rock, punk and subgenres) plus dark-electro / industrial. Mostly
  Estonia, with major Baltic / Nordic / European events on top.
- **[rap.skene.info](https://rap.skene.info)** — Estonian hip-hop / rap scene.
  Stays Estonia-focused. Technically a sub-site of the same project (`/rap/*`).

## Stack

No framework, no build step — intentionally lightweight.

- **Frontend:** plain static HTML + CSS + vanilla JS. All UI logic (genre
  filters, ET/EN language toggle, rotating logo) is inline. No React/Vue.
- **Data:** version-controlled JSON. Curated entries live in `data/manual.json`
  (and `rap/data/manual.json`); Python scripts generate the served
  `data/data.json` and an accumulating archive.
- **Scripts:** Python 3.11+ (`fetch.py`, `fetch_rap.py`, `archive_split.py`,
  `make_weekly_image.py` using Pillow). Minimal dependencies.
- **Hosting:** Vercel (static). Two sites from one repo via host-based routing
  in `vercel.json` (`rap.skene.info` → `/rap/*`).
- **Automation:** a daily GitHub Actions cron (`.github/workflows/update.yml`)
  runs the fetch scripts and commits any data changes.

## Repository layout

```
index.html, arhiiv.html, changelog.html   # main site (www)
rap/                                       # rap sub-site (same structure)
data/
  manual.json      # curated entries — the source of truth for edits
  data.json        # generated: upcoming + featured entries
  archive/         # generated: accumulating past events, by year
  blocklist.json   # exclusions
sweep/sources.json # FB/IG pages and sites reviewed for new entries
scripts/           # Python data-generation scripts
vercel.json        # host routing for the two sites
```

## Running locally

Serve the folder statically and run the fetch script to (re)generate data:

```bash
python scripts/fetch.py        # regenerates data/data.json + archive
python scripts/fetch_rap.py    # same for the rap sub-site
python -m http.server 8899     # then open http://localhost:8899
```

`make_weekly_image.py` additionally needs Pillow (`pip install pillow`).

## Data & attribution

Event data is aggregated from third-party sources (organisers, venues, ticket
sellers). Every entry cites its origin, and the goal is to send traffic to those
sources rather than replace them. The MIT license below covers the **code**;
event listings belong to their respective organisers and are used for
informational, non-commercial linking.

## Contributing

Spotted a missing event, a wrong date, or a source worth adding? There's a
contact form on the site, or open an issue / pull request here.

## License

[MIT](LICENSE) © 2026 Silver Jaanus

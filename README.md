# Backlink Builder

A consent-first backlink opportunity builder. Provide a website URL and the tool produces a prioritized outreach plan with relevant backlink opportunities, personalized pitch angles, and CSV/JSON exports.

This project intentionally avoids spammy automated posting. It helps you find and organize ethical backlink campaigns; a human should review every prospect and send outreach only where it is relevant and allowed.

## GUI usage

Launch the desktop interface:

```bash
python -m backlink_builder --gui
```

The GUI has two primary inputs:

1. **Website link** — the site you want to build backlinks for.
2. **Backlink sites file** — an optional `.txt` or `.csv` attachment containing backlinking sites to review, one per line or comma-separated.

Click **Start Link Building Check** to generate the exports in the selected output folder. While it runs, the progress table shows each imported backlink site as **Made / working** or **Not working / dead** and displays a clickable verification link for each working backlink site so you can open it and confirm the placement.

## CLI usage

```bash
python -m backlink_builder https://example.com --keyword "example keyword" --sites-file backlink-sites.txt --out exports
```

Outputs:

- `exports/opportunities.csv` — scored backlink opportunities.
- `exports/opportunities.json` — machine-readable campaign data.
- `exports/outreach.md` — editable outreach templates.
- `exports/link_progress.csv` — reachability progress for attached backlink sites, showing which are working, which are dead/not working, and the verification URL to click for working links.

## Development

```bash
python -m pytest
```

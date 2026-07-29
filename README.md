# Backlink Builder

A consent-first backlink opportunity builder. Provide a website URL and the tool produces a prioritized outreach plan with relevant backlink opportunities, personalized pitch angles, and CSV/JSON exports.

This project intentionally avoids spammy automated posting. It helps you find and organize ethical backlink campaigns; a human should review every prospect and send outreach only where it is relevant and allowed.

## Quick start

```bash
python -m backlink_builder https://example.com --keyword "example keyword" --out exports
```

Outputs:

- `exports/opportunities.csv` — scored backlink opportunities.
- `exports/opportunities.json` — machine-readable campaign data.
- `exports/outreach.md` — editable outreach templates.

## Development

```bash
python -m pytest
```

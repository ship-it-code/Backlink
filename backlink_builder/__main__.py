from __future__ import annotations

import argparse

from .core import build_campaign, write_exports


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a consent-first backlink outreach plan.")
    parser.add_argument("website", help="Website URL to promote")
    parser.add_argument("--keyword", action="append", default=[], help="Target keyword; can be repeated")
    parser.add_argument("--out", default="exports", help="Directory for CSV, JSON, and outreach exports")
    args = parser.parse_args()

    campaign = build_campaign(args.website, args.keyword)
    paths = write_exports(campaign, args.out)
    print(f"Created {len(campaign.opportunities)} backlink opportunities for {campaign.domain}.")
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()

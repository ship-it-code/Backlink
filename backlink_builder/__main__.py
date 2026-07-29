from __future__ import annotations

import argparse

from .core import audit_backlink_sites, build_campaign, load_backlink_sites, write_exports
from .gui import main as gui_main


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a consent-first backlink outreach plan.")
    parser.add_argument("website", nargs="?", help="Website URL to promote")
    parser.add_argument("--keyword", action="append", default=[], help="Target keyword; can be repeated")
    parser.add_argument("--sites-file", help="Text or CSV file containing backlink sites to include")
    parser.add_argument("--out", default="exports", help="Directory for CSV, JSON, and outreach exports")
    parser.add_argument("--gui", action="store_true", help="Launch the desktop GUI")
    args = parser.parse_args()

    if args.gui or not args.website:
        gui_main()
        return

    backlink_sites = load_backlink_sites(args.sites_file)
    campaign = build_campaign(args.website, args.keyword, backlink_sites)
    paths = write_exports(campaign, args.out)
    print(f"Created {len(campaign.opportunities)} backlink opportunities for {campaign.domain}.")
    for status in audit_backlink_sites(backlink_sites):
        display_status = "Made / working" if status.link_made else "Not working / dead"
        print(f"{display_status}: {status.site} ({status.detail})")
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()

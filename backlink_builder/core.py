from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.parse import urlparse
import csv
import json
import re


@dataclass(frozen=True)
class Opportunity:
    """A backlink prospect that requires human review before outreach."""

    kind: str
    target: str
    angle: str
    score: int
    next_step: str


@dataclass(frozen=True)
class BacklinkCampaign:
    website: str
    domain: str
    keywords: tuple[str, ...]
    opportunities: tuple[Opportunity, ...]

    def to_dict(self) -> dict:
        return {
            "website": self.website,
            "domain": self.domain,
            "keywords": list(self.keywords),
            "opportunities": [asdict(item) for item in self.opportunities],
        }


def normalize_url(url: str) -> str:
    """Return a URL with a scheme and a network location."""
    candidate = url.strip()
    if not candidate:
        raise ValueError("website URL is required")
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", candidate):
        candidate = f"https://{candidate}"
    parsed = urlparse(candidate)
    if not parsed.netloc or "." not in parsed.netloc:
        raise ValueError(f"invalid website URL: {url}")
    return candidate.rstrip("/")


def extract_domain(url: str) -> str:
    parsed = urlparse(normalize_url(url))
    return parsed.netloc.lower().removeprefix("www.")


def default_keywords(domain: str) -> tuple[str, ...]:
    stem = domain.split(".")[0].replace("-", " ")
    return (stem, f"{stem} resources", f"{stem} guide")


def build_campaign(website: str, keywords: list[str] | None = None) -> BacklinkCampaign:
    """Build an ethical backlink campaign from a website and optional keywords."""
    normalized = normalize_url(website)
    domain = extract_domain(normalized)
    selected_keywords = tuple(k.strip() for k in (keywords or []) if k.strip()) or default_keywords(domain)
    primary = selected_keywords[0]

    opportunities = (
        Opportunity(
            kind="Resource page outreach",
            target=f"Search: {primary} + resources + submit",
            angle=f"Suggest {domain} as a useful addition where it genuinely helps readers researching {primary}.",
            score=92,
            next_step="Review each resource page manually and contact only pages that accept relevant suggestions.",
        ),
        Opportunity(
            kind="Guest contribution",
            target=f"Search: {primary} + write for us",
            angle=f"Pitch an original article backed by expertise from {domain}; avoid duplicate or thin content.",
            score=86,
            next_step="Verify editorial guidelines and pitch a unique outline before writing the post.",
        ),
        Opportunity(
            kind="Broken link replacement",
            target=f"Search: {primary} + links + 404",
            angle=f"Offer {normalized} only when it is a close, high-quality replacement for a dead reference.",
            score=81,
            next_step="Use a crawler or browser extension to confirm the broken link and document the replacement fit.",
        ),
        Opportunity(
            kind="Unlinked brand mention",
            target=f"Search: \"{domain}\" -site:{domain}",
            angle="Ask publishers who already mention the brand to add a citation link if it improves attribution.",
            score=78,
            next_step="Confirm the mention exists, then send a concise attribution request.",
        ),
        Opportunity(
            kind="Partner/vendor listings",
            target="Existing customers, integrations, vendors, associations, and local directories",
            angle=f"Request inclusion on legitimate partner pages where there is an existing relationship with {domain}.",
            score=74,
            next_step="Compile real relationships first; do not submit to unrelated low-quality directories.",
        ),
    )
    return BacklinkCampaign(normalized, domain, selected_keywords, opportunities)


def write_exports(campaign: BacklinkCampaign, output_dir: str | Path) -> list[Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "opportunities.json"
    csv_path = out / "opportunities.csv"
    md_path = out / "outreach.md"

    json_path.write_text(json.dumps(campaign.to_dict(), indent=2) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["kind", "target", "angle", "score", "next_step"])
        writer.writeheader()
        for opportunity in campaign.opportunities:
            writer.writerow(asdict(opportunity))
    md_path.write_text(render_outreach(campaign), encoding="utf-8")
    return [json_path, csv_path, md_path]


def render_outreach(campaign: BacklinkCampaign) -> str:
    lines = [f"# Outreach drafts for {campaign.domain}", ""]
    for item in campaign.opportunities:
        lines.extend([
            f"## {item.kind}",
            "",
            "Subject: Useful resource for your readers",
            "",
            "Hi {{first_name}},",
            "",
            f"I found your page while researching {campaign.keywords[0]}. {item.angle}",
            "",
            f"Potential URL: {campaign.website}",
            "",
            "If it is not a fit, no worries at all.",
            "",
            "Best,",
            "{{sender_name}}",
            "",
        ])
    return "\n".join(lines)

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from zipfile import ZIP_DEFLATED, ZipFile
import csv
import json
import re
import xml.sax.saxutils as xml_utils


@dataclass(frozen=True)
class Opportunity:
    """A backlink prospect that requires human review before outreach."""

    kind: str
    target: str
    angle: str
    score: int
    next_step: str


@dataclass(frozen=True)
class LinkStatus:
    """Live status for an imported backlink site during campaign building."""

    site: str
    status: str
    detail: str
    link_made: bool
    verify_url: str


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


def load_backlink_sites(path: str | Path | None) -> tuple[str, ...]:
    """Load optional backlink prospect URLs/domains from a text or CSV file."""
    if not path:
        return ()

    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"backlink sites file not found: {source}")

    sites: list[str] = []
    for raw_line in source.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        for token in line.split(","):
            candidate = token.strip()
            if not candidate or candidate.lower() in {"url", "site", "domain", "website"}:
                continue
            sites.append(normalize_url(candidate))

    return tuple(dict.fromkeys(sites))


def check_site_status(site: str, timeout: float = 8.0, opener=urlopen) -> LinkStatus:
    """Check whether an imported backlink site is reachable before outreach work starts."""
    normalized = normalize_url(site)
    try:
        code = _request_status(normalized, "HEAD", timeout, opener)
    except HTTPError as exc:
        if exc.code in {403, 405}:
            try:
                code = _request_status(normalized, "GET", timeout, opener)
            except HTTPError as get_exc:
                code = get_exc.code
            except (TimeoutError, URLError, OSError) as get_exc:
                return LinkStatus(normalized, "dead", str(get_exc), False, "")
        else:
            code = exc.code
    except (TimeoutError, URLError, OSError) as exc:
        return LinkStatus(normalized, "dead", str(exc), False, "")

    if 200 <= int(code) < 400:
        return LinkStatus(normalized, "working", f"HTTP {code}", True, normalized)
    return LinkStatus(normalized, "not working", f"HTTP {code}", False, "")


def _request_status(site: str, method: str, timeout: float, opener) -> int:
    request = Request(site, method=method, headers={"User-Agent": "BacklinkBuilder/1.0"})
    response = opener(request, timeout=timeout)
    return int(getattr(response, "status", getattr(response, "code", 200)))


def audit_backlink_sites(sites: list[str] | tuple[str, ...], timeout: float = 8.0, opener=urlopen) -> tuple[LinkStatus, ...]:
    """Return progress statuses for every imported backlink site."""
    return tuple(check_site_status(site, timeout=timeout, opener=opener) for site in sites)


def build_campaign(
    website: str,
    keywords: list[str] | None = None,
    backlink_sites: list[str] | tuple[str, ...] | None = None,
) -> BacklinkCampaign:
    """Build an ethical backlink campaign from a website, keywords, and optional prospect sites."""
    normalized = normalize_url(website)
    domain = extract_domain(normalized)
    selected_keywords = tuple(k.strip() for k in (keywords or []) if k.strip()) or default_keywords(domain)
    primary = selected_keywords[0]

    opportunities = [
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
    ]

    for site in backlink_sites or ():
        prospect = normalize_url(site)
        prospect_domain = extract_domain(prospect)
        opportunities.append(
            Opportunity(
                kind="Imported backlink site",
                target=prospect,
                angle=f"Evaluate whether {prospect_domain} has a relevant placement where linking to {domain} would help readers.",
                score=70,
                next_step="Manually review the site rules and submit/contact only if backlinks are allowed and contextually useful.",
            )
        )

    return BacklinkCampaign(normalized, domain, selected_keywords, tuple(opportunities))


def write_exports(campaign: BacklinkCampaign, output_dir: str | Path) -> list[Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "opportunities.json"
    csv_path = out / "opportunities.csv"
    md_path = out / "outreach.md"
    progress_path = out / "link_progress.csv"
    excel_path = out / "backlinks.xlsx"

    json_path.write_text(json.dumps(campaign.to_dict(), indent=2) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["kind", "target", "angle", "score", "next_step"])
        writer.writeheader()
        for opportunity in campaign.opportunities:
            writer.writerow(asdict(opportunity))
    md_path.write_text(render_outreach(campaign), encoding="utf-8")
    imported_sites = [item.target for item in campaign.opportunities if item.kind == "Imported backlink site"]
    link_statuses = audit_backlink_sites(imported_sites)
    with progress_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["site", "status", "detail", "link_made", "verify_url"])
        writer.writeheader()
        for status in link_statuses:
            writer.writerow(asdict(status))
    write_excel_export(campaign, link_statuses, excel_path)
    return [json_path, csv_path, md_path, progress_path, excel_path]


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


def write_excel_export(campaign: BacklinkCampaign, statuses: tuple[LinkStatus, ...], output_path: str | Path) -> Path:
    """Write an Excel workbook containing website links and backlink verification links."""
    path = Path(output_path)
    headers = ["Website Link", "Backlink Site", "Status", "Backlink Verification Link", "Detail", "Link Made"]
    rows = [headers]
    if statuses:
        for status in statuses:
            rows.append([
                campaign.website,
                status.site,
                status.status,
                status.verify_url,
                status.detail,
                "Yes" if status.link_made else "No",
            ])
    else:
        rows.append([campaign.website, "No backlink sites attached", "skipped", "", "Only default opportunities created", "No"])

    hyperlinks = []
    for row_index, row in enumerate(rows[1:], start=2):
        hyperlinks.append((f"A{row_index}", row[0]))
        if row[3]:
            hyperlinks.append((f"D{row_index}", row[3]))

    with ZipFile(path, "w", ZIP_DEFLATED) as workbook:
        workbook.writestr("[Content_Types].xml", _xlsx_content_types())
        workbook.writestr("_rels/.rels", _xlsx_root_relationships())
        workbook.writestr("xl/workbook.xml", _xlsx_workbook())
        workbook.writestr("xl/_rels/workbook.xml.rels", _xlsx_workbook_relationships())
        workbook.writestr("xl/worksheets/sheet1.xml", _xlsx_sheet(rows, hyperlinks))
        workbook.writestr("xl/worksheets/_rels/sheet1.xml.rels", _xlsx_sheet_relationships(hyperlinks))
    return path


def _xlsx_content_types() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>
"""


def _xlsx_root_relationships() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
"""


def _xlsx_workbook() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="Backlinks" sheetId="1" r:id="rId1"/></sheets>
</workbook>
"""


def _xlsx_workbook_relationships() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>
"""


def _xlsx_sheet(rows: list[list[str]], hyperlinks: list[tuple[str, str]]) -> str:
    row_xml = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for column_index, value in enumerate(row, start=1):
            ref = f"{_xlsx_column_name(column_index)}{row_index}"
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{xml_utils.escape(str(value))}</t></is></c>')
        row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    hyperlink_xml = ""
    if hyperlinks:
        links = [f'<hyperlink ref="{cell}" r:id="rId{index}"/>' for index, (cell, _) in enumerate(hyperlinks, start=1)]
        hyperlink_xml = f'<hyperlinks>{"".join(links)}</hyperlinks>'

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheetData>' + "".join(row_xml) + '</sheetData>' + hyperlink_xml + '</worksheet>'
    )


def _xlsx_sheet_relationships(hyperlinks: list[tuple[str, str]]) -> str:
    relationships = [
        '<Relationship Id="rId{index}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" '
        'Target="{target}" TargetMode="External"/>'.format(index=index, target=xml_utils.escape(target))
        for index, (_, target) in enumerate(hyperlinks, start=1)
    ]
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(relationships)
        + '</Relationships>'
    )


def _xlsx_column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name

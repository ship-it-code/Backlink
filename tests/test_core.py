import json
from zipfile import ZipFile

import pytest

from backlink_builder.core import audit_backlink_sites, build_campaign, load_backlink_sites, normalize_url, write_exports


class FakeResponse:
    status = 204


def fake_working_opener(request, timeout):
    return FakeResponse()


def test_normalize_url_adds_https():
    assert normalize_url("example.com") == "https://example.com"


def test_normalize_url_rejects_invalid_input():
    with pytest.raises(ValueError):
        normalize_url("not-a-domain")


def test_load_backlink_sites_supports_text_and_csv(tmp_path):
    source = tmp_path / "sites.csv"
    source.write_text("url\nexample.org, https://partner.test/page\n# comment\nexample.org\n")
    assert load_backlink_sites(source) == ("https://example.org", "https://partner.test/page")


def test_audit_backlink_sites_marks_working_sites():
    statuses = audit_backlink_sites(["example.org"], opener=fake_working_opener)
    assert statuses[0].site == "https://example.org"
    assert statuses[0].status == "working"
    assert statuses[0].link_made is True
    assert statuses[0].verify_url == "https://example.org"


def test_build_campaign_creates_scored_opportunities():
    campaign = build_campaign("https://www.example.com", ["technical seo"])
    assert campaign.domain == "example.com"
    assert campaign.keywords == ("technical seo",)
    assert len(campaign.opportunities) >= 5
    assert campaign.opportunities[0].score >= campaign.opportunities[-1].score


def test_build_campaign_includes_imported_backlink_sites():
    campaign = build_campaign("example.com", backlink_sites=["directory.example"])
    imported = campaign.opportunities[-1]
    assert imported.kind == "Imported backlink site"
    assert imported.target == "https://directory.example"


def test_write_exports(tmp_path):
    campaign = build_campaign("example.com")
    paths = write_exports(campaign, tmp_path)
    assert {path.name for path in paths} == {
        "opportunities.json",
        "opportunities.csv",
        "outreach.md",
        "link_progress.csv",
        "backlinks.xlsx",
    }
    data = json.loads((tmp_path / "opportunities.json").read_text())
    assert data["domain"] == "example.com"
    assert "verify_url" in (tmp_path / "link_progress.csv").read_text()
    with ZipFile(tmp_path / "backlinks.xlsx") as workbook:
        sheet = workbook.read("xl/worksheets/sheet1.xml").decode()
    assert "Website Link" in sheet
    assert "Backlink Verification Link" in sheet

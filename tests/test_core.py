import json

import pytest

from backlink_builder.core import build_campaign, load_backlink_sites, normalize_url, write_exports


def test_normalize_url_adds_https():
    assert normalize_url("example.com") == "https://example.com"


def test_normalize_url_rejects_invalid_input():
    with pytest.raises(ValueError):
        normalize_url("not-a-domain")


def test_load_backlink_sites_supports_text_and_csv(tmp_path):
    source = tmp_path / "sites.csv"
    source.write_text("url\nexample.org, https://partner.test/page\n# comment\nexample.org\n")
    assert load_backlink_sites(source) == ("https://example.org", "https://partner.test/page")


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
    assert {path.name for path in paths} == {"opportunities.json", "opportunities.csv", "outreach.md"}
    data = json.loads((tmp_path / "opportunities.json").read_text())
    assert data["domain"] == "example.com"

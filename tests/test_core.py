import json

import pytest

from backlink_builder.core import build_campaign, extract_domain, normalize_url, write_exports


def test_normalize_url_adds_https():
    assert normalize_url("example.com") == "https://example.com"


def test_normalize_url_rejects_invalid_input():
    with pytest.raises(ValueError):
        normalize_url("not-a-domain")


def test_build_campaign_creates_scored_opportunities():
    campaign = build_campaign("https://www.example.com", ["technical seo"])
    assert campaign.domain == "example.com"
    assert campaign.keywords == ("technical seo",)
    assert len(campaign.opportunities) >= 5
    assert campaign.opportunities[0].score >= campaign.opportunities[-1].score


def test_write_exports(tmp_path):
    campaign = build_campaign("example.com")
    paths = write_exports(campaign, tmp_path)
    assert {path.name for path in paths} == {"opportunities.json", "opportunities.csv", "outreach.md"}
    data = json.loads((tmp_path / "opportunities.json").read_text())
    assert data["domain"] == "example.com"

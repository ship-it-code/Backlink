"""Consent-first backlink opportunity builder."""

from .core import BacklinkCampaign, LinkStatus, audit_backlink_sites, build_campaign, load_backlink_sites

__all__ = ["BacklinkCampaign", "LinkStatus", "audit_backlink_sites", "build_campaign", "load_backlink_sites"]

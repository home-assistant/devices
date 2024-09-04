"""Utility functions for Home Assistant."""

import httpx


def integrations_info():
    return httpx.get("https://www.home-assistant.io/integrations.json").json()

"""Validation helpers."""

from typing import Any, Callable

import voluptuous as vol


def has_at_least_one_key(*keys: Any) -> Callable[[dict], dict]:
    """Validate that at least one key exists."""
    key_set = set(keys)

    def validate(obj: dict) -> dict:
        """Test keys exist in dict."""
        if not isinstance(obj, dict):
            raise vol.Invalid("expected dictionary")

        if not key_set.isdisjoint(obj):
            return obj
        expected = ", ".join(str(k) for k in keys)
        raise vol.Invalid(f"must contain at least one of {expected}.")

    return validate


def str_or_none(value):
    if value == "None":
        return None
    return value


def bool(value):
    return value == "True"

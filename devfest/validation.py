"""Validation helpers."""


def str_or_none(value):
    if value == "None":
        return None
    return value


def bool(value):
    return value == "True"

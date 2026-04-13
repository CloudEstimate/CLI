from __future__ import annotations

from urllib.parse import urlencode

def encode_estimate_share_state(state: dict[str, str | bool]) -> str:
    return "__".join(
        [
            f"size-{state['size']}",
            f"ha-{'true' if state['ha'] else 'false'}",
            f"term-{state['term']}",
            f"region-{state['region']}"
        ]
    )


def decode_estimate_share_state(token: str) -> dict[str, str | bool]:
    parts = dict(
        part.split("-", 1)
        for part in token.split("__")
        if "-" in part
    )
    return {
        "size": parts.get("size", "m"),
        "ha": parts.get("ha") == "true",
        "term": parts.get("term", "on-demand"),
        "region": parts.get("region", "")
    }


def encode_compare_share_state(state: dict[str, str | bool]) -> str:
    return "__".join(
        [
            f"size-{state['size']}",
            f"ha-{'true' if state['ha'] else 'false'}",
            f"term-{state['term']}"
        ]
    )


def decode_compare_share_state(token: str) -> dict[str, str | bool]:
    parts = dict(
        part.split("-", 1)
        for part in token.split("__")
        if "-" in part
    )
    return {
        "size": parts.get("size", "m"),
        "ha": parts.get("ha") == "true",
        "term": parts.get("term", "on-demand")
    }


def build_estimate_query(state: dict[str, str | bool]) -> str:
    return urlencode(
        {
            "size": state["size"],
            "ha": str(state["ha"]).lower(),
            "term": state["term"],
            "region": state["region"]
        }
    )


def build_estimate_share_path(
    slug: str,
    cloud: str,
    state: dict[str, str | bool]
) -> str:
    return f"/share/{slug}/{cloud}/{encode_estimate_share_state(state)}"


def build_compare_share_path(
    slug: str,
    state: dict[str, str | bool]
) -> str:
    return f"/share/{slug}/compare/{encode_compare_share_state(state)}"

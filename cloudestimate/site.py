from __future__ import annotations

import os
from typing import Literal

site_config = {
    "name": "CloudEstimate",
    "description": "A worked example of the Precomputed AI design pattern for reference-architecture-based cloud sizing and monthly cost estimates.",
    "precomputed_ai": {
        "name": "Precomputed AI",
        "url": "https://precomputedai.com",
        "citation": "Raquedan, R. (2026). Precomputed AI: Reason Ahead of Time, Serve Instantly."
    }
}

cloud_meta = {
    "gcp": {
        "slug": "gcp",
        "name": "Google Cloud",
        "short_name": "Google Cloud",
        "accent": "#575d8d",
        "default_region": "us-central1",
        "calculator_label": "Google Cloud Pricing Calculator",
        "calculator_url": "https://cloud.google.com/products/calculator"
    },
    "aws": {
        "slug": "aws",
        "name": "AWS",
        "short_name": "AWS",
        "accent": "#b78d16",
        "default_region": "us-east-1",
        "calculator_label": "AWS Pricing Calculator",
        "calculator_url": "https://calculator.aws"
    },
    "azure": {
        "slug": "azure",
        "name": "Azure",
        "short_name": "Azure",
        "accent": "#7d82b8",
        "default_region": "eastus",
        "calculator_label": "Azure Pricing Calculator",
        "calculator_url": "https://azure.microsoft.com/pricing/calculator/"
    }
}

cloud_order = ("gcp", "aws", "azure")
size_order = ("xs", "s", "m", "l", "xl")
term_order = ("on-demand", "1yr", "3yr")

CloudSlug = Literal["gcp", "aws", "azure"]
SizeSlug = Literal["xs", "s", "m", "l", "xl"]
CommitmentTerm = Literal["on-demand", "1yr", "3yr"]


def get_base_url() -> str | None:
    value = os.environ.get("CLOUDESTIMATE_BASE_URL") or os.environ.get("PUBLIC_SITE_URL")
    if not value:
        return None
    return value.rstrip("/")

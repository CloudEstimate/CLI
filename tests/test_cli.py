from __future__ import annotations

import json

from click.testing import CliRunner

from cloudestimate.cli import cli
from cloudestimate.data import get_isv, load_isv_catalog, load_pricing_cache, load_shape_mappings
from cloudestimate.engine import (
    build_compare_view,
    build_estimate,
    get_pricing_caches,
    resolve_compare_state,
    resolve_estimate_state,
)
from cloudestimate.terraform import build_gcp_terraform_snippet


def test_catalog_loading_counts_supported_isvs():
    catalog = load_isv_catalog()
    slugs = {entry.slug for entry in catalog}

    assert len(catalog) == 24
    assert "gitlab" in slugs
    assert "minio" in slugs


def test_list_json_reports_the_catalog():
    runner = CliRunner()
    result = runner.invoke(cli, ["list", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["count"] == 24
    assert any(item["slug"] == "gitlab" for item in payload["items"])


def test_estimate_json_uses_web_defaults():
    runner = CliRunner()
    result = runner.invoke(cli, ["estimate", "gitlab", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)

    assert payload["state"]["cloud"] == "gcp"
    assert payload["state"]["region"] == "us-central1"
    assert payload["estimate"]["monthly_total"] == 671.22
    assert payload["share_path"] == "/share/gitlab/gcp/size-xs__ha-false__term-on-demand__region-us-central1"
    assert "google_compute_instance" in payload["terraform_snippet"]


def test_compare_json_ranks_aws_as_lowest_for_gitlab():
    runner = CliRunner()
    result = runner.invoke(cli, ["compare", "gitlab", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)

    assert payload["view"]["cheapest_cloud"] == "aws"
    assert payload["view"]["estimates"]["aws"]["monthly_total"] == 463.38
    assert payload["open_estimates"][0]["url"].startswith("/sizing/gitlab/")


def test_terraform_snippet_formats_integer_disks():
    isv = get_isv("gitlab")
    pricing_cache = load_pricing_cache("gcp")
    state = resolve_estimate_state(isv, pricing_cache, "gcp", size="xs")
    estimate = build_estimate(isv, state, pricing_cache, load_shape_mappings())
    snippet = build_gcp_terraform_snippet(isv.slug, state.region, estimate.components)

    assert "size  = 200" in snippet
    assert "size  = 250" in snippet


def test_compare_view_matches_estimate_ranking():
    isv = get_isv("gitlab")
    state = resolve_compare_state(isv, size="xs")
    view = build_compare_view(isv, state, get_pricing_caches(), load_shape_mappings())

    assert view.cheapest_cloud == "aws"
    assert view.regions["gcp"] == "us-central1"
    assert view.estimates["azure"].monthly_total > 0

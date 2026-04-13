from __future__ import annotations

import json
from dataclasses import asdict

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from cloudestimate.data import get_isv, load_isv_catalog, load_pricing_cache, load_shape_mappings
from cloudestimate.engine import (
    build_compare_explanation,
    build_compare_view,
    build_estimate,
    build_sizing_explanation,
    get_pricing_caches,
    pick_default_region,
    resolve_compare_state,
    resolve_estimate_state,
    summarize_components
)
from cloudestimate.formatting import format_currency, format_date, format_rounded_annual, format_role_label, format_storage, format_user_range
from cloudestimate.share import build_compare_share_path, build_estimate_query, build_estimate_share_path
from cloudestimate.site import cloud_meta, cloud_order, get_base_url, term_order, size_order
from cloudestimate.terraform import build_gcp_terraform_snippet

console = Console()
CATEGORY_CHOICES = ("devops-platform", "data-store", "search", "streaming", "artifact-repo", "identity", "other")
NOT_MODELLED = (
    "Vendor licensing and support",
    "Professional services",
    "Network egress",
    "Compliance controls",
    "Backup storage",
    "Monitoring"
)


@click.group(context_settings={"allow_extra_args": True, "ignore_unknown_options": True}, invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """CloudEstimate CLI.

    Use `cloudestimate estimate <isv>` for a single-cloud estimate, `cloudestimate compare <isv>`
    for a cross-cloud comparison, or `cloudestimate list` to browse the catalog.
    """

    if ctx.invoked_subcommand is not None:
        return

    click.echo(ctx.get_help())


@cli.command(name="list")
@click.option("--query", default="", help="Filter by ISV name, vendor, slug, or description.")
@click.option(
    "--category",
    type=click.Choice(CATEGORY_CHOICES, case_sensitive=False),
    default=None,
    help="Filter by ISV category."
)
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON.")
def list_cmd(query, category, as_json):
    """List the supported ISVs in the catalog."""

    catalog = sorted(load_isv_catalog(), key=lambda entry: entry.name.lower())
    filtered = [
        entry
        for entry in catalog
        if _matches_filter(entry, query, category)
    ]

    if as_json:
        payload = {
            "count": len(filtered),
            "items": [
                _isv_payload(entry)
                for entry in filtered
            ]
        }
        click.echo(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
        return

    title = Text("Supported ISVs", style="bold")
    console.print(Panel(title, subtitle=f"{len(filtered)} workloads encoded from public reference architectures", border_style="blue"))

    table = Table(box=box.SIMPLE_HEAVY, show_lines=False, expand=True)
    table.add_column("ISV", style="bold", overflow="fold")
    table.add_column("Vendor", overflow="fold")
    table.add_column("Category")
    table.add_column("Sizes")
    for cloud in cloud_order:
        table.add_column(cloud_meta[cloud]["name"], justify="center")

    for entry in filtered:
        sizes = ", ".join(size.upper() for size in size_order if size in entry.sizes)
        row_style = None
        table.add_row(
            entry.name,
            entry.vendor,
            entry.category,
            sizes,
            *(["Yes"] * len(cloud_order)),
            style=row_style
        )

    if not filtered:
        console.print("No ISVs matched the current filter.")
        return

    console.print(table)


@cli.command(name="estimate")
@click.argument("isv_slug")
@click.option("--cloud", type=click.Choice(cloud_order, case_sensitive=False), default="gcp", show_default=True)
@click.option("--size", type=click.Choice(size_order, case_sensitive=False), default=None, help="Size tier to estimate.")
@click.option("--ha/--no-ha", default=False, show_default=True, help="Toggle high availability overhead.")
@click.option("--term", type=click.Choice(term_order, case_sensitive=False), default="on-demand", show_default=True)
@click.option("--region", default=None, help="Override the default region for the selected cloud.")
@click.option("--base-url", default=None, help="Base URL used to build share links.")
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON.")
def estimate_cmd(isv_slug, cloud, size, ha, term, region, base_url, as_json):
    """Estimate the monthly and annual cost for one ISV on one cloud."""

    isv = _get_isv_or_fail(isv_slug)
    pricing_cache = load_pricing_cache(cloud)
    _validate_size_choice(isv, size)
    _validate_region_choice(pricing_cache, region)

    state = resolve_estimate_state(isv, pricing_cache, cloud, size=size, ha=ha, term=term, region=region)
    estimate = build_estimate(isv, state, pricing_cache, load_shape_mappings())
    explanation = build_sizing_explanation(isv, cloud, state, estimate)
    share_state = {"size": state.size, "ha": state.ha, "term": state.term, "region": state.region}
    base_url = _resolve_base_url(base_url)
    current_url = _build_estimate_url(base_url, isv.slug, cloud, share_state)
    share_url = _build_share_url(base_url, build_estimate_share_path(isv.slug, cloud, share_state))
    compare_url = _build_compare_url(base_url, isv.slug, {"size": state.size, "ha": state.ha, "term": state.term})
    related_views = [
        {
            "label": f"View on {cloud_meta[target_cloud]['name']}",
            "url": _build_estimate_url(
                base_url,
                isv.slug,
                target_cloud,
                {"size": state.size, "ha": state.ha, "term": state.term, "region": pick_default_region(load_pricing_cache(target_cloud), cloud_meta[target_cloud]["default_region"])}
            )
        }
        for target_cloud in cloud_order
        if target_cloud != cloud
    ]
    related_views.append(
        {
            "label": "Compare all three",
            "url": compare_url
        }
    )
    terraform_snippet = build_gcp_terraform_snippet(
        slug=isv.slug,
        region=state.region,
        components=estimate.components,
        comment_label=cloud_meta[cloud]["name"]
    ) if cloud == "gcp" else None

    payload = _estimate_payload(
        isv=isv,
        state=state,
        estimate=estimate,
        explanation=explanation,
        current_url=current_url,
        share_url=share_url,
        share_path=build_estimate_share_path(isv.slug, cloud, share_state),
        compare_url=compare_url,
        related_views=related_views,
        terraform_snippet=terraform_snippet,
        pricing_label=cloud_meta[cloud]["calculator_label"],
        calculator_url=cloud_meta[cloud]["calculator_url"]
    )

    if as_json:
        click.echo(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
        return

    _render_estimate_report(isv, state, estimate, explanation, payload)


@cli.command(name="compare")
@click.argument("isv_slug")
@click.option("--size", type=click.Choice(size_order, case_sensitive=False), default=None, help="Size tier to compare.")
@click.option("--ha/--no-ha", default=False, show_default=True, help="Toggle high availability overhead.")
@click.option("--term", type=click.Choice(term_order, case_sensitive=False), default="on-demand", show_default=True)
@click.option("--base-url", default=None, help="Base URL used to build share links.")
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON.")
def compare_cmd(isv_slug, size, ha, term, base_url, as_json):
    """Compare the same ISV across Google Cloud, AWS, and Azure."""

    isv = _get_isv_or_fail(isv_slug)
    _validate_size_choice(isv, size)

    state = resolve_compare_state(isv, size=size, ha=ha, term=term)
    pricing_caches = get_pricing_caches()
    view = build_compare_view(isv, state, pricing_caches, load_shape_mappings())
    explanation = build_compare_explanation(isv, state, view.estimates)
    base_url = _resolve_base_url(base_url)
    current_url = _build_compare_url(base_url, isv.slug, {"size": state.size, "ha": state.ha, "term": state.term})
    share_path = build_compare_share_path(isv.slug, {"size": state.size, "ha": state.ha, "term": state.term})
    share_url = _build_share_url(base_url, share_path)
    open_estimates = [
        {
            "label": f"Open {cloud_meta[cloud]['name']} estimate",
            "url": _build_estimate_url(
                base_url,
                isv.slug,
                cloud,
                {"size": state.size, "ha": state.ha, "term": state.term, "region": view.regions[cloud]}
            )
        }
        for cloud in cloud_order
    ]

    payload = _compare_payload(
        isv=isv,
        state=state,
        view=view,
        explanation=explanation,
        current_url=current_url,
        share_url=share_url,
        share_path=share_path,
        open_estimates=open_estimates
    )

    if as_json:
        click.echo(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
        return

    _render_compare_report(isv, state, view, explanation, payload)


def _render_estimate_report(isv, state, estimate, explanation, payload):
    accent = cloud_meta[state.cloud]["accent"]
    header = Text()
    header.append(f"Size {isv.name} on {cloud_meta[state.cloud]['name']}\n", style="bold")
    header.append(f"{estimate.size_label} - {format_user_range(estimate.size_description)}", style="dim")
    console.print(Panel(header, border_style=accent, padding=(1, 2)))

    summary = Table.grid(padding=(0, 1))
    summary.add_column(style="bold")
    summary.add_column()
    summary.add_row("Cloud", cloud_meta[state.cloud]["name"])
    summary.add_row("Size", estimate.size_label)
    summary.add_row("High availability", "On" if state.ha else "Off")
    summary.add_row("Commitment term", state.term)
    summary.add_row("Region", state.region)
    summary.add_row("Pricing snapshot", format_date(estimate.pricing_snapshot_date))
    console.print(summary)

    console.print()
    cost_table = Table(title="Cost Summary", box=box.SIMPLE_HEAVY, show_lines=False)
    cost_table.add_column("Item")
    cost_table.add_column("Monthly", justify="right")
    cost_table.add_column("Annual", justify="right")
    cost_table.add_row("Compute", format_currency(estimate.compute_total), format_rounded_annual(estimate.compute_total * 12))
    cost_table.add_row("Storage", format_currency(estimate.storage_total), format_rounded_annual(estimate.storage_total * 12))
    cost_table.add_row("Other", format_currency(estimate.other_total), format_rounded_annual(estimate.other_total * 12))
    cost_table.add_row("Total", format_currency(estimate.monthly_total), format_rounded_annual(estimate.annual_total), style="bold")
    console.print(cost_table)

    console.print()
    components_table = Table(title="Components Provisioned", box=box.SIMPLE_HEAVY, show_lines=False, expand=True)
    components_table.add_column("Role", style="bold", overflow="fold")
    components_table.add_column("Instance", overflow="fold")
    components_table.add_column("vCPU", justify="right")
    components_table.add_column("RAM", justify="right")
    components_table.add_column("Storage", justify="right")
    for component in estimate.components:
        components_table.add_row(
            format_role_label(component.role),
            f"{component.count} x {component.instance_type}",
            f"{component.vcpu:g}",
            f"{component.memory_gb:g}",
            format_storage(component.storage_gb)
        )
    console.print(components_table)

    console.print()
    console.print(Panel(explanation, title="Why this sizing", border_style=accent))

    export_table = Table.grid(padding=(0, 1), expand=True)
    export_table.add_column(style="bold", width=18)
    export_table.add_column(overflow="fold")
    export_table.add_row("Estimate URL", payload["current_url"])
    export_table.add_row("Share URL", payload["share_url"])
    export_table.add_row("Compare URL", payload["compare_url"])
    export_table.add_row("Calculator", payload["calculator"]["label"])
    export_table.add_row("Calculator URL", payload["calculator"]["url"])
    if payload["terraform_snippet"]:
        export_table.add_row("Terraform", "Google Cloud export available below")
    console.print(Panel(export_table, title="Export", border_style=accent))

    if payload["terraform_snippet"]:
        console.print()
        console.print(Panel(Syntax(payload["terraform_snippet"], "hcl", theme="ansi_dark", line_numbers=False), title="Google Cloud Terraform Baseline", border_style=accent))
    else:
        console.print()
        console.print(Panel("Terraform export is available for Google Cloud at launch. AWS and Azure are deferred to v1.5.", title="Terraform", border_style=accent))

    console.print()
    related = Table(title="Related Views", box=box.SIMPLE_HEAVY, show_lines=False, expand=True)
    related.add_column("Label", style="bold")
    related.add_column("URL", overflow="fold")
    for item in payload["related_views"]:
        related.add_row(item["label"], item["url"])
    console.print(related)

    _render_sources_and_notes(
        title="Sources",
        reference_line=f"Reference architecture: {isv.name} for {estimate.ref_arch_tier}, version {estimate.citations.ref_arch_version}, retrieved {format_date(estimate.citations.ref_arch_retrieved_date)}.",
        ref_arch_url=estimate.citations.ref_arch_url,
        pricing_line=f"Pricing: {cloud_meta[state.cloud]['name']} pricing snapshot, retrieved {format_date(estimate.pricing_snapshot_date)}.",
        notes=isv.notes,
        disclaimers=isv.disclaimers,
        border_style=accent
    )


def _render_compare_report(isv, state, view, explanation, payload):
    accent = cloud_meta[view.cheapest_cloud]["accent"]
    header = Text()
    header.append(f"Compare {isv.name} across clouds\n", style="bold")
    header.append(f"{view.size.upper()} - {format_user_range(isv.sizes[view.size].range_description)}", style="dim")
    console.print(Panel(header, border_style=accent, padding=(1, 2)))

    summary = Table.grid(padding=(0, 1))
    summary.add_column(style="bold")
    summary.add_column()
    summary.add_row("Size", isv.sizes[view.size].label)
    summary.add_row("High availability", "On" if state.ha else "Off")
    summary.add_row("Commitment term", state.term)
    console.print(summary)

    console.print()
    table = Table(title="Cloud Comparison", box=box.SIMPLE_HEAVY, show_lines=False, expand=True)
    table.add_column("Cloud", style="bold")
    table.add_column("Region")
    table.add_column("Monthly", justify="right")
    table.add_column("Annual", justify="right")
    table.add_column("Compute", justify="right")
    table.add_column("Storage", justify="right")
    table.add_column("Other", justify="right")
    table.add_column("Winner", justify="center")
    for cloud in cloud_order:
        estimate = view.estimates[cloud]
        winner = "Lowest" if cloud == view.cheapest_cloud else ""
        row_style = "bold green" if cloud == view.cheapest_cloud else None
        table.add_row(
            cloud_meta[cloud]["name"],
            view.regions[cloud],
            format_currency(estimate.monthly_total),
            format_rounded_annual(estimate.annual_total),
            format_currency(estimate.compute_total),
            format_currency(estimate.storage_total),
            format_currency(estimate.other_total),
            winner,
            style=row_style
        )
    console.print(table)

    console.print()
    summary_table = Table(title="Component Summary", box=box.SIMPLE_HEAVY, show_lines=False, expand=True)
    summary_table.add_column("Cloud", style="bold")
    summary_table.add_column("Top Components", overflow="fold")
    for cloud in cloud_order:
        summary_table.add_row(cloud_meta[cloud]["name"], summarize_components(view.estimates[cloud]))
    console.print(summary_table)

    console.print()
    console.print(Panel(explanation, title="Why the totals differ", border_style=accent))

    open_table = Table(title="Open Estimates", box=box.SIMPLE_HEAVY, show_lines=False, expand=True)
    open_table.add_column("Label", style="bold")
    open_table.add_column("URL", overflow="fold")
    for item in payload["open_estimates"]:
        open_table.add_row(item["label"], item["url"])
    console.print(open_table)

    _render_sources_and_notes(
        title="Sources",
        reference_line=f"Reference architecture: {isv.name}, version {isv.ref_arch.version}, retrieved {format_date(isv.ref_arch.retrieved_date)}.",
        ref_arch_url=isv.ref_arch.source_url,
        pricing_line=", ".join(
            f"{cloud_meta[cloud]['name']}: {format_date(view.estimates[cloud].pricing_snapshot_date)}"
            for cloud in cloud_order
        ) + ".",
        notes=isv.notes,
        disclaimers=isv.disclaimers,
        border_style=accent
    )


def _render_sources_and_notes(
    title,
    reference_line,
    ref_arch_url,
    pricing_line,
    notes,
    disclaimers,
    border_style
):
    sources = Table.grid(padding=(0, 1), expand=True)
    sources.add_column()
    sources.add_row(reference_line)
    sources.add_row(ref_arch_url)
    sources.add_row(pricing_line)
    sources.add_row("Commercial pricing only. GovCloud, sovereign cloud, and discounts beyond those shown are not modelled.")
    console.print(Panel(sources, title=title, border_style=border_style))

    if notes:
        notes_table = Table.grid(padding=(0, 1), expand=True)
        notes_table.add_column()
        for note in notes:
            notes_table.add_row(f"- {note}")
        console.print(Panel(notes_table, title="Notes", border_style=border_style))

    not_modelled = Table.grid(padding=(0, 1), expand=True)
    not_modelled.add_column()
    for item in NOT_MODELLED:
        not_modelled.add_row(f"- {item}")
    console.print(Panel(not_modelled, title="Not included in this estimate", border_style=border_style))

    if disclaimers:
        disclaimers_table = Table.grid(padding=(0, 1), expand=True)
        disclaimers_table.add_column()
        for disclaimer in disclaimers:
            disclaimers_table.add_row(f"- {disclaimer}")
        console.print(Panel(disclaimers_table, title="Disclaimers", border_style=border_style))


def _matches_filter(entry, query, category):
    text = " ".join(
        [
            entry.slug,
            entry.name,
            entry.vendor,
            entry.category,
            entry.description
        ]
    ).lower()
    if query and query.lower() not in text:
        return False
    if category and entry.category != category:
        return False
    return True


def _isv_payload(entry):
    return {
        "slug": entry.slug,
        "name": entry.name,
        "vendor": entry.vendor,
        "category": entry.category,
        "description": entry.description,
        "ref_arch": asdict(entry.ref_arch),
        "sizes": {
            size: {
                "label": tier.label,
                "range_description": tier.range_description,
                "ref_arch_tier": tier.ref_arch_tier,
                "components": [asdict(component) for component in tier.components],
                "ha_components": [asdict(component) for component in tier.ha_components]
            }
            for size, tier in entry.sizes.items()
        },
        "notes": list(entry.notes),
        "disclaimers": list(entry.disclaimers)
    }


def _estimate_payload(
    isv,
    state,
    estimate,
    explanation,
    current_url,
    share_url,
    share_path,
    compare_url,
    related_views,
    terraform_snippet,
    pricing_label,
    calculator_url
):
    return {
        "workload": {
            "slug": isv.slug,
            "name": isv.name,
            "vendor": isv.vendor,
            "category": isv.category,
            "description": isv.description
        },
        "state": asdict(state),
        "estimate": asdict(estimate),
        "explanation": explanation,
        "current_url": current_url,
        "share_url": share_url,
        "share_path": share_path,
        "compare_url": compare_url,
        "related_views": related_views,
        "calculator": {
            "label": pricing_label,
            "url": calculator_url
        },
        "terraform_snippet": terraform_snippet,
        "sources": {
            "reference_architecture": asdict(estimate.citations),
            "pricing_snapshot_date": estimate.pricing_snapshot_date
        },
        "notes": list(isv.notes),
        "disclaimers": list(isv.disclaimers),
        "not_modelled": list(NOT_MODELLED)
    }


def _compare_payload(
    isv,
    state,
    view,
    explanation,
    current_url,
    share_url,
    share_path,
    open_estimates
):
    return {
        "workload": {
            "slug": isv.slug,
            "name": isv.name,
            "vendor": isv.vendor,
            "category": isv.category,
            "description": isv.description
        },
        "state": asdict(state),
        "view": asdict(view),
        "explanation": explanation,
        "current_url": current_url,
        "share_url": share_url,
        "share_path": share_path,
        "open_estimates": open_estimates,
        "sources": {
            "reference_architecture": asdict(isv.ref_arch),
            "pricing_snapshots": {
                cloud: view.estimates[cloud].pricing_snapshot_date for cloud in cloud_order
            }
        },
        "notes": list(isv.notes),
        "disclaimers": list(isv.disclaimers),
        "not_modelled": list(NOT_MODELLED)
    }


def _resolve_base_url(base_url):
    return (base_url or get_base_url() or None)


def _build_estimate_url(base_url, slug, cloud, state):
    path = f"/sizing/{slug}/{cloud}?{build_estimate_query(state)}"
    return _build_share_url(base_url, path)


def _build_compare_url(base_url, slug, state):
    path = f"/sizing/{slug}/compare?size={state['size']}&ha={str(state['ha']).lower()}&term={state['term']}"
    return _build_share_url(base_url, path)


def _build_share_url(base_url, path):
    if not base_url:
        return path
    return f"{base_url.rstrip('/')}{path}"


def _get_isv_or_fail(slug):
    try:
        return get_isv(slug)
    except KeyError as exc:
        raise click.BadParameter(str(exc)) from exc


def _validate_size_choice(isv, size):
    if size and size not in isv.sizes:
        available = ", ".join(size.upper() for size in size_order if size in isv.sizes)
        raise click.BadParameter(f'Size "{size}" is not available for {isv.slug}. Available sizes: {available}.')


def _validate_region_choice(pricing_cache, region):
    if region and region not in pricing_cache.regions:
        available = ", ".join(pricing_cache.regions.keys())
        raise click.BadParameter(f'Region "{region}" is not available for this cloud. Available regions: {available}.')


if __name__ == "__main__":
    cli()

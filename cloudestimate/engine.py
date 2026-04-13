from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from cloudestimate.data import (
    IsvEntry,
    PricingCache,
    RegionPricing,
    ShapeMapping,
    load_all_pricing_caches,
)
from cloudestimate.formatting import (
    format_currency,
    format_percent,
    format_role_label,
    format_storage,
)
from cloudestimate.site import CloudSlug, CommitmentTerm, cloud_meta, cloud_order, size_order

TERM_PRICE_KEY = {
    "on-demand": "on_demand_hourly_usd",
    "1yr": "reserved_1yr_hourly_usd",
    "3yr": "reserved_3yr_hourly_usd"
}


@dataclass(slots=True)
class EstimateState:
    cloud: CloudSlug
    size: str
    ha: bool
    term: CommitmentTerm
    region: str


@dataclass(slots=True)
class CompareState:
    size: str
    ha: bool
    term: CommitmentTerm


@dataclass(slots=True)
class EstimateCitations:
    ref_arch_url: str
    ref_arch_version: str
    ref_arch_retrieved_date: str
    pricing_retrieved_at: str


@dataclass(slots=True)
class EstimateComponent:
    role: str
    count: int
    vcpu: float
    memory_gb: float
    storage_gb: float
    storage_type: str | None
    profile: str
    instance_type: str
    unit_hourly: float
    monthly_compute: float
    monthly_storage: float


@dataclass(slots=True)
class EstimateResult:
    monthly_total: float
    annual_total: float
    compute_total: float
    storage_total: float
    other_total: float
    pricing_snapshot_date: str
    size_label: str
    size_description: str
    ref_arch_tier: str
    components: tuple[EstimateComponent, ...]
    citations: EstimateCitations


@dataclass(slots=True)
class CompareView:
    size: str
    ha: bool
    term: CommitmentTerm
    regions: dict[CloudSlug, str]
    estimates: dict[CloudSlug, EstimateResult]
    ranked_clouds: tuple[CloudSlug, ...]
    cheapest_cloud: CloudSlug


def get_default_size(isv: IsvEntry) -> str:
    for size in size_order:
        if size in isv.sizes:
            return size

    available = ", ".join(sorted(isv.sizes.keys()))
    raise ValueError(f'No size tiers are defined for {isv.slug}. Available sizes: {available}.')


def get_regions_for_cloud(pricing_cache: PricingCache) -> tuple[str, ...]:
    return tuple(pricing_cache.regions.keys())


def score_region(pricing: RegionPricing) -> float:
    compute_rates = [rate.on_demand_hourly_usd for rate in pricing.compute.values()]
    average_compute = sum(compute_rates) / len(compute_rates) if compute_rates else float("inf")
    return average_compute + pricing.storage.ssd_gb_month_usd + pricing.storage.object_gb_month_usd


def pick_default_region(pricing_cache: PricingCache, fallback_region: str) -> str:
    if not pricing_cache.regions:
        return fallback_region

    ranked = sorted(
        pricing_cache.regions.items(),
        key=lambda item: (score_region(item[1]), item[0])
    )
    return ranked[0][0]


def pick_shape_mapping(shape_mappings: Iterable[ShapeMapping], vcpu: float, memory_gb: float) -> ShapeMapping:
    sorted_mappings = sorted(
        shape_mappings,
        key=lambda mapping: (
            max(mapping.vcpu - vcpu, 0) + max(mapping.memory_gb - memory_gb, 0),
            mapping.vcpu,
            mapping.memory_gb
        )
    )

    for mapping in sorted_mappings:
        if mapping.vcpu >= vcpu and mapping.memory_gb >= memory_gb:
            return mapping

    if not sorted_mappings:
        raise ValueError("No shape mappings are available.")

    return sorted_mappings[-1]


def get_storage_rate(pricing: RegionPricing, storage_type: str | None) -> float:
    if storage_type == "ssd":
        return pricing.storage.ssd_gb_month_usd

    if storage_type == "hdd":
        return pricing.storage.hdd_gb_month_usd

    if storage_type == "nvme":
        return pricing.storage.nvme_gb_month_usd

    if storage_type == "object":
        return pricing.storage.object_gb_month_usd

    return 0.0


def resolve_estimate_state(
    isv: IsvEntry,
    pricing_cache: PricingCache,
    cloud: CloudSlug,
    size: str | None = None,
    ha: bool = False,
    term: CommitmentTerm = "on-demand",
    region: str | None = None
) -> EstimateState:
    resolved_size = size if size in isv.sizes else get_default_size(isv)
    resolved_region = region if region in pricing_cache.regions else pick_default_region(pricing_cache, cloud_meta[cloud]["default_region"])

    return EstimateState(
        cloud=cloud,
        size=resolved_size,
        ha=ha,
        term=term,
        region=resolved_region
    )


def resolve_compare_state(
    isv: IsvEntry,
    size: str | None = None,
    ha: bool = False,
    term: CommitmentTerm = "on-demand"
) -> CompareState:
    resolved_size = size if size in isv.sizes else get_default_size(isv)
    return CompareState(size=resolved_size, ha=ha, term=term)


def build_estimate(
    isv: IsvEntry,
    state: EstimateState,
    pricing_cache: PricingCache,
    shape_mappings: Iterable[ShapeMapping]
) -> EstimateResult:
    size_tier = isv.sizes[state.size]
    region_pricing = pricing_cache.regions[state.region]
    components = list(size_tier.components)
    if state.ha:
        components.extend(size_tier.ha_components)

    resolved_components: list[EstimateComponent] = []
    for component in components:
        mapping = pick_shape_mapping(shape_mappings, component.vcpu, component.memory_gb)
        instance_type = getattr(mapping, state.cloud)
        rates = region_pricing.compute.get(instance_type)
        if rates is None:
            raise ValueError(f"Missing compute price for {instance_type}.")

        unit_hourly = getattr(rates, TERM_PRICE_KEY[state.term])
        monthly_compute = unit_hourly * 730 * component.count
        monthly_storage = (component.storage_gb or 0) * get_storage_rate(region_pricing, component.storage_type) * component.count

        resolved_components.append(
            EstimateComponent(
                role=component.role,
                count=component.count,
                vcpu=component.vcpu,
                memory_gb=component.memory_gb,
                storage_gb=float(component.storage_gb or 0),
                storage_type=component.storage_type,
                profile=mapping.profile,
                instance_type=instance_type,
                unit_hourly=unit_hourly,
                monthly_compute=monthly_compute,
                monthly_storage=monthly_storage
            )
        )

    compute_total = sum(component.monthly_compute for component in resolved_components)
    storage_total = sum(component.monthly_storage for component in resolved_components)
    load_balancer_count = sum(
        component.count
        for component in resolved_components
        if "load-balancer" in component.role
    )
    other_total = load_balancer_count * region_pricing.other.load_balancer_monthly_usd
    monthly_total = compute_total + storage_total + other_total

    return EstimateResult(
        monthly_total=monthly_total,
        annual_total=monthly_total * 12,
        compute_total=compute_total,
        storage_total=storage_total,
        other_total=other_total,
        pricing_snapshot_date=pricing_cache.retrieved_at[:10],
        size_label=size_tier.label,
        size_description=size_tier.range_description,
        ref_arch_tier=size_tier.ref_arch_tier,
        components=tuple(resolved_components),
        citations=EstimateCitations(
            ref_arch_url=isv.ref_arch.source_url,
            ref_arch_version=isv.ref_arch.version,
            ref_arch_retrieved_date=isv.ref_arch.retrieved_date,
            pricing_retrieved_at=pricing_cache.retrieved_at
        )
    )


def build_compare_view(
    isv: IsvEntry,
    state: CompareState,
    pricing_caches: dict[CloudSlug, PricingCache],
    shape_mappings: Iterable[ShapeMapping]
) -> CompareView:
    regions = {
        cloud: pick_default_region(pricing_caches[cloud], cloud_meta[cloud]["default_region"])
        for cloud in cloud_order
    }
    estimates = {
        cloud: build_estimate(
            isv,
            EstimateState(
                cloud=cloud,
                size=state.size,
                ha=state.ha,
                term=state.term,
                region=regions[cloud]
            ),
            pricing_caches[cloud],
            shape_mappings
        )
        for cloud in cloud_order
    }
    ranked_clouds = tuple(
        sorted(
            cloud_order,
            key=lambda cloud: (
                estimates[cloud].monthly_total,
                cloud_order.index(cloud)
            )
        )
    )

    return CompareView(
        size=state.size,
        ha=state.ha,
        term=state.term,
        regions=regions,
        estimates=estimates,
        ranked_clouds=ranked_clouds,
        cheapest_cloud=ranked_clouds[0]
    )


def build_sizing_explanation(
    isv: IsvEntry,
    cloud: CloudSlug,
    state: EstimateState,
    estimate: EstimateResult
) -> str:
    dominant = _dominant_line_item(estimate)
    share = (dominant["value"] / estimate.monthly_total) * 100 if estimate.monthly_total > 0 else 0
    biggest_storage = max(estimate.components, key=lambda component: component.storage_gb, default=None)
    commitment_sentence = (
        _build_commitment_sentence(state.term, estimate)
        if state.term != "on-demand" and estimate.components
        else None
    )

    sentences = [
        f"{isv.name} at the {estimate.size_label.lower()} tier maps to the {estimate.ref_arch_tier} reference architecture on {cloud_meta[cloud]['name']} in {state.region}.",
        f"{dominant['label']} is the largest line item in this estimate, accounting for {format_percent(share)} of monthly cost.",
        (
            "High availability is enabled here, so the footprint carries duplicate capacity for failover across the application, data, or cache tiers."
            if state.ha
            else "High availability is not included here, so this baseline stays lean and leaves failover headroom out of the monthly total."
        ),
    ]

    if biggest_storage and biggest_storage.storage_gb:
        storage_clause = (
            f"{format_role_label(biggest_storage.role)} carries the heaviest storage footprint at {format_storage(biggest_storage.storage_gb)}"
        )
        if biggest_storage.count > 1:
            storage_clause += f" on each of its {biggest_storage.count} nodes"
        storage_clause += "."
        if commitment_sentence:
            storage_clause += f" {commitment_sentence}"
        sentences.append(storage_clause)
    else:
        sentence = "This tier is primarily a compute sizing exercise rather than a storage-heavy one."
        if commitment_sentence:
            sentence += f" {commitment_sentence}"
        sentences.append(sentence)

    return " ".join(sentences)


def build_compare_explanation(
    isv: IsvEntry,
    state: CompareState,
    estimates: dict[CloudSlug, EstimateResult]
) -> str:
    ranked = sorted(
        (
            {"cloud": cloud, "total": estimate.monthly_total}
            for cloud, estimate in estimates.items()
        ),
        key=lambda item: item["total"]
    )
    cheapest = ranked[0]
    priciest = ranked[-1]
    second = ranked[1] if len(ranked) > 1 else None
    delta = priciest["total"] - cheapest["total"]
    midpoint_delta = second["total"] - cheapest["total"] if second else 0

    sentences = [
        f"{cloud_meta[cheapest['cloud']]['name']} is the lowest-cost option for {isv.name} at the {state.size.lower()} tier, landing {format_currency(delta)} per month below {cloud_meta[priciest['cloud']]['name']}.",
        (
            "This spread comes from instance and storage pricing in the default regions rather than commitment discounts, so the ranking reflects straight commercial list pricing."
            if state.term == "on-demand"
            else f"{state.term} commitments compress compute spend across all three clouds, but the ranking still follows the relative price of the matched VM families and storage rates."
        ),
        (
            f"With high availability enabled, the cost gap matters most in duplicated data tiers, where each extra node amplifies regional price differences by about {format_currency(midpoint_delta)} per month between the cheapest and middle option."
            if state.ha
            else "Without high availability, the totals stay closer together because there is less replicated capacity, but existing enterprise commitments or hybrid-use discounts could still change the real procurement outcome."
        )
    ]

    return " ".join(sentences)


def _dominant_line_item(estimate: EstimateResult) -> dict[str, float | str]:
    items = [
        {"label": "Compute", "value": estimate.compute_total},
        {"label": "Storage", "value": estimate.storage_total},
        {"label": "Other", "value": estimate.other_total}
    ]
    return sorted(items, key=lambda item: item["value"], reverse=True)[0]


def _build_commitment_sentence(term: CommitmentTerm, estimate: EstimateResult) -> str:
    on_demand_equivalent = estimate.compute_total / (0.724 if term == "1yr" else 0.538)
    savings = ((on_demand_equivalent - estimate.compute_total) / on_demand_equivalent) * 100 if on_demand_equivalent > 0 else 0
    return f"{term} pricing cuts the compute portion by about {format_percent(savings)} against on-demand in this snapshot."


def summarize_components(estimate: EstimateResult, limit: int = 5) -> str:
    return "; ".join(
        f"{component.count} x {component.instance_type} for {format_role_label(component.role)}"
        for component in estimate.components[:limit]
    )


def get_pricing_caches() -> dict[CloudSlug, PricingCache]:
    return load_all_pricing_caches()

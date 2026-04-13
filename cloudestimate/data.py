from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from cloudestimate.site import CloudSlug, cloud_order


@dataclass(slots=True)
class ReferenceArchitecture:
    source_url: str
    version: str
    retrieved_date: str


@dataclass(slots=True)
class Component:
    role: str
    count: int
    vcpu: float
    memory_gb: float
    storage_gb: int | None = None
    storage_type: str | None = None


@dataclass(slots=True)
class SizeTier:
    label: str
    range_description: str
    ref_arch_tier: str
    components: tuple[Component, ...]
    ha_components: tuple[Component, ...] = ()


@dataclass(slots=True)
class IsvEntry:
    slug: str
    name: str
    vendor: str
    category: str
    description: str
    ref_arch: ReferenceArchitecture
    sizes: dict[str, SizeTier]
    notes: tuple[str, ...] = ()
    disclaimers: tuple[str, ...] = ()


@dataclass(slots=True)
class ShapeMapping:
    profile: str
    vcpu: int
    memory_gb: int
    gcp: str
    aws: str
    azure: str


@dataclass(slots=True)
class ComputeRates:
    on_demand_hourly_usd: float
    reserved_1yr_hourly_usd: float
    reserved_3yr_hourly_usd: float


@dataclass(slots=True)
class StorageRates:
    ssd_gb_month_usd: float
    hdd_gb_month_usd: float
    nvme_gb_month_usd: float
    object_gb_month_usd: float


@dataclass(slots=True)
class OtherRates:
    load_balancer_monthly_usd: float


@dataclass(slots=True)
class RegionPricing:
    compute: dict[str, ComputeRates]
    storage: StorageRates
    other: OtherRates


@dataclass(slots=True)
class PricingCache:
    cloud: CloudSlug
    retrieved_at: str
    regions: dict[str, RegionPricing]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _candidate_roots() -> tuple[Path, ...]:
    roots: list[Path] = []
    env_root = os.environ.get("CLOUDESTIMATE_WEB_ROOT")
    if env_root:
        roots.append(Path(env_root))
    roots.extend([_repo_root() / "web", _repo_root(), Path.cwd() / "web", Path.cwd()])
    return tuple(dict.fromkeys(roots))


def _find_first_existing(*relative_paths: str) -> Path:
    for root in _candidate_roots():
        for candidate_root in (root, root / "web"):
            for relative_path in relative_paths:
                candidate = candidate_root / relative_path
                if candidate.exists():
                    return candidate

    paths = ", ".join(relative_paths)
    raise FileNotFoundError(
        f"Could not locate CloudEstimate web data. Expected one of: {paths}. "
        "Set CLOUDESTIMATE_WEB_ROOT to the web directory if you are running the CLI outside the repo checkout."
    )


def _load_json_file(*relative_paths: str) -> Any:
    path = _find_first_existing(*relative_paths)
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml_file(*relative_paths: str) -> Any:
    path = _find_first_existing(*relative_paths)
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _component_from_payload(payload: dict[str, Any]) -> Component:
    storage_gb = payload.get("storage_gb")
    if storage_gb is not None:
        storage_gb = int(storage_gb)

    storage_type = payload.get("storage_type") or None

    return Component(
        role=str(payload["role"]),
        count=int(payload["count"]),
        vcpu=float(payload["vcpu"]),
        memory_gb=float(payload["memory_gb"]),
        storage_gb=storage_gb,
        storage_type=storage_type
    )


def _size_tier_from_payload(payload: dict[str, Any]) -> SizeTier:
    return SizeTier(
        label=str(payload["label"]),
        range_description=str(payload["range_description"]).strip(),
        ref_arch_tier=str(payload["ref_arch_tier"]),
        components=tuple(_component_from_payload(component) for component in payload.get("components", [])),
        ha_components=tuple(_component_from_payload(component) for component in payload.get("ha_components") or [])
    )


def _isv_from_payload(payload: dict[str, Any]) -> IsvEntry:
    ref_arch = payload["ref_arch"]
    sizes = {size: _size_tier_from_payload(size_payload) for size, size_payload in payload.get("sizes", {}).items()}

    return IsvEntry(
        slug=str(payload["slug"]),
        name=str(payload["name"]),
        vendor=str(payload["vendor"]),
        category=str(payload["category"]),
        description=str(payload["description"]).strip(),
        ref_arch=ReferenceArchitecture(
            source_url=str(ref_arch["source_url"]),
            version=str(ref_arch["version"]),
            retrieved_date=str(ref_arch["retrieved_date"])
        ),
        sizes=sizes,
        notes=tuple(str(note).strip() for note in payload.get("notes") or [] if str(note).strip()),
        disclaimers=tuple(str(disclaimer).strip() for disclaimer in payload.get("disclaimers") or [] if str(disclaimer).strip())
    )


def _shape_mapping_from_payload(payload: dict[str, Any]) -> ShapeMapping:
    return ShapeMapping(
        profile=str(payload["profile"]),
        vcpu=int(payload["vcpu"]),
        memory_gb=int(payload["memory_gb"]),
        gcp=str(payload["gcp"]),
        aws=str(payload["aws"]),
        azure=str(payload["azure"])
    )


def _compute_rates_from_payload(payload: dict[str, Any]) -> ComputeRates:
    return ComputeRates(
        on_demand_hourly_usd=float(payload["on_demand_hourly_usd"]),
        reserved_1yr_hourly_usd=float(payload["reserved_1yr_hourly_usd"]),
        reserved_3yr_hourly_usd=float(payload["reserved_3yr_hourly_usd"])
    )


def _storage_rates_from_payload(payload: dict[str, Any]) -> StorageRates:
    return StorageRates(
        ssd_gb_month_usd=float(payload["ssd_gb_month_usd"]),
        hdd_gb_month_usd=float(payload["hdd_gb_month_usd"]),
        nvme_gb_month_usd=float(payload["nvme_gb_month_usd"]),
        object_gb_month_usd=float(payload["object_gb_month_usd"])
    )


def _other_rates_from_payload(payload: dict[str, Any]) -> OtherRates:
    return OtherRates(load_balancer_monthly_usd=float(payload.get("load_balancer_monthly_usd", 0)))


def _region_pricing_from_payload(payload: dict[str, Any]) -> RegionPricing:
    return RegionPricing(
        compute={instance_type: _compute_rates_from_payload(rate_payload) for instance_type, rate_payload in payload.get("compute", {}).items()},
        storage=_storage_rates_from_payload(payload.get("storage", {})),
        other=_other_rates_from_payload(payload.get("other", {}))
    )


@lru_cache(maxsize=1)
def load_isv_catalog() -> tuple[IsvEntry, ...]:
    if _find_optional("functions/generated/isv-catalog.json"):
        payload = _load_json_file("functions/generated/isv-catalog.json")
        return tuple(_isv_from_payload(entry) for entry in payload)

    payload = _load_yaml_directory("src/content/isvs")
    return tuple(_isv_from_payload(entry) for entry in payload)


@lru_cache(maxsize=1)
def load_isv_index() -> dict[str, IsvEntry]:
    return {entry.slug: entry for entry in load_isv_catalog()}


@lru_cache(maxsize=1)
def load_shape_mappings() -> tuple[ShapeMapping, ...]:
    if _find_optional("functions/generated/shape-mappings.json"):
        payload = _load_json_file("functions/generated/shape-mappings.json")
        return tuple(_shape_mapping_from_payload(entry) for entry in payload)

    payload = _load_yaml_file("src/data/shape-mappings.yaml")
    return tuple(_shape_mapping_from_payload(entry) for entry in payload)


@lru_cache(maxsize=None)
def load_pricing_cache(cloud: CloudSlug) -> PricingCache:
    path = _find_optional(f"src/data/generated/pricing/{cloud}.json")
    if path is None:
        pricing_root = _find_first_existing("src/data/pricing")
        matches = sorted(pricing_root.glob(f"{cloud}-*.json"))
        if not matches:
            raise FileNotFoundError(f"Could not locate pricing snapshot for {cloud}.")
        path = matches[0]

    payload = json.loads(path.read_text(encoding="utf-8"))
    regions = {region_name: _region_pricing_from_payload(region_payload) for region_name, region_payload in payload.get("regions", {}).items()}
    return PricingCache(cloud=cloud, retrieved_at=str(payload["retrieved_at"]), regions=regions)


def load_all_pricing_caches() -> dict[CloudSlug, PricingCache]:
    return {cloud: load_pricing_cache(cloud) for cloud in cloud_order}


def get_isv(slug: str) -> IsvEntry:
    try:
        return load_isv_index()[slug]
    except KeyError as exc:
        available = ", ".join(entry.slug for entry in load_isv_catalog())
        raise KeyError(f'Unknown ISV "{slug}". Available slugs: {available}.') from exc


def _find_optional(*relative_paths: str) -> Path | None:
    try:
        return _find_first_existing(*relative_paths)
    except FileNotFoundError:
        return None


def _load_yaml_directory(relative_directory: str) -> list[dict[str, Any]]:
    directory = _find_first_existing(relative_directory)
    if not directory.is_dir():
        raise FileNotFoundError(f"Expected a directory at {directory}")

    payloads: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.yaml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if payload:
            payloads.append(payload)

    return payloads

from __future__ import annotations

from collections.abc import Iterable


def build_gcp_terraform_snippet(
    slug: str,
    region: str,
    components: Iterable,
    comment_label: str = "Google Cloud"
) -> str:
    resources = []

    for index, component in enumerate(components):
        resource_name = safe_terraform_name(f"{component.role}_{index + 1}")
        instance_name = safe_gcp_name(f"{slug}-{component.role}-{index + 1}")
        disk_resource = ""
        disk_attachment = ""

        if component.storage_gb > 0:
            disk_resource = f"""
resource "google_compute_disk" "{resource_name}_data" {{
  count = {component.count}
  name  = "{instance_name}-data-${{count.index + 1}}"
  type  = "{get_gcp_disk_type(component.storage_type)}"
  zone  = "{region}-a"
  size  = {_format_number(component.storage_gb)}
}}
"""
            disk_attachment = """
  attached_disk {{
    source = google_compute_disk.{resource_name}_data[count.index].id
    mode   = "READ_WRITE"
  }}""".format(resource_name=resource_name)

        resources.append(
            f"""{disk_resource}resource "google_compute_instance" "{resource_name}" {{
  count        = {component.count}
  name         = "{instance_name}-${{count.index + 1}}"
  machine_type = "{component.instance_type}"
  zone         = "{region}-a"

  boot_disk {{
    initialize_params {{
      image = "projects/debian-cloud/global/images/family/debian-12"
      size  = 50
      type  = "pd-balanced"
    }}
  }}

  network_interface {{
    network = "default"
    access_config {{}}
  }}{disk_attachment}

  labels = {{
    app  = "{safe_gcp_name(slug)}"
    role = "{safe_gcp_name(component.role)}"
  }}
}}"""
        )

    resources_block = "\n\n".join(resources)

    return f"""terraform {{
  required_version = ">= 1.6.0"

  required_providers {{
    google = {{
      source  = "hashicorp/google"
      version = "~> 6.0"
    }}
  }}
}}

variable "project_id" {{
  description = "Google Cloud project ID for this deployment."
  type        = string
  default     = "replace-with-project-id"
}}

provider "google" {{
  project = var.project_id
  region  = "{region}"
  zone    = "{region}-a"
}}

# Generated for {comment_label} from the current estimate state.
{resources_block}
"""


def safe_terraform_name(value: str) -> str:
    return _sanitize(value, "_")


def safe_gcp_name(value: str) -> str:
    return _sanitize(value, "-")


def get_gcp_disk_type(storage_type: str | None) -> str:
    if storage_type == "ssd":
        return "pd-ssd"

    if storage_type == "nvme":
        return "hyperdisk-balanced"

    return "pd-standard"


def _sanitize(value: str, separator: str) -> str:
    import re

    sanitized = re.sub(r"[^a-z0-9]+", separator, value, flags=re.IGNORECASE)
    return sanitized.strip(separator).lower()


def _format_number(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))

    return f"{value:g}"

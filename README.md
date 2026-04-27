# CloudEstimate CLI

CloudEstimate CLI mirrors the web app's curated ISV catalog and sizing model. CloudEstimate is a worked example of the [Precomputed AI](https://precomputedai.com) design pattern; the CLI serves from the same versioned reference-architecture, shape-mapping, and pricing artifacts as the web app.

Precomputed AI citation: Raquedan, R. (2026). *Precomputed AI: Reason Ahead of Time, Serve Instantly.* https://precomputedai.com

## Quick Start

```bash
cd CLI
python3 -m pip install -e .
cloudestimate --help
```

If the CLI cannot find the web data directory, set `CLOUDESTIMATE_WEB_ROOT` to the `web/` folder in this repo.

## Commands

- `cloudestimate list`
- `cloudestimate estimate <isv>`
- `cloudestimate compare <isv>`

The CLI also accepts `--json` on each command for machine-readable output.

### `list`

Shows the supported ISVs, vendors, categories, and catalog coverage.

Examples:

```bash
cloudestimate list
cloudestimate list --query gitlab
cloudestimate list --category streaming
```

### `estimate`

Estimates one workload on one cloud.

Options:

- `--cloud gcp|aws|azure`
- `--size xs|s|m|l|xl`
- `--ha / --no-ha`
- `--term on-demand|1yr|3yr`
- `--region <region>`
- `--base-url <url>` for absolute share links

Examples:

```bash
cloudestimate estimate gitlab
cloudestimate estimate gitlab --cloud aws --size m --ha --term 1yr
cloudestimate estimate gitlab --json
```

### `compare`

Compares the same workload across Google Cloud, AWS, and Azure using the default region for each cloud.

Examples:

```bash
cloudestimate compare gitlab
cloudestimate compare gitlab --size xl --ha --term 3yr
cloudestimate compare gitlab --json
```

## What It Uses

- `web/functions/generated/isv-catalog.json` for the normalized workload catalog
- `web/functions/generated/shape-mappings.json` for VM shape matching
- `web/src/data/generated/pricing/*.json` for pricing snapshots

The CLI renders the same estimate metadata shown in the web app:

- monthly and annual totals
- compute, storage, and other line items
- component-level VM mappings
- source citations and pricing snapshot dates
- Terraform export for Google Cloud estimates
- share URLs that match the web routes

## Environment Variables

- `CLOUDESTIMATE_WEB_ROOT`: override the path to the `web/` directory
- `CLOUDESTIMATE_BASE_URL`: prefix share links with a custom site URL
- `PUBLIC_SITE_URL`: used as a fallback base URL if `CLOUDESTIMATE_BASE_URL` is not set

## Contributing

The CLI is intentionally aligned with the web app's content model. If you are adding or updating a workload, update the web catalog and pricing assets first, then verify the CLI output against the web estimate pages.

See `web/CONTRIBUTING.md` for the catalog schema and validation flow.

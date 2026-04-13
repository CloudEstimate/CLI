# Contributing to CloudEstimate CLI

Thanks for helping improve CloudEstimate.

This CLI is now aligned with the web app's curated ISV catalog, so the source of truth lives in the web workspace:

- `web/src/content/isvs/*.yaml` for workload definitions
- `web/src/data/generated/pricing/*.json` for cached pricing snapshots
- `web/functions/generated/isv-catalog.json` and `web/functions/generated/shape-mappings.json` for the generated artifacts the CLI reads

## Recommended Workflow

1. Update the workload or pricing data in the web workspace.
2. Regenerate the generated artifacts if needed.
3. Run the CLI from `CLI/` and verify `list`, `estimate`, and `compare` output.
4. Open a pull request with a clear note about the catalog or pricing change.

## Validation Tips

Useful checks while iterating:

```bash
cd web
npm run validate:isvs
npm run sync:functions-data

cd ../CLI
python3 -m cloudestimate.cli list
python3 -m cloudestimate.cli estimate gitlab
python3 -m cloudestimate.cli compare gitlab
```

## What to Watch For

- Keep reference architecture citations current and explicit.
- Keep size tiers consistent with the web sizing pages.
- Make sure pricing snapshots and share URLs still line up with the web routes.
- Avoid changing the CLI output contract unless the web docs are changing with it.

If you're unsure how a workload should be modeled, follow the patterns in the existing web ISV catalog and methodology pages.

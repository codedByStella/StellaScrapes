
#!/usr/bin/env python3
"""
catalog.py
==========
Fetches dataset metadata from Socrata domains and writes a catalog
to socrata_catalog.json.

The public version retains metadata retrieval and catalog generation.
Proprietary field-detection, dataset-classification, and registry-
generation logic has been intentionally removed.

Usage:
    # Catalog a single domain
    python catalog.py --domain data.austintexas.gov

    # Catalog all domains from discover.py output
    python catalog.py --all --domains-file socrata_domains.json

    # Catalog top N domains by dataset count
    python catalog.py --all --top 50 --domains-file socrata_domains.json

Output: socrata_catalog.json
"""

import json
import sys
import time
import urllib.request
import argparse
import os
import re
from datetime import datetime, timezone

GLOBAL_CATALOG = "https://api.us.socrata.com/api/catalog/v1"
PAGE_SIZE = 100


# ── HTTP fetch ────────────────────────────────────────────────────────────────

def fetch(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "DataScraperBot/1.0"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))

        except urllib.error.HTTPError as e:
            if e.code in (404, 403):
                return None

            if attempt == retries - 1:
                return None

            time.sleep(2 ** attempt)

        except Exception:
            if attempt == retries - 1:
                return None

            time.sleep(2 ** attempt)

    return None


# ── Catalog a single domain ───────────────────────────────────────────────────

def catalog_domain(domain, verbose=True):
    """
    Fetches all datasets from a Socrata domain.

    Returns:
        {
            "domain": str,
            "dataset_count": int,
            "datasets": [...]
        }
    """

    datasets = []
    offset = 0
    total = None

    while True:
        url = (
            f"{GLOBAL_CATALOG}?only=datasets"
            f"&domains={domain}"
            f"&limit={PAGE_SIZE}"
            f"&offset={offset}"
        )

        data = fetch(url)

        if data is None:
            if verbose:
                print(f"    ✗ {domain} — unreachable or no catalog API")
            return None

        results = data.get("results", [])

        if total is None:
            total = data.get("resultSetSize", 0)

        if not results:
            break

        for item in results:
            resource = item.get("resource", {})

            name = resource.get("name", "")
            description = resource.get("description", "") or ""
            updated = resource.get("data_updated_at", "") or ""

            # Strip HTML from description.
            description_clean = re.sub(
                r"<[^>]+>",
                " ",
                description
            ).strip()

            datasets.append({
                "id": resource.get("id", ""),
                "name": name,
                "description": description_clean[:300],
                "columns": resource.get("columns_field_name", []),
                "row_count": resource.get(
                    "page_views", {}
                ).get("page_views_total", 0),
                "updated_at": updated[:10] if updated else "",
                "permalink": item.get("permalink", "")
            })

        offset += PAGE_SIZE

        if offset >= total:
            break

        time.sleep(0.05)

    if verbose:
        print(
            f"    ✓ {domain:<45} "
            f"{len(datasets):>4} datasets"
        )

    return {
        "domain": domain,
        "dataset_count": len(datasets),
        "datasets": datasets
    }


# ── Registry generation ───────────────────────────────────────────────────────

# [REDACTED]
#
# Proprietary implementation omitted:
# - Dataset category classification.
# - Automatic field-role detection.
# - Dataset selection and ranking within categories.
# - Conversion of catalog results into registry configuration.
#
# The public version does not generate registry-ready entries.


# ── Main ──────────────────────────────────────────────────────────────────────

def run_single(domain, out_path="socrata_catalog.json"):
    print(f"\nCataloging: {domain}")

    result = catalog_domain(domain, verbose=True)

    if result:
        output = {
            "domains": {
                domain: result
            }
        }

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)

        print(f"\nSaved to {out_path}")
        print(f"Datasets found: {result['dataset_count']}")


def run_all(
    domains_file="socrata_domains.json",
    out_path="socrata_catalog.json",
    top=None
):
    # Load domain list.
    if not os.path.exists(domains_file):
        print(
            f"ERROR: {domains_file} not found. "
            "Run discover.py first."
        )
        sys.exit(1)

    with open(domains_file, encoding="utf-8") as f:
        data = json.load(f)

    all_domains = [
        domain["domain"]
        for domain in data["domains"]
    ]

    if top:
        all_domains = all_domains[:top]

    print(f"\nCataloging {len(all_domains)} domains...")
    print(f"Output: {out_path}")
    print()

    # Load existing catalog if resuming.
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            catalog = json.load(f)

        already_done = set(
            catalog.get("domains", {}).keys()
        )

        print(
            f"  Resuming — {len(already_done)} "
            "domains already cataloged"
        )

    else:
        catalog = {"domains": {}}
        already_done = set()

    results = catalog["domains"]
    errors = []

    for i, domain in enumerate(all_domains):
        if domain in already_done:
            continue

        print(f"  [{i + 1}/{len(all_domains)}]", end=" ")

        result = catalog_domain(domain, verbose=True)

        if result:
            results[domain] = result
        else:
            errors.append(domain)
            results[domain] = None

        # Save checkpoint every 10 domains.
        if (i + 1) % 10 == 0:
            catalog["domains"] = results

            catalog["_meta"] = {
                "last_updated": datetime.now(
                    timezone.utc
                ).isoformat(),
                "domains_cataloged": len([
                    value
                    for value in results.values()
                    if value
                ]),
                "domains_failed": len(errors)
            }

            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(catalog, f, indent=2)

            print(
                f"\n  Checkpoint saved "
                f"({i + 1} domains processed)\n"
            )

        time.sleep(0.2)

    # Final save.
    catalog["domains"] = results

    catalog["_meta"] = {
        "last_updated": datetime.now(
            timezone.utc
        ).isoformat(),
        "domains_cataloged": len([
            value
            for value in results.values()
            if value
        ]),
        "domains_failed": len(errors),
        "failed_domains": errors
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"  Complete. {len(results)} domains processed.")
    print(f"  Failed: {len(errors)}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Catalog datasets on Socrata domains"
    )

    parser.add_argument(
        "--domain",
        help="Single domain to catalog"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Catalog all domains from domains file"
    )

    parser.add_argument(
        "--domains-file",
        default="socrata_domains.json",
        help="Domain list from discover.py"
    )

    parser.add_argument(
        "--top",
        type=int,
        help="Only catalog top N domains"
    )

    parser.add_argument(
        "--out",
        default="socrata_catalog.json",
        help="Output file"
    )

    args = parser.parse_args()

    if args.domain:
        run_single(args.domain, args.out)

    elif args.all:
        run_all(
            args.domains_file,
            args.out,
            args.top
        )

    else:
        parser.print_help()

        print("\nExamples:")
        print(
            "  python catalog.py "
            "--domain data.austintexas.gov"
        )
        print(
            "  python catalog.py "
            "--all --domains-file socrata_domains.json"
        )
        print(
            "  python catalog.py --all --top 50"
        )

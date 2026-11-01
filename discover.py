
#!/usr/bin/env python3
"""
discover.py
===========
Discovers unique Socrata publishing domains from the global catalog.

The catalog API limits this script to the first 10,000 results.
The output records whether the scan completed or was interrupted.

Usage:
    python discover.py
    python discover.py --out socrata_domains.json

Output:
    socrata_domains.json
    - Domain names
    - Dataset counts per domain
    - Sample dataset names
    - Scan metadata and completion status
"""

import json
import sys
import time
import urllib.request
import urllib.error
import argparse
from collections import defaultdict

CATALOG_URL = "https://api.us.socrata.com/api/catalog/v1"
PAGE_SIZE = 100
MAX_RESULTS = 10000


def fetch(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "DataScraperBot/1.0"}
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))

        except Exception as e:
            if attempt == retries - 1:
                raise

            print(f"  Retry {attempt + 1} after error: {e}")
            time.sleep(2 ** attempt)


def discover(out_path="socrata_domains.json"):
    print("Discovering Socrata publishing domains...")
    print(f"  Source: {CATALOG_URL}")
    print()

    domain_counts = defaultdict(int)
    domain_names = {}

    offset = 0
    total = None
    scan_complete = False
    scan_error = None

    while True:
        url = (
            f"{CATALOG_URL}?only=datasets"
            f"&limit={PAGE_SIZE}"
            f"&offset={offset}"
        )

        try:
            data = fetch(url)

        except Exception as e:
            scan_error = str(e)
            print(f"  ERROR at offset {offset}: {e}")
            break

        results = data.get("results", [])

        if total is None:
            total = data.get("resultSetSize", 0)
            print(f"  Total datasets in catalog: {total}")

        if not results:
            scan_complete = True
            break

        for item in results:
            domain = item.get("metadata", {}).get("domain", "")

            if domain:
                domain_counts[domain] += 1

                if domain not in domain_names:
                    domain_names[domain] = (
                        item.get("resource", {}).get("name", "")
                    )

        offset += PAGE_SIZE

        done = min(offset, total)
        pct = (done / total * 100) if total else 0

        print(
            f"  Scanned {done:,}/{total:,} "
            f"({pct:.0f}%) — "
            f"{len(domain_counts)} unique domains so far",
            end="\r"
        )

        sys.stdout.flush()

        if offset >= total:
            scan_complete = True
            break

        if offset >= MAX_RESULTS:
            break

        time.sleep(0.1)

    print()
    print(
        f"\n  Scan ended. "
        f"Found {len(domain_counts)} unique domains."
    )

    # Sort by dataset count descending.
    sorted_domains = sorted(
        domain_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )

    output = {
        "_meta": {
            "total_datasets_scanned": min(
                offset,
                total or offset,
                MAX_RESULTS
            ),
            "catalog_result_count": total,
            "unique_domains": len(domain_counts),
            "scan_complete": scan_complete,
            "result_limit_reached": (
                offset >= MAX_RESULTS
                and total is not None
                and total > MAX_RESULTS
            ),
            "error": scan_error,
            "note": (
                "Results are sourced from the public Socrata catalog. "
                "The catalog includes government and non-government "
                "publishing domains. A scan may be limited to the "
                "first 10,000 catalog results."
            )
        },
        "domains": [
            {
                "domain": domain,
                "dataset_count": count,
                "sample_dataset": domain_names.get(domain, "")
            }
            for domain, count in sorted_domains
        ]
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"  Saved to {out_path}")
    print()
    print("  Top 20 domains by dataset count:")
    print(f"  {'DOMAIN':<45} {'DATASETS':>8}")
    print(f"  {'-' * 45} {'-' * 8}")

    for domain, count in sorted_domains[:20]:
        print(f"  {domain:<45} {count:>8}")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Discover Socrata publishing domains"
    )

    parser.add_argument(
        "--out",
        default="socrata_domains.json",
        help="Output file path"
    )

    args = parser.parse_args()
    discover(args.out)

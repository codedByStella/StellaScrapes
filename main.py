
#!/usr/bin/env python3
"""
Public Records Platform
========================
A modular platform for searching and processing public datasets.

Usage:
    python main.py           # Interactive menu
    python main.py search    # Interactive search prompt
    python main.py discover
    python main.py catalog
    python main.py cities
    python main.py test
"""

import sys
import os
import csv

# ── Constants ─────────────────────────────────────────────────────────────────

VERSION = "1.0.0"
OUTPUT_DIR = "./output"

BANNER = """
╔══════════════════════════════════════════════════════════╗
║         PUBLIC RECORDS PLATFORM  v{ver:<20}  ║
║         Data discovery and record processing.           ║
╚══════════════════════════════════════════════════════════╝
""".format(ver=VERSION)

MENU = """
  [1]  Search           Search available public datasets
  [2]  Cities           List cities in the registry
  [3]  Discover         Discover publishing domains
  [4]  Catalog          Catalog datasets across domains
  [5]  Test             Run test suite
  [Q]  Quit
"""

SEARCH_HELP = """
  SEARCH:
    Enter a query describing the records you want to find.

    The search router interprets the query and selects
    an applicable dataset from the registry.

    Search syntax and proprietary query-processing details
    are intentionally omitted from this public version.
"""

# ── Imports (deferred so menu loads fast) ─────────────────────────────────────

def _import_router():
    from router import route, export_csv, REGISTRY
    return route, export_csv, REGISTRY


def _import_clean():
    from clean_permits import (
        clean,
        export_csv as export_clean_csv,
        export_excel,
        clean_generic,
        export_csv_generic,
        export_excel_generic,
    )
    return (
        clean,
        export_clean_csv,
        export_excel,
        clean_generic,
        export_csv_generic,
        export_excel_generic,
    )


def _import_discover():
    from discover import discover
    return discover


def _import_catalog():
    from catalog import run_all, run_single
    return run_all, run_single


# ── Search ────────────────────────────────────────────────────────────────────

def cmd_search(query: str = None):
    route, export_csv, REGISTRY = _import_router()

    if not query:
        print(SEARCH_HELP)
        try:
            query = input("  Search > ").strip()
        except (KeyboardInterrupt, EOFError):
            return

        if not query:
            return

    print(f"\n  Searching: '{query}' ...")
    print()

    result = route(query)

    if result.query.get("_fuzzy_match"):
        print(f"  ~ Matched: {result.query['_fuzzy_match']}")

    if result.error:
        print(f"  ✗ {result.error}\n")
        return

    if result.count == 0:
        print(f"  No results for '{query}'")
        print("  Try broadening the query or date range.\n")
        return

    print(
        f"\n  ✓ {result.count} records  |  "
        f"{result.city}  |  last {result.days} days"
    )

    if result.trade:
        print(f"    Filter: {result.trade}")

    print()

    # Select a useful secondary column based on record type.
    has_contractor = result.data_type == "permits"
    has_name = result.data_type in (
        "business_licenses",
        "foreclosures",
        "evictions",
        "tax_liens",
    )

    if has_contractor:
        print(f"  {'DATE':<12} {'ADDRESS':<36} {'TYPE':<22} {'CONTRACTOR'}")
        print(f"  {'-'*12} {'-'*36} {'-'*22} {'-'*25}")
    elif has_name:
        print(f"  {'DATE':<12} {'ADDRESS':<36} {'TYPE':<22} {'NAME'}")
        print(f"  {'-'*12} {'-'*36} {'-'*22} {'-'*25}")
    else:
        print(f"  {'DATE':<12} {'ADDRESS':<36} {'TYPE':<22} {'DESCRIPTION'}")
        print(f"  {'-'*12} {'-'*36} {'-'*22} {'-'*35}")

    for record in result.records[:10]:
        if has_contractor:
            extra = (record.get("contractor") or "—")[:30]
        elif has_name:
            extra = (record.get("name") or "—")[:30]
        else:
            extra = (record.get("description") or "—")[:35]

        print(
            f"  {record.get('date', '')[:10]:<12} "
            f"{record.get('address', '')[:35]:<36} "
            f"{record.get('record_type', '')[:21]:<22} "
            f"{extra}"
        )

    if result.count > 10:
        print(f"\n  ... and {result.count - 10} more records")

    print()

    try:
        choice = input("  Export results to CSV + Excel? (y/n): ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        return

    if choice == "y":
        raw_path = export_csv(result, OUTPUT_DIR)

        (
            clean,
            export_clean_csv,
            export_excel,
            clean_generic,
            export_csv_generic,
            export_excel_generic,
        ) = _import_clean()

        with open(raw_path, newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))

        base = (
            os.path.splitext(os.path.basename(raw_path))[0]
            .replace("_raw", "")
        )

        csv_path = os.path.join(OUTPUT_DIR, f"{base}_clean.csv")
        excel_path = os.path.join(OUTPUT_DIR, f"{base}_clean.xlsx")

        if result.data_type == "permits":
            cleaned = clean(rows)

            if cleaned:
                export_clean_csv(cleaned, csv_path)
                export_excel(cleaned, excel_path)

                print("\n  ✓ Files saved to ./output/")
                print(f"    {os.path.basename(csv_path)}")
                print(f"    {os.path.basename(excel_path)}")

        else:
            cleaned = clean_generic(rows)

            if cleaned:
                export_csv_generic(cleaned, csv_path)
                export_excel_generic(cleaned, excel_path)

                print("\n  ✓ Files saved to ./output/")
                print(f"    {os.path.basename(csv_path)}")
                print(f"    {os.path.basename(excel_path)}")

                print("\n  PREVIEW (top 5):")

                for record in cleaned[:5]:
                    name = record.get("name", "—")[:35]
                    address = record.get("address", "—")[:35]
                    record_type = record.get("record_type", "")[:20]

                    print(
                        f"    {record.get('date', ''):<12} "
                        f"{name:<36} "
                        f"{address:<36} "
                        f"{record_type}"
                    )

    print()


# ── Cities ────────────────────────────────────────────────────────────────────

# Platforms with a working fetch adapter in router.py.
# Keep this synchronized with the router implementation.

IMPLEMENTED_PLATFORMS = {"socrata"}


def cmd_cities():
    _, __, REGISTRY = _import_router()
    cities = REGISTRY.get("cities", {})

    print(
        f"\n  {'CITY':<26} {'STATE':<6} "
        f"{'PLATFORM':<10} {'DATA TYPES'}"
    )
    print(
        f"  {'-'*26} {'-'*6} "
        f"{'-'*10} {'-'*35}"
    )

    by_pop = sorted(
        cities.items(),
        key=lambda item: item[1].get("population", 0),
        reverse=True,
    )

    for key, config in by_pop:
        datasets = config.get("datasets", {})

        platform_set = {
            dataset.get("platform", "?")
            for dataset in datasets.values()
        }

        platform_str = "/".join(sorted(platform_set))

        def _mark(dataset_key, dataset_config):
            if dataset_config.get("dataset_id", "TODO") == "TODO":
                return f"{dataset_key} (todo)"

            if dataset_config.get("platform") not in IMPLEMENTED_PLATFORMS:
                return f"{dataset_key} (no adapter)"

            return f"{dataset_key} ✓"

        types_str = ", ".join(
            _mark(dataset_key, dataset_config)
            for dataset_key, dataset_config in datasets.items()
        )

        print(
            f"  {config['display']:<26} "
            f"{config['state']:<6} "
            f"{platform_str:<10} "
            f"{types_str}"
        )

    print(f"\n  Total: {len(cities)} cities\n")


# ── Discover ──────────────────────────────────────────────────────────────────

def cmd_discover():
    discover = _import_discover()

    print("\n  This will query the Socrata global catalog and")
    print("  collect publishing domains.")
    print("  Output: socrata_domains.json\n")

    try:
        confirm = input("  Start? (y/n): ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        return

    if confirm == "y":
        discover("socrata_domains.json")


# ── Catalog ───────────────────────────────────────────────────────────────────

def cmd_catalog():
    run_all, run_single = _import_catalog()

    print("\n  [1]  Catalog all discovered domains")
    print("  [2]  Catalog a single domain")
    print("  [B]  Back\n")

    try:
        choice = input("  Choice > ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        return

    if choice == "1":
        if not os.path.exists("socrata_domains.json"):
            print(
                "\n  ✗ socrata_domains.json not found. "
                "Run Discover first.\n"
            )
            return

        try:
            top_input = input(
                "  Catalog top N domains (blank = all): "
            ).strip()

            top = int(top_input) if top_input.isdigit() else None

        except (KeyboardInterrupt, EOFError):
            return

        run_all(
            "socrata_domains.json",
            "socrata_catalog.json",
            top=top,
        )

    elif choice == "2":
        try:
            domain = input("  Domain > ").strip()
        except (KeyboardInterrupt, EOFError):
            return

        if domain:
            run_single(domain, "socrata_catalog.json")


# ── Proprietary functionality withheld ───────────────────────────────────────

# [REDACTED]
#
# The production application includes an additional prospect-generation
# workflow.
#
# Its implementation, source-specific collection logic, category
# configuration, and operational details are intentionally omitted.
#
# The public version does not expose or replace that functionality.


# ── Test ──────────────────────────────────────────────────────────────────────

def cmd_test():
    import subprocess

    # test_router.py is a standalone script with its own
    # pass/fail reporting. Run it directly rather than through pytest.

    print("\n  Running test suite...\n")

    result = subprocess.run(
        [sys.executable, "test_router.py"],
        capture_output=False,
    )

    if result.returncode != 0:
        print(
            "\n  Test runner exited with an error. "
            "Check output above.\n"
        )
    else:
        print(
            "\n  Test run complete — "
            "see PASS/WARN/FAIL summary above.\n"
        )


# ── Interactive Menu ──────────────────────────────────────────────────────────

def interactive():
    print(BANNER)
    print(MENU)

    while True:
        try:
            choice = input("  > ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n  Bye.")
            break

        if not choice:
            continue

        elif choice in ("q", "quit", "exit"):
            print("  Bye.")
            break

        elif choice in ("1", "search", "s"):
            cmd_search()
            print(MENU)

        elif choice in ("2", "cities", "city", "c"):
            cmd_cities()

        elif choice in ("3", "discover", "d"):
            cmd_discover()

        elif choice in ("4", "catalog"):
            cmd_catalog()

        elif choice in ("5", "test", "t"):
            cmd_test()

        elif choice in ("help", "?", "h"):
            print(MENU)

        else:
            # Treat unrecognized menu input as a search query.
            cmd_search(choice)


# ── CLI dispatch ──────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    if not args:
        interactive()
        return

    cmd = args[0].lower()

    if cmd == "search":
        query = " ".join(args[1:]) if len(args) > 1 else None
        cmd_search(query)

    elif cmd in ("cities", "city"):
        cmd_cities()

    elif cmd == "discover":
        cmd_discover()

    elif cmd == "catalog":
        cmd_catalog()

    elif cmd == "test":
        cmd_test()

    elif cmd in ("help", "--help", "-h"):
        print(__doc__)

    else:
        # Treat the full argument string as a search query.
        cmd_search(" ".join(args))


if __name__ == "__main__":
    main()

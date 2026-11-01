
#!/usr/bin/env python3
"""
StellaScrapes — Public Release Tests

Tests the functionality retained in the public-release router.

The production query parser, location matching, API retrieval,
normalization, and filtering implementations have been withheld.

[REDACTED]
- Production query parsing test cases.
- Source-specific registry coverage tests.
- Production routing and adapter tests.
- Live API integration tests.
"""

import csv
import tempfile
import unittest
from pathlib import Path

from router import (
    RouterResult,
    export_csv,
    get_registry,
    load_registry,
    route,
)


class RegistryTests(unittest.TestCase):

    def test_registry_loads(self):
        registry = load_registry()

        self.assertIsInstance(registry, dict)

    def test_registry_access(self):
        registry = get_registry()

        self.assertIsInstance(registry, dict)


class RouterInterfaceTests(unittest.TestCase):

    def test_route_returns_result(self):
        result = route("public release test")

        self.assertIsInstance(result, RouterResult)

    def test_result_contains_expected_attributes(self):
        result = route("public release test")

        self.assertTrue(hasattr(result, "records"))
        self.assertTrue(hasattr(result, "query"))
        self.assertTrue(hasattr(result, "city"))
        self.assertTrue(hasattr(result, "data_type"))
        self.assertTrue(hasattr(result, "trade"))
        self.assertTrue(hasattr(result, "days"))
        self.assertTrue(hasattr(result, "error"))
        self.assertTrue(hasattr(result, "count"))

    def test_search_reports_withheld_implementation(self):
        result = route("public release test")

        self.assertEqual(result.records, [])
        self.assertEqual(result.count, 0)
        self.assertIsNotNone(result.error)

    def test_result_representation(self):
        result = RouterResult(
            records=[],
            query_parsed={},
            city_display="Test",
            data_type="permits",
            trade=None,
            days=7,
        )

        self.assertIn("RouterResult", repr(result))


class ExportTests(unittest.TestCase):

    def test_csv_export_creates_file(self):
        result = RouterResult(
            records=[
                {
                    "date": "2026-01-01",
                    "address": "123 Example Street",
                    "city": "Example City",
                    "record_type": "Test",
                    "description": "Example record",
                    "contractor": "Example Contractor",
                    "status": "Issued",
                    "url": "",
                }
            ],
            query_parsed={},
            city_display="Example City",
            data_type="permits",
            trade=None,
            days=7,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = export_csv(result, temp_dir)

            self.assertTrue(Path(output_path).is_file())

            with open(
                output_path,
                "r",
                encoding="utf-8",
                newline=""
            ) as file:
                rows = list(csv.DictReader(file))

            self.assertEqual(len(rows), 1)
            self.assertEqual(
                rows[0]["address"],
                "123 Example Street"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)

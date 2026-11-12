import csv
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from sales_pipeline.pipeline import read_sales_csv


class ReadSalesCsvTests(unittest.TestCase):
    def read_csv(self, rows: list[list[str]]) -> list:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sales.csv"
            with path.open("w", encoding="utf-8", newline="") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(
                    [
                        "order_id",
                        "order_date",
                        "customer_id",
                        "product_id",
                        "quantity",
                        "unit_price",
                    ]
                )
                writer.writerows(rows)
            return read_sales_csv(path)

    def test_reads_and_converts_a_valid_record(self) -> None:
        sales = self.read_csv(
            [["ORD-1", "2026-01-03", "CUST-1", "PROD-A", "2", "12.50"]]
        )

        self.assertEqual(len(sales), 1)
        self.assertEqual(sales[0].order_date, date(2026, 1, 3))
        self.assertEqual(sales[0].quantity, 2)
        self.assertEqual(sales[0].unit_price, Decimal("12.50"))

    def test_rejects_zero_quantity(self) -> None:
        with self.assertRaisesRegex(ValueError, "quantity must be greater than zero"):
            self.read_csv(
                [["ORD-1", "2026-01-03", "CUST-1", "PROD-A", "0", "12.50"]]
            )

    def test_rejects_date_that_is_not_yyyy_mm_dd(self) -> None:
        with self.assertRaisesRegex(ValueError, "order_date must use YYYY-MM-DD"):
            self.read_csv(
                [["ORD-1", "20260103", "CUST-1", "PROD-A", "1", "12.50"]]
            )

    def test_rejects_duplicate_order_ids_in_the_same_file(self) -> None:
        with self.assertRaisesRegex(ValueError, "repeats order_id"):
            self.read_csv(
                [
                    ["ORD-1", "2026-01-03", "CUST-1", "PROD-A", "1", "12.50"],
                    ["ORD-1", "2026-01-04", "CUST-2", "PROD-B", "1", "9.00"],
                ]
            )

    def test_rejects_missing_required_columns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sales.csv"
            path.write_text("order_id,quantity\nORD-1,2\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "missing required columns"):
                read_sales_csv(path)


if __name__ == "__main__":
    unittest.main()

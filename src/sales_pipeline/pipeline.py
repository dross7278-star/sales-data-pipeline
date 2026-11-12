import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from importlib.resources import files
from pathlib import Path


REQUIRED_COLUMNS = (
    "order_id",
    "order_date",
    "customer_id",
    "product_id",
    "quantity",
    "unit_price",
)


@dataclass(frozen=True)
class Sale:
    order_id: str
    order_date: date
    customer_id: str
    product_id: str
    quantity: int
    unit_price: Decimal


def read_sales_csv(path: str | Path) -> list[Sale]:
    """Read and validate the whole CSV before any records are loaded."""
    sales: list[Sale] = []
    seen_order_ids: set[str] = set()

    with Path(path).open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)):
            raise ValueError("CSV contains duplicate column names")

        missing_columns = [column for column in REQUIRED_COLUMNS if column not in headers]
        if missing_columns:
            raise ValueError(
                "CSV is missing required columns: " + ", ".join(missing_columns)
            )

        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"CSV row {row_number} has more values than its header")
            if all(value is None or not value.strip() for value in row.values()):
                continue
            sale = _parse_sale(row, row_number)
            if sale.order_id in seen_order_ids:
                raise ValueError(
                    f"CSV row {row_number} repeats order_id {sale.order_id!r}"
                )
            seen_order_ids.add(sale.order_id)
            sales.append(sale)

    return sales


def _parse_sale(row: dict[str, str | None], row_number: int) -> Sale:
    def required_text(column: str) -> str:
        value = row.get(column)
        if value is None or not value.strip():
            raise ValueError(f"CSV row {row_number}: {column} cannot be empty")
        return value.strip()

    order_id = required_text("order_id")
    customer_id = required_text("customer_id")
    product_id = required_text("product_id")

    raw_date = required_text("order_date")
    try:
        order_date = date.fromisoformat(raw_date)
    except ValueError as error:
        raise ValueError(
            f"CSV row {row_number}: order_date must use YYYY-MM-DD format"
        ) from error
    if order_date.isoformat() != raw_date:
        raise ValueError(
            f"CSV row {row_number}: order_date must use YYYY-MM-DD format"
        )

    raw_quantity = required_text("quantity")
    try:
        quantity = int(raw_quantity)
    except ValueError as error:
        raise ValueError(f"CSV row {row_number}: quantity must be a whole number") from error
    if quantity <= 0:
        raise ValueError(f"CSV row {row_number}: quantity must be greater than zero")

    raw_price = required_text("unit_price")
    try:
        unit_price = Decimal(raw_price)
    except InvalidOperation as error:
        raise ValueError(
            f"CSV row {row_number}: unit_price must be a valid number"
        ) from error
    if not unit_price.is_finite() or unit_price < 0:
        raise ValueError(
            f"CSV row {row_number}: unit_price must be zero or greater"
        )

    return Sale(
        order_id=order_id,
        order_date=order_date,
        customer_id=customer_id,
        product_id=product_id,
        quantity=quantity,
        unit_price=unit_price,
    )


def load_sales_to_postgres(sales: list[Sale], database_url: str) -> None:
    """Create the sales table if needed, then add new records in one transaction."""
    import psycopg

    schema = files("sales_pipeline").joinpath("schema.sql").read_text(encoding="utf-8")
    with psycopg.connect(database_url) as connection:
        connection.execute(schema)
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO sales (
                    order_id, order_date, customer_id, product_id, quantity, unit_price
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (order_id) DO UPDATE SET
                    order_date = EXCLUDED.order_date,
                    customer_id = EXCLUDED.customer_id,
                    product_id = EXCLUDED.product_id,
                    quantity = EXCLUDED.quantity,
                    unit_price = EXCLUDED.unit_price
                """,
                [
                    (
                        sale.order_id,
                        sale.order_date,
                        sale.customer_id,
                        sale.product_id,
                        sale.quantity,
                        sale.unit_price,
                    )
                    for sale in sales
                ],
            )

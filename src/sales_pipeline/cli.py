import argparse
import csv
import os
import sys

import psycopg

from sales_pipeline.pipeline import load_sales_to_postgres, read_sales_csv


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check a sales CSV file and load its records into PostgreSQL."
    )
    parser.add_argument("--input", required=True, help="Path to the sales CSV file")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL"),
        help="PostgreSQL connection URL (or set the DATABASE_URL environment variable)",
    )
    args = parser.parse_args()

    if not args.database_url:
        parser.error("set DATABASE_URL or provide --database-url")

    try:
        sales = read_sales_csv(args.input)
        load_sales_to_postgres(sales, args.database_url)
    except (OSError, ValueError, csv.Error) as error:
        print(f"Input error: {error}", file=sys.stderr)
        return 1
    except psycopg.Error as error:
        print(f"Database error: {error}", file=sys.stderr)
        return 1

    print(f"Finished loading {len(sales)} sales record(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

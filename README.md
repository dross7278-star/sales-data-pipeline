# Sales data pipeline

A small pipeline that checks sales data in a CSV file and loads it into PostgreSQL.
It also includes example SQL reports and tests.

## What goes in the CSV?

The file must have these columns:

| Column | Meaning | Example |
| --- | --- | --- |
| `order_id` | A unique ID for the sale | `ORD-1001` |
| `order_date` | The day the sale happened (`YYYY-MM-DD`) | `2026-01-03` |
| `customer_id` | The customer's ID | `CUST-01` |
| `product_id` | The product's ID | `PROD-A` |
| `quantity` | How many were sold (must be above zero) | `2` |
| `unit_price` | Price for one item (must be zero or more) | `12.50` |

See [data/sales.csv](data/sales.csv) for a sample.

## Run it

1. Install the project and its PostgreSQL driver:

   ```sh
   python -m pip install -e .
   ```

2. Start a local PostgreSQL database with Docker:

   ```sh
   docker compose up -d
   ```

3. Tell the program how to connect to the database, then load the sample:

   ```sh
   export DATABASE_URL=postgresql://sales:sales@localhost:5432/sales
   python -m sales_pipeline --input data/sales.csv
   ```

4. Open the dashboard:

   ```sh
   python -m sales_pipeline.web
   ```

   Then visit <http://127.0.0.1:5000> in your browser. The dashboard shows
   revenue, sales, items sold, average sale, monthly revenue, top products, and
   recent sales. Use the menu to change the reporting period.

The program checks the entire file before connecting to the database. If any row
is incorrect, it reports the row and stops without loading part of that file.
If a later file contains an existing `order_id`, its saved sale is updated
instead of creating a duplicate.

## See the reports

Run the queries in [sql/analytics.sql](sql/analytics.sql) using a PostgreSQL
client connected to the same database. The first report shows sales and revenue
by month; the second shows revenue and units sold by product.

## Run tests

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```

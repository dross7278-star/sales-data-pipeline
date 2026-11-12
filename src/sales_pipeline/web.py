import os
from datetime import date, timedelta
from decimal import Decimal

import psycopg
from flask import Flask, jsonify, render_template, request
from psycopg.rows import dict_row


app = Flask(__name__)

PERIODS = {
    "30": 30,
    "90": 90,
    "365": 365,
    "all": None,
}


@app.get("/")
def dashboard():
    return render_template("dashboard.html")


@app.get("/api/dashboard")
def dashboard_data():
    period = request.args.get("period", "365")
    if period not in PERIODS:
        return jsonify(error="Choose a period of 30, 90, 365, or all days."), 400

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return jsonify(error="DATABASE_URL is not set. See the README to start the dashboard."), 503

    days = PERIODS[period]
    start_date = date.today() - timedelta(days=days) if days is not None else None
    date_filter = "%s::date IS NULL OR order_date >= %s::date"
    parameters = (start_date, start_date)

    try:
        with psycopg.connect(database_url, row_factory=dict_row) as connection:
            metrics = connection.execute(
                f"""
                SELECT
                    COUNT(*) AS order_count,
                    COALESCE(SUM(quantity * unit_price), 0) AS revenue,
                    COALESCE(SUM(quantity), 0) AS units,
                    COALESCE(AVG(quantity * unit_price), 0) AS average_sale
                FROM sales
                WHERE {date_filter}
                """,
                parameters,
            ).fetchone()
            monthly_rows = connection.execute(
                f"""
                SELECT
                    date_trunc('month', order_date)::date AS month,
                    SUM(quantity * unit_price) AS revenue,
                    COUNT(*) AS order_count
                FROM sales
                WHERE {date_filter}
                GROUP BY 1
                ORDER BY 1
                """,
                parameters,
            ).fetchall()
            product_rows = connection.execute(
                f"""
                SELECT
                    product_id,
                    SUM(quantity * unit_price) AS revenue,
                    SUM(quantity) AS units
                FROM sales
                WHERE {date_filter}
                GROUP BY product_id
                ORDER BY revenue DESC, product_id
                LIMIT 5
                """,
                parameters,
            ).fetchall()
            recent_rows = connection.execute(
                f"""
                SELECT order_id, order_date, customer_id, product_id,
                       quantity, quantity * unit_price AS revenue
                FROM sales
                WHERE {date_filter}
                ORDER BY order_date DESC, order_id
                LIMIT 8
                """,
                parameters,
            ).fetchall()
    except psycopg.Error:
        app.logger.exception("Could not load sales dashboard data")
        return jsonify(
            error="Could not read sales from PostgreSQL. Check that the database is running and the sales table exists."
        ), 503

    return jsonify(
        period=period,
        metrics={
            "order_count": metrics["order_count"],
            "revenue": _money(metrics["revenue"]),
            "units": metrics["units"],
            "average_sale": _money(metrics["average_sale"]),
        },
        monthly=[
            {
                "month": row["month"].isoformat(),
                "revenue": _money(row["revenue"]),
                "order_count": row["order_count"],
            }
            for row in monthly_rows
        ],
        products=[
            {
                "product_id": row["product_id"],
                "revenue": _money(row["revenue"]),
                "units": row["units"],
            }
            for row in product_rows
        ],
        recent_sales=[
            {
                "order_id": row["order_id"],
                "order_date": row["order_date"].isoformat(),
                "customer_id": row["customer_id"],
                "product_id": row["product_id"],
                "quantity": row["quantity"],
                "revenue": _money(row["revenue"]),
            }
            for row in recent_rows
        ],
    )


def _money(amount: Decimal) -> str:
    return format(amount, ".2f")


if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
    )

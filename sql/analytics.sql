-- Revenue and number of sales records for each month.
SELECT
    date_trunc('month', order_date)::date AS month,
    SUM(quantity * unit_price) AS revenue,
    COUNT(*) AS sale_count
FROM sales
GROUP BY 1
ORDER BY 1;

-- Revenue grouped by product.
SELECT
    product_id,
    SUM(quantity * unit_price) AS revenue,
    SUM(quantity) AS units_sold
FROM sales
GROUP BY product_id
ORDER BY revenue DESC;

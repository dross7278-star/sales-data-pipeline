const currency = new Intl.NumberFormat(undefined, {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2,
});
const wholeNumber = new Intl.NumberFormat(undefined);
const periodSelect = document.querySelector("#period-select");
const message = document.querySelector("#dashboard-message");

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

function money(value) {
  return currency.format(Number(value) || 0);
}

function renderChart(months) {
  const chart = document.querySelector("#revenue-chart");
  if (!months.length) {
    chart.innerHTML = '<div class="empty-chart">No sales recorded in this period.</div>';
    return;
  }

  const width = 720;
  const height = 217;
  const left = 54;
  const right = 12;
  const top = 14;
  const bottom = 31;
  const plotWidth = width - left - right;
  const plotHeight = height - top - bottom;
  const values = months.map((item) => Number(item.revenue));
  const maxValue = Math.max(...values, 1);
  const points = values.map((value, index) => {
    const x = months.length === 1
      ? left + plotWidth / 2
      : left + (plotWidth * index) / (months.length - 1);
    const y = top + plotHeight - (value / maxValue) * plotHeight;
    return { x, y, value, month: months[index].month };
  });
  const line = points.map((point, index) =>
    `${index === 0 ? "M" : "L"} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`
  ).join(" ");
  const area = `${line} L ${points.at(-1).x.toFixed(1)} ${top + plotHeight} L ${points[0].x.toFixed(1)} ${top + plotHeight} Z`;
  const guideLines = [0, 1, 2, 3].map((step) => {
    const y = top + (plotHeight * step) / 3;
    const value = maxValue * (1 - step / 3);
    return `<line class="chart-grid" x1="${left}" y1="${y}" x2="${width - right}" y2="${y}"></line>
      <text class="chart-label" x="${left - 8}" y="${y + 3}" text-anchor="end">${escapeHtml(money(value))}</text>`;
  }).join("");
  const labels = points.map((point, index) => {
    if (points.length > 7 && index % Math.ceil(points.length / 6) !== 0 && index !== points.length - 1) return "";
    const label = new Date(`${point.month}T12:00:00`).toLocaleDateString(undefined, {
      month: "short",
      year: "2-digit",
    });
    return `<text class="chart-label" x="${point.x}" y="${height - 7}" text-anchor="middle">${escapeHtml(label)}</text>`;
  }).join("");
  const markers = points.map((point) =>
    `<circle class="chart-point" cx="${point.x}" cy="${point.y}" r="3.5"><title>${escapeHtml(point.month)}: ${escapeHtml(money(point.value))}</title></circle>`
  ).join("");

  chart.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Monthly revenue line chart">
    <defs><linearGradient id="chart-fill" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0%" stop-color="#8179ed" stop-opacity=".18"></stop>
      <stop offset="100%" stop-color="#8179ed" stop-opacity="0"></stop>
    </linearGradient></defs>
    ${guideLines}
    <path class="chart-area-fill" d="${area}"></path>
    <path class="chart-line" d="${line}"></path>
    ${markers}${labels}
  </svg>`;
}

function renderProducts(products) {
  const list = document.querySelector("#product-list");
  if (!products.length) {
    list.innerHTML = '<div class="no-products">No products to show yet.</div>';
    return;
  }
  const highest = Math.max(...products.map((product) => Number(product.revenue)), 1);
  list.innerHTML = products.map((product) => {
    const percent = Math.max((Number(product.revenue) / highest) * 100, 2);
    return `<div class="product-row">
      <div class="product-meta">
        <span class="product-name">${escapeHtml(product.product_id)}</span>
        <span class="product-revenue">${escapeHtml(money(product.revenue))}</span>
      </div>
      <div class="bar-track" aria-label="${escapeHtml(product.product_id)} revenue share">
        <div class="bar-fill" style="width:${percent.toFixed(1)}%"></div>
      </div>
      <span class="product-units">${wholeNumber.format(product.units)} items sold</span>
    </div>`;
  }).join("");
}

function renderSales(sales) {
  const rows = document.querySelector("#sales-rows");
  document.querySelector("#sales-count").textContent = `${sales.length} SHOWN`;
  if (!sales.length) {
    rows.innerHTML = '<tr><td class="empty-row" colspan="6">No sales recorded in this period.</td></tr>';
    return;
  }
  rows.innerHTML = sales.map((sale) => `<tr>
    <td>${escapeHtml(sale.order_id)}</td>
    <td>${escapeHtml(new Date(`${sale.order_date}T12:00:00`).toLocaleDateString())}</td>
    <td>${escapeHtml(sale.customer_id)}</td>
    <td>${escapeHtml(sale.product_id)}</td>
    <td>${wholeNumber.format(sale.quantity)}</td>
    <td class="amount">${escapeHtml(money(sale.revenue))}</td>
  </tr>`).join("");
}

function renderDashboard(data) {
  document.querySelector("#metric-revenue").textContent = money(data.metrics.revenue);
  document.querySelector("#metric-orders").textContent = wholeNumber.format(data.metrics.order_count);
  document.querySelector("#metric-units").textContent = wholeNumber.format(data.metrics.units);
  document.querySelector("#metric-average").textContent = money(data.metrics.average_sale);
  renderChart(data.monthly);
  renderProducts(data.products);
  renderSales(data.recent_sales);
}

async function loadDashboard() {
  message.hidden = true;
  periodSelect.disabled = true;
  try {
    const response = await fetch(`/api/dashboard?period=${encodeURIComponent(periodSelect.value)}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "The dashboard could not load.");
    renderDashboard(data);
  } catch (error) {
    message.textContent = error.message || "The dashboard could not load. Please try again.";
    message.hidden = false;
  } finally {
    periodSelect.disabled = false;
  }
}

periodSelect.addEventListener("change", loadDashboard);
loadDashboard();

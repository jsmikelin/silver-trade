(function () {
  "use strict";

  var FEED_URL = "/api/live-price.json";
  var FALLBACK_SOURCE_URL = "https://gold-api.com/docs";
  var PRODUCT_PREMIUMS = { bar: 0.30, grain: 0.50, powder: 0.80 };
  var chart = null;

  function element(id) {
    return document.getElementById(id);
  }

  function formatPrice(value) {
    return "$" + Number(value).toFixed(2);
  }

  function setText(id, value) {
    var target = element(id);
    if (target) target.textContent = value;
  }

  function setStatusContent(target, label, sourceName, sourceUrl) {
    if (!target) return;
    var link = document.createElement("a");
    link.href = sourceUrl;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = sourceName;
    target.replaceChildren(document.createTextNode(label + " · "), link);
  }

  function validateFeed(data) {
    if (!data || data.schema_version !== 2) return false;
    if (!Number.isFinite(data.price) || data.price <= 0) return false;
    if (!/^\d{4}-\d{2}-\d{2}$/.test(data.market_date || "")) return false;
    if (!Array.isArray(data.history) || data.history.length < 2) return false;
    if (!data.source || typeof data.source.name !== "string") return false;
    if (!/^https:\/\//.test(data.source.url || "")) return false;
    return data.history.every(function (point) {
      return /^\d{4}-\d{2}-\d{2}$/.test(point.date || "") &&
        Number.isFinite(point.price) && point.price > 0;
    });
  }

  function marketAgeDays(marketDate) {
    var published = new Date(marketDate + "T23:59:59Z");
    return Math.max(0, Math.floor((Date.now() - published.getTime()) / 86400000));
  }

  function updateStatus(data) {
    var status = element("priceDataStatus");
    var update = element("priceUpdateTime");
    var dateLabel = new Intl.DateTimeFormat("en-GB", {
      day: "2-digit", month: "short", year: "numeric", timeZone: "UTC"
    }).format(new Date(data.market_date + "T12:00:00Z"));
    var stale = marketAgeDays(data.market_date) > 5;
    var prefix = stale ? "Delayed market data" : "Daily market data";
    var sourceName = data.source.name;
    var sourceUrl = data.source.url;
    if (status) {
      setStatusContent(status, prefix + " · " + dateLabel, sourceName + " source", sourceUrl);
      status.dataset.state = stale ? "stale" : "current";
    }
    if (update) update.textContent = prefix + " · " + dateLabel;
  }

  function updatePrices(data) {
    var price = Number(data.price);
    var change = Number(data.change || 0);
    var changePct = Number(data.change_pct || 0);
    var sign = change >= 0 ? "+" : "";
    var changeElement = element("comexLiveChange");

    setText("comexLivePrice", formatPrice(price));
    setText("comexPrice", formatPrice(price));
    setText("silverBenchmarkLabel", data.benchmark);
    setText("silverPriceBarSource", data.benchmark);
    if (changeElement) {
      changeElement.textContent = sign + change.toFixed(2) + " (" +
        sign + changePct.toFixed(2) + "%)";
      changeElement.style.color = change >= 0 ? "#4ade80" : "#f87171";
    }

    Object.keys(PRODUCT_PREMIUMS).forEach(function (key) {
      var premium = PRODUCT_PREMIUMS[key];
      setText(key + "Price", formatPrice(price + premium));
      setText(key + "Premium", "+$" + premium.toFixed(2) + "/oz");
    });
    setText("spreadInfo", "Indicative prices based on daily silver data + product premium");
    updateStatus(data);
  }

  function drawChart(history) {
    var pricing = document.querySelector(".hero-pricing");
    if (!pricing || typeof window.Chart !== "function") return;
    var wrapper = document.querySelector(".hero-pricing-chart");
    if (!wrapper) {
      wrapper = document.createElement("div");
      wrapper.className = "hero-pricing-chart";
      wrapper.innerHTML = '<canvas id="priceTrendChart" aria-label="30 day silver price trend"></canvas>';
      pricing.appendChild(wrapper);
    }
    var canvas = element("priceTrendChart");
    if (!canvas) return;
    if (chart) chart.destroy();
    chart = new window.Chart(canvas.getContext("2d"), {
      type: "line",
      data: {
        labels: history.map(function (point) { return point.date.slice(5); }),
        datasets: [{
          label: "Silver Daily Average (USD/oz)",
          data: history.map(function (point) { return point.price; }),
          borderColor: "#e8b82f",
          backgroundColor: "rgba(232,184,47,0.14)",
          fill: true,
          borderWidth: 2.5,
          pointRadius: 0,
          pointHoverRadius: 4,
          tension: 0.25
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { intersect: false, mode: "index" },
        plugins: {
          legend: { position: "bottom", labels: { color: "#c8cfdd", boxWidth: 12 } },
          tooltip: {
            callbacks: {
              label: function (context) {
                return "Silver: $" + context.parsed.y.toFixed(3) + "/oz";
              }
            }
          }
        },
        scales: {
          x: {
            ticks: { color: "#98a2b5", maxTicksLimit: 6 },
            grid: { color: "rgba(255,255,255,0.08)" }
          },
          y: {
            ticks: {
              color: "#98a2b5",
              callback: function (value) { return "$" + Number(value).toFixed(2); }
            },
            grid: { color: "rgba(255,255,255,0.08)" }
          }
        }
      }
    });
  }

  function showUnavailable() {
    setText("comexLivePrice", "$--.--");
    setText("comexLiveChange", "Data unavailable");
    setText("priceUpdateTime", "Benchmark temporarily unavailable");
    var status = element("priceDataStatus");
    if (status) {
      setStatusContent(
        status,
        "Market data temporarily unavailable",
        "Check source",
        FALLBACK_SOURCE_URL
      );
      status.dataset.state = "error";
    }
  }

  async function loadPrices() {
    try {
      var response = await fetch(FEED_URL + "?v=" + Date.now(), {
        cache: "no-store",
        headers: { Accept: "application/json" }
      });
      if (!response.ok) throw new Error("HTTP " + response.status);
      var data = await response.json();
      if (!validateFeed(data)) throw new Error("Invalid silver feed schema");
      updatePrices(data);
      drawChart(data.history);
    } catch (error) {
      console.warn("[silver-pricing]", error);
      showUnavailable();
    }
  }

  function init() {
    loadPrices();
    window.setInterval(loadPrices, 6 * 60 * 60 * 1000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

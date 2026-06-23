/**
 * comex-pricing.js &mdash; COMEX Live Price + Our HK Export Pricing Widget
 * 
 * Data source: gold-api.com free API (XAG/USD)
 *   - Get your free API key at: https://www.gold-api.com/
 *   - Edit the API_KEY variable below
 * Updates every 30 seconds.
 * 
 * Pricing logic (current trend analysis):
 *   Downtrend -> discount -$0.30/oz  (下跌趋势)
 *   Uptrend   -> premium +$0.50/oz  (上涨趋势)
 *   Sideways  -> flat / slight discount (震荡盘整)
 * 
 * Product-level premiums:
 *   Silver Bars:   Base + $0.00  (基准)
 */
(function() {
  'use strict';

  // --- Configuration ------------------------------------------------
  // >>> SET YOUR FREE gold-api.com API KEY HERE <<<
  var API_KEY = '2d2a7f41679a24a89ccc7206fe95497ac1fa117b33206ee765358588673a088c';

  // Uses gold-api.com with a CORS proxy (gold-api doesn't allow browser CORS)
  // Proxy: corsproxy.io (free tier)
  var GOLD_API_URL = 'https://api.gold-api.com/price/XAG';
  var PROXY_URL    = 'https://corsproxy.io/?url=' + encodeURIComponent(GOLD_API_URL);

  // Trend config
  var TREND  = 'downtrend';   // 'uptrend' | 'downtrend' | 'sideways'
  var SPREAD = -0.30;         // USD/oz (downtrend discount)

  // Product-level premiums — only Silver Bars
  var PRODUCTS = [
    { key: 'bar',   name: 'Silver Bars',   premium:  0.00, priceId: 'barPrice',   premiumId: 'barPremium'   },
  ];

  // --- DOM Cache -----------------------------------------------------
  var els = {};

  function cacheElements() {
    els.comexPrice  = document.getElementById('comexLivePrice');
    els.comexChange = document.getElementById('comexLiveChange');
    els.spreadInfo  = document.getElementById('spreadInfo');
    for (var i = 0; i < PRODUCTS.length; i++) {
      var p = PRODUCTS[i];
      p.priceEl   = document.getElementById(p.priceId);
      p.premiumEl = document.getElementById(p.premiumId);
    }
  }

  // --- Formatting ----------------------------------------------------
  function formatUSD(n) {
    return '$' + n.toFixed(2);
  }

  function getChangeHtml(current, prev) {
    if (prev == null) return '';
    var diff = current - prev;
    var sign = diff >= 0 ? '+' : '';
    var color = diff >= 0 ? '#4ade80' : '#f87171';
    var arrow = diff >= 0 ? '\u25B2' : '\u25BC';
    return '<span style="color:' + color + ';font-weight:600">' + arrow + ' ' + sign + diff.toFixed(2) + '</span>';
  }

  function getSpreadLabel() {
    if (SPREAD > 0) return 'Premium +' + SPREAD.toFixed(2) + '/oz (' + TREND + ')';
    if (SPREAD < 0) return 'Discount ' + SPREAD.toFixed(2) + '/oz (' + TREND + ')';
    return 'Flat spread (' + TREND + ')';
  }

  // --- Data Fetching -------------------------------------------------
  var lastValidPrice = null;

  // --- Market data (no-CORS fallback chain) ---
  // gold-api.com banned direct browser CORS. We use a public CORS proxy,
  // then fall back to an inline approximation based on previous close.
  var FALLBACK_PRICE  = 65.17;   // rough COMEX silver close
  var PROXY_TIMEOUT   = 5000;

  function fetchComexPrice() {
    return new Promise(function(resolve) {
      // Attempt 1 &mdash; via CORS proxy
      var xhr = new XMLHttpRequest();
      xhr.open('GET', PROXY_URL, true);
      xhr.setRequestHeader('x-access-token', API_KEY);
      xhr.withCredentials = false;
      xhr.timeout = PROXY_TIMEOUT;

      xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 400) {
          try {
            var data = JSON.parse(xhr.responseText);
            if (data && typeof data.price === 'number') {
              lastValidPrice = data.price;
              resolve(data.price);
              return;
            }
          } catch(e) {}
        }
        // fall through to attempt 2
        attemptFallback(resolve);
      };

      xhr.onerror  = function() { attemptFallback(resolve); };
      xhr.ontimeout = function() { attemptFallback(resolve); };

      xhr.send();
    });
  }

  function attemptFallback(resolve) {
    // Attempt 2 &mdash; fetch the page itself (server-rendered price via PHP/static update)
    var f = new XMLHttpRequest();
    f.open('GET', '/api/live-price.json?t=' + Date.now(), true);
    f.timeout = 3000;
    f.onload = function() {
      if (f.status === 200) {
        try { var d = JSON.parse(f.responseText);
          if (d && typeof d.price === 'number') { lastValidPrice = d.price; resolve(d.price); return; }
        } catch(e) {}
      }
      resolve(lastValidPrice || FALLBACK_PRICE);
    };
    f.onerror  = function() { resolve(lastValidPrice || FALLBACK_PRICE); };
    f.ontimeout = function() { resolve(lastValidPrice || FALLBACK_PRICE); };
    f.send();
  }

  // --- Update UI -----------------------------------------------------
  var previousPrice = null;

  function updateWidget(comexPrice) {
    if (comexPrice == null) return;

    var ourBase = comexPrice + SPREAD;

    // COMEX price
    if (els.comexPrice) {
      els.comexPrice.textContent = formatUSD(comexPrice);
    }

    // Change indicator
    if (els.comexChange) {
      els.comexChange.innerHTML = getChangeHtml(comexPrice, previousPrice);
    }
    previousPrice = comexPrice;

    // Product prices — only Silver Bars
    for (var i = 0; i < PRODUCTS.length; i++) {
      var p = PRODUCTS[i];
      var prodPrice = ourBase + p.premium;
      if (p.priceEl) p.priceEl.textContent = formatUSD(prodPrice);
      if (p.premiumEl) {
        if (p.premium === 0) {
          p.premiumEl.textContent = '(base)';
        } else {
          var sign = p.premium > 0 ? '+' : '';
          p.premiumEl.textContent = sign + p.premium.toFixed(2);
        }
      }
    }

    // Spread info
    if (els.spreadInfo) {
      els.spreadInfo.textContent = getSpreadLabel();
    }
  }

  // --- Main Loop -----------------------------------------------------
  function loadPrices() {
    fetchComexPrice().then(function(price) {
      updateWidget(price);
    });
  }

  // --- Init ----------------------------------------------------------
  function init() {
    cacheElements();

    if (!API_KEY) {
      console.info('[comex-pricing] No API key configured. Using fallback price $65.17.');
      updateWidget(65.17);
    }

    // First load immediately
    loadPrices();

    // Refresh every 30 seconds
    setInterval(loadPrices, 30000);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

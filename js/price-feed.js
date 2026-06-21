/**
 * price-feed.js — Daily Silver Price Feed
 * Fetches SGE silver (ag0) and COMEX silver (SI) prices from Sina Finance.
 * Calculates SGE spot price excluding 13% VAT.
 * Displays in the homepage price bar.
 *
 * Formula: SGE Ex-VAT = SGE Price / 1.13
 * SGE 白银连续 = 元/千克
 * COMEX silver = 美元/盎司
 */
(function() {
  'use strict';

  const SGE_URL = 'https://hq.sinajs.cn/list=AG0';
  const COMEX_URL = 'https://hq.sinajs.cn/list=HF_SI';

  function parseSinaData(raw) {
    // Format: var hq_str_AG0="name,open,prev_close,price,high,low,...";
    const m = raw.match(/"(.*?)"/);
    if (!m) return null;
    const parts = m[1].split(',');
    return {
      name: parts[0],
      open: parseFloat(parts[1]),
      prevClose: parseFloat(parts[2]),
      price: parseFloat(parts[3]),
      high: parseFloat(parts[4]),
      low: parseFloat(parts[5]),
    };
  }

  function formatCNY(n) {
    return n.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
  }

  function formatUSD(n) {
    return n.toFixed(2);
  }

  function fetchPrice(url) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('GET', url, true);
      xhr.withCredentials = false;
      xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 400) {
          resolve(xhr.responseText);
        } else {
          reject(new Error('HTTP ' + xhr.status));
        }
      };
      xhr.onerror = function() {
        reject(new Error('Network error'));
      };
      xhr.ontimeout = function() {
        reject(new Error('Timeout'));
      };
      xhr.timeout = 8000;
      xhr.send();
    });
  }

  function updatePriceBar(sge, comex) {
    const sgeEl = document.getElementById('sgePrice');
    const comexEl = document.getElementById('comexPrice');
    const updateEl = document.getElementById('priceUpdateTime');

    if (sge) {
      // SGE 白银连续价格（元/千克），扣除13%增值税
      const exVatPrice = sge.price / 1.13;
      sgeEl.textContent = formatCNY(exVatPrice);
    }

    if (comex) {
      comexEl.textContent = formatUSD(comex.price);
    }

    if (updateEl) {
      const now = new Date();
      const dateStr = now.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
      const timeStr = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
      updateEl.textContent = 'Updated: ' + dateStr + ' ' + timeStr;
    }
  }

  async function loadPrices() {
    try {
      const [sgeRaw, comexRaw] = await Promise.all([
        fetchPrice(SGE_URL),
        fetchPrice(COMEX_URL),
      ]);

      const sge = parseSinaData(sgeRaw);
      const comex = parseSinaData(comexRaw);

      updatePriceBar(sge, comex);
    } catch (e) {
      console.warn('Price feed: failed to fetch, using fallback display');
      // Keep the "--" placeholders visible
    }
  }

  // Run on page load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadPrices);
  } else {
    loadPrices();
  }
})();

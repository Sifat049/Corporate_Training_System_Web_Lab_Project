/* =====================================================================
   charts.js - Vanilla JS diye <canvas> e bar chart ar donut chart (kono library lagbe na).
   Usage (template e):
     {{ charts|json_script:"chart-data" }}
     <canvas data-chart="bar" data-key="progress"></canvas>
   Banglish note: Canvas 2D API diye amra nijer haate rectangle (fillRect) ar arc (ctx.arc) aanki.
   ===================================================================== */
(function () {
  "use strict";
  var COLORS = ["#4f46e5", "#06b6d4", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#ec4899"];
  var tip = null;
  // Dark/light mode e chart er rong CSS variable theke ashe
  function themeColor(name, fallback) {
    var v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  }

  function tooltip() {
    if (!tip) {
      tip = document.createElement("div");
      tip.className = "chart-tip";
      document.body.appendChild(tip);
    }
    return tip;
  }

  function setup(canvas, height) {
    var dpr = window.devicePixelRatio || 1;
    var width = canvas.parentElement.clientWidth;
    canvas.style.width = width + "px";
    canvas.style.height = height + "px";
    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    var ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx: ctx, w: width, h: height };
  }

  function legend(canvas, items) {
    var holder = canvas.parentElement;
    var old = holder.querySelector(".legend");
    if (old) old.remove();
    var ul = document.createElement("ul");
    ul.className = "legend";
    items.forEach(function (it) {
      var li = document.createElement("li");
      li.innerHTML = '<i style="background:' + it.color + '"></i>' + it.label;
      ul.appendChild(li);
    });
    holder.appendChild(ul);
  }

  function shorten(text, max) {
    text = String(text);
    return text.length > max ? text.slice(0, max - 1) + "…" : text;
  }

  /* ---------- Bar chart (grouped) ---------- */
  function drawBar(canvas, cfg) {
    var height = parseInt(canvas.getAttribute("data-height"), 10) || 260;
    var s = setup(canvas, height), ctx = s.ctx;
    var labels = cfg.labels || [], sets = cfg.datasets || [];
    if (!labels.length) { empty(ctx, s, "No data yet"); return; }

    var all = [].concat.apply([], sets.map(function (d) { return d.values; }));
    var max = cfg.max || Math.max.apply(null, all.concat([1]));
    // Y axis er "bhalo" step ber kora (1, 2, 5, 10, 25 ...)
    var rough = max / 4, mag = Math.pow(10, Math.floor(Math.log10(rough)));
    var norm = rough / mag;
    var step = (norm <= 1 ? 1 : norm <= 2 ? 2 : norm <= 5 ? 5 : 10) * mag;
    if (step < 1) step = 1;
    if (cfg.max === 100) step = 25;
    max = Math.ceil(max / step) * step;

    var pad = { l: 36, r: 10, t: 12, b: 46 };
    var cw = s.w - pad.l - pad.r, ch = s.h - pad.t - pad.b;
    ctx.font = "12px sans-serif";
    ctx.strokeStyle = themeColor("--chart-grid", "#e5e7eb");
    ctx.fillStyle = themeColor("--chart-text", "#6b7280");
    ctx.textAlign = "right";
    for (var v = 0; v <= max; v += step) {
      var y = pad.t + ch - (v / max) * ch;
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(s.w - pad.r, y); ctx.stroke();
      ctx.fillText(v, pad.l - 6, y + 4);
    }
    var groupW = cw / labels.length;
    var barW = Math.min(36, (groupW * 0.7) / sets.length);
    var boxes = [];
    labels.forEach(function (label, i) {
      var gx = pad.l + i * groupW + (groupW - barW * sets.length) / 2;
      sets.forEach(function (d, j) {
        var val = d.values[i] || 0;
        var bh = (val / max) * ch;
        var x = gx + j * barW, y2 = pad.t + ch - bh;
        ctx.fillStyle = d.color || COLORS[j % COLORS.length];
        roundRect(ctx, x + 1, y2, barW - 2, bh, 4);
        boxes.push({ x: x, y: y2, w: barW, h: bh, text: label + " - " + d.label + ": " + val });
      });
      ctx.fillStyle = themeColor("--chart-label", "#374151");
      ctx.textAlign = "center";
      ctx.fillText(shorten(label, Math.max(4, Math.min(18, Math.floor(groupW / 7.5)))), pad.l + i * groupW + groupW / 2, s.h - pad.b + 18);
    });
    if (sets.length > 1) {
      legend(canvas, sets.map(function (d, j) { return { label: d.label, color: d.color || COLORS[j % COLORS.length] }; }));
    }
    hover(canvas, boxes);
  }

  function roundRect(ctx, x, y, w, h, r) {
    if (h <= 0) return;
    r = Math.min(r, h, w / 2);
    ctx.beginPath();
    ctx.moveTo(x, y + r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.lineTo(x + w, y + h);
    ctx.lineTo(x, y + h);
    ctx.closePath();
    ctx.fill();
  }

  /* ---------- Donut chart ---------- */
  function drawDonut(canvas, cfg) {
    var height = parseInt(canvas.getAttribute("data-height"), 10) || 220;
    var s = setup(canvas, height), ctx = s.ctx;
    var values = cfg.values || [], labels = cfg.labels || [];
    var total = values.reduce(function (a, b) { return a + b; }, 0);
    if (!total) { empty(ctx, s, "No data yet"); return; }
    var cx = s.w / 2, cy = s.h / 2, r = Math.min(cx, cy) - 8, inner = r * 0.62;
    var start = -Math.PI / 2, arcs = [];
    values.forEach(function (val, i) {
      var angle = (val / total) * Math.PI * 2;
      ctx.beginPath();
      ctx.arc(cx, cy, r, start, start + angle);
      ctx.arc(cx, cy, inner, start + angle, start, true);
      ctx.closePath();
      ctx.fillStyle = (cfg.colors && cfg.colors[i]) || COLORS[i % COLORS.length];
      ctx.fill();
      arcs.push({ from: start, to: start + angle, text: labels[i] + ": " + val });
      start += angle;
    });
    ctx.fillStyle = themeColor("--text", "#111827");
    ctx.font = "700 24px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(total, cx, cy + 4);
    ctx.font = "12px sans-serif";
    ctx.fillStyle = themeColor("--chart-text", "#6b7280");
    ctx.fillText("total", cx, cy + 20);
    legend(canvas, labels.map(function (l, i) { return { label: l + " (" + values[i] + ")", color: (cfg.colors && cfg.colors[i]) || COLORS[i % COLORS.length] }; }));

    canvas.onmousemove = function (e) {
      var rect = canvas.getBoundingClientRect();
      var dx = e.clientX - rect.left - cx, dy = e.clientY - rect.top - cy;
      var dist = Math.sqrt(dx * dx + dy * dy);
      var ang = Math.atan2(dy, dx);
      if (ang < -Math.PI / 2) ang += Math.PI * 2;
      var hit = dist >= inner && dist <= r ? arcs.filter(function (a) { return ang >= a.from && ang <= a.to; })[0] : null;
      showTip(hit ? hit.text : null, e);
    };
    canvas.onmouseleave = function () { showTip(null); };
  }

  function empty(ctx, s, msg) {
    ctx.fillStyle = themeColor("--chart-text", "#9ca3af");
    ctx.font = "14px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(msg, s.w / 2, s.h / 2);
  }

  function hover(canvas, boxes) {
    canvas.onmousemove = function (e) {
      var rect = canvas.getBoundingClientRect();
      var mx = e.clientX - rect.left, my = e.clientY - rect.top;
      var hit = boxes.filter(function (b) { return mx >= b.x && mx <= b.x + b.w && my >= b.y && my <= b.y + b.h; })[0];
      showTip(hit ? hit.text : null, e);
    };
    canvas.onmouseleave = function () { showTip(null); };
  }

  function showTip(text, e) {
    var t = tooltip();
    if (!text) { t.style.display = "none"; return; }
    t.textContent = text;
    t.style.display = "block";
    t.style.left = e.clientX + 12 + "px";
    t.style.top = e.clientY + 12 + "px";
  }

  function renderAll() {
    document.querySelectorAll("canvas[data-chart]").forEach(function (canvas) {
      var source = document.getElementById(canvas.getAttribute("data-source") || "chart-data");
      if (!source) return;
      var cfg = JSON.parse(source.textContent)[canvas.getAttribute("data-key")];
      if (!cfg) return;
      if (canvas.getAttribute("data-chart") === "donut") drawDonut(canvas, cfg);
      else drawBar(canvas, cfg);
    });
  }

  window.CTCharts = { render: renderAll };
  var timer;
  window.addEventListener("resize", function () { clearTimeout(timer); timer = setTimeout(renderAll, 150); });
  document.addEventListener("DOMContentLoaded", renderAll);
})();

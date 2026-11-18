/* =====================================================================
   app.js - Vanilla JavaScript (kono library nai)
   Banglish note:
   - DOM = browser e HTML er tree. document.querySelector() diye element dhori.
   - addEventListener() diye event (click, submit, input) er jonno function bandhi.
   ===================================================================== */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    initPageTitle();
    initSidebar();
    initMessages();
    initConfirmForms();
    initTableFilter();
    initPasswordToggle();
    initFileInputs();
    initProgressBars();
    initSubmitLock();
    initPasswordMatch();
    initTheme();
    initBell();
  });

  /* 0. Browser tab title = page heading + site name */
  function initPageTitle() {
    var h = document.getElementById("pageHeading");
    if (h) document.title = h.textContent.trim() + " | Corporate Training";
  }

  /* 1. Mobile sidebar open/close */
  function initSidebar() {
    var toggle = document.getElementById("menuToggle");
    var sidebar = document.getElementById("sidebar");
    var overlay = document.getElementById("overlay");
    if (!toggle || !sidebar) return;
    function close() {
      sidebar.classList.remove("open");
      overlay.classList.remove("show");
    }
    toggle.addEventListener("click", function () {
      sidebar.classList.toggle("open");
      overlay.classList.toggle("show");
    });
    overlay.addEventListener("click", close);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") close();
    });
  }

  /* 2. Success/error message gulo 6 second pore auto hide, X button e close */
  function initMessages() {
    document.querySelectorAll(".alert").forEach(function (alertBox) {
      var closeBtn = alertBox.querySelector(".close");
      function remove() {
        alertBox.style.transition = "opacity .3s";
        alertBox.style.opacity = "0";
        setTimeout(function () { alertBox.remove(); }, 300);
      }
      if (closeBtn) closeBtn.addEventListener("click", remove);
      if (alertBox.classList.contains("alert-success") || alertBox.classList.contains("alert-info")) {
        setTimeout(remove, 6000);
      }
    });
  }

  /* 3. Delete button e "Are you sure?" confirm: <form data-confirm="message"> */
  function initConfirmForms() {
    document.querySelectorAll("form[data-confirm]").forEach(function (form) {
      form.addEventListener("submit", function (e) {
        if (!window.confirm(form.getAttribute("data-confirm"))) {
          e.preventDefault();
          e.stopImmediatePropagation();
        }
      });
    });
  }

  /* 4. Live table search: <input data-table-filter="tableId"> */
  function initTableFilter() {
    document.querySelectorAll("[data-table-filter]").forEach(function (input) {
      var table = document.getElementById(input.getAttribute("data-table-filter"));
      if (!table) return;
      input.addEventListener("input", function () {
        var term = input.value.trim().toLowerCase();
        table.querySelectorAll("tbody tr").forEach(function (row) {
          row.style.display = row.textContent.toLowerCase().indexOf(term) === -1 ? "none" : "";
        });
      });
    });
  }

  /* 5. Password show/hide */
  function initPasswordToggle() {
    document.querySelectorAll("[data-toggle-password]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var input = btn.parentElement.querySelector("input");
        var show = input.type === "password";
        input.type = show ? "text" : "password";
        btn.textContent = show ? "Hide" : "Show";
      });
    });
  }

  /* 6. File upload: size check (client side) - server o abar check kore */
  function initFileInputs() {
    document.querySelectorAll('input[type="file"]').forEach(function (input) {
      input.addEventListener("change", function () {
        var maxMb = parseFloat(input.getAttribute("data-max-mb")) || 50;
        var file = input.files[0];
        if (file && file.size > maxMb * 1024 * 1024) {
          alert("File is too large. Maximum allowed size is " + maxMb + " MB.");
          input.value = "";
        }
      });
    });
  }

  /* 7. Progress bar animation: <span data-value="60"> */
  function initProgressBars() {
    document.querySelectorAll(".progress > span[data-value]").forEach(function (bar) {
      var value = Math.max(0, Math.min(100, parseInt(bar.getAttribute("data-value"), 10) || 0));
      setTimeout(function () { bar.style.width = value + "%"; }, 80);
    });
  }

  /* 8. Double submit atkano: submit er por button disable */
  /* 10. Dark mode toggle + notification bell dropdown (100% version) */
  function initTheme() {
    var btn = document.getElementById("themeToggle");
    if (!btn) return;
    btn.addEventListener("click", function () {
      var next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      try { localStorage.setItem("ct-theme", next); } catch (e) {}
      if (window.CTCharts) window.CTCharts.render();  // chart er rong bodle jay
    });
  }

  function initBell() {
    var btn = document.getElementById("bellBtn");
    var menu = document.getElementById("bellMenu");
    if (!btn || !menu) return;
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      var open = menu.classList.toggle("show");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.addEventListener("click", function (e) {
      if (!menu.contains(e.target)) { menu.classList.remove("show"); btn.setAttribute("aria-expanded", "false"); }
    });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") menu.classList.remove("show"); });
  }

  function initSubmitLock() {
    document.querySelectorAll("form[data-lock]").forEach(function (form) {
      form.addEventListener("submit", function () {
        var btn = form.querySelector('button[type="submit"]');
        if (btn) {
          setTimeout(function () {
            btn.disabled = true;
            btn.textContent = "Please wait...";
          }, 0);
        }
      });
    });
  }

  /* 9. Register form: password match live hint */
  function initPasswordMatch() {
    var p1 = document.getElementById("id_password1");
    var p2 = document.getElementById("id_password2");
    if (!p1 || !p2) return;
    var hint = document.createElement("small");
    hint.className = "help";
    p2.parentElement.appendChild(hint);
    function check() {
      if (!p2.value) { hint.textContent = ""; return; }
      var ok = p1.value === p2.value;
      hint.textContent = ok ? "Passwords match" : "Passwords do not match yet";
      hint.style.color = ok ? "#059669" : "#dc2626";
    }
    p1.addEventListener("input", check);
    p2.addEventListener("input", check);
  }
})();

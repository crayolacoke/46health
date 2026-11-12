/* Pricing page: filters and expand/collapse. */
(function () {
  var cats = Array.prototype.slice.call(document.querySelectorAll(".pr-cat"));
  var expand = document.getElementById("pr-expand");
  function syncExpand() { var all = cats.every(function (c) { return c.open; }); expand.textContent = all ? "Collapse all" : "Expand all"; }
  expand.addEventListener("click", function () { var open = !cats.every(function (c) { return c.open; }); cats.forEach(function (c) { c.open = open; }); syncExpand(); });
  cats.forEach(function (c) { c.addEventListener("toggle", syncExpand); });
  function match(row, f) {
    if (f === "under100") { var p = +row.getAttribute("data-price"); return p > 0 && p < 100; }
    if (f === "monthly") return row.getAttribute("data-monthly") === "1";
    if (f === "new") return row.getAttribute("data-new") === "1";
    return true;
  }
  document.querySelectorAll(".pr-filter").forEach(function (b) {
    b.addEventListener("click", function () {
      var f = b.getAttribute("data-filter");
      document.querySelectorAll(".pr-filter").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      cats.forEach(function (c) {
        var shown = 0;
        c.querySelectorAll(".pr-row").forEach(function (r) { var ok = match(r, f); r.hidden = !ok; if (ok) shown++; });
        c.querySelectorAll(".pr-group").forEach(function (g) {
          var n = g.nextElementSibling, any = false;
          while (n && n.classList.contains("pr-row")) { if (!n.hidden) any = true; n = n.nextElementSibling; }
          g.hidden = !any;
        });
        c.hidden = f !== "all" && shown === 0;
        c.querySelector(".pr-empty").hidden = shown > 0;
        if (f !== "all") c.open = shown > 0;
      });
      if (f === "all") cats.forEach(function (c, i) { c.open = i === 0; });
      syncExpand();
    });
  });
  syncExpand();
})();

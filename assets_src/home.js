/* 46 Health homepage: areas-of-care carousel, shop-by-goal tabs, floating consult-list bar. */
(function () {
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---- Carousel (scroll-snap track; buttons, dots, swipe, gentle autoplay)
  var hc = document.querySelector(".hc");
  if (hc) {
    var track = hc.querySelector(".hc-track");
    var slides = Array.prototype.slice.call(hc.querySelectorAll(".hc-slide"));
    var dots = Array.prototype.slice.call(hc.querySelectorAll(".hc-dot"));
    var cur = 0, timer = null, paused = false;
    function go(i, smooth) {
      cur = (i + slides.length) % slides.length;
      track.scrollTo({ left: slides[cur].offsetLeft - track.offsetLeft, behavior: smooth === false || reduce ? "auto" : "smooth" });
      mark();
    }
    function mark() {
      dots.forEach(function (d, j) { if (j === cur) d.setAttribute("aria-current", "true"); else d.removeAttribute("aria-current"); });
      slides.forEach(function (s, j) {
        s.setAttribute("aria-hidden", j === cur ? "false" : "true");
        s.querySelectorAll("a, button").forEach(function (el) { if (j === cur) el.removeAttribute("tabindex"); else el.setAttribute("tabindex", "-1"); });
        var m = s.querySelector(".hc-media"); if (m) m.setAttribute("tabindex", "-1");
      });
    }
    var st;
    track.addEventListener("scroll", function () {
      clearTimeout(st);
      st = setTimeout(function () {
        var w = track.clientWidth || 1, i = Math.round(track.scrollLeft / w);
        if (i !== cur) { cur = Math.max(0, Math.min(slides.length - 1, i)); mark(); }
      }, 80);
    }, { passive: true });
    hc.querySelector(".hc-prev").addEventListener("click", function () { go(cur - 1); restart(); });
    hc.querySelector(".hc-next").addEventListener("click", function () { go(cur + 1); restart(); });
    dots.forEach(function (d, j) { d.addEventListener("click", function () { go(j); restart(); }); });
    track.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight") { e.preventDefault(); go(cur + 1); restart(); }
      if (e.key === "ArrowLeft") { e.preventDefault(); go(cur - 1); restart(); }
    });
    function tick() { if (!paused && !document.hidden) go(cur + 1); }
    function restart() { if (reduce) return; clearInterval(timer); timer = setInterval(tick, 6000); }
    ["mouseenter", "focusin", "touchstart"].forEach(function (ev) { hc.addEventListener(ev, function () { paused = true; }, { passive: true }); });
    ["mouseleave", "focusout"].forEach(function (ev) { hc.addEventListener(ev, function () { paused = false; }); });
    window.addEventListener("resize", function () { go(cur, false); });
    mark(); restart();
  }

  // ---- Shop by goal tabs
  var tabs = Array.prototype.slice.call(document.querySelectorAll('.goal-tabs [role="tab"]'));
  function select(t, focus) {
    tabs.forEach(function (x) {
      var on = x === t;
      x.setAttribute("aria-selected", on ? "true" : "false");
      x.tabIndex = on ? 0 : -1;
      var p = document.getElementById(x.getAttribute("aria-controls"));
      if (p) p.hidden = !on;
    });
    if (focus) t.focus();
  }
  tabs.forEach(function (t, i) {
    t.addEventListener("click", function () { select(t); });
    t.addEventListener("keydown", function (e) {
      var k = e.key, n = null;
      if (k === "ArrowRight") n = tabs[(i + 1) % tabs.length];
      if (k === "ArrowLeft") n = tabs[(i - 1 + tabs.length) % tabs.length];
      if (k === "Home") n = tabs[0];
      if (k === "End") n = tabs[tabs.length - 1];
      if (n) { e.preventDefault(); select(n, true); }
    });
  });

  // ---- Floating consult-list bar (only when the list has something on it)
  var bar = document.querySelector(".float-bar");
  if (bar) {
    var num = bar.querySelector(".float-num");
    function sync() {
      var list = [];
      try { list = JSON.parse(localStorage.getItem("46h_consult_list") || "[]"); } catch (e) {}
      num.textContent = list.length;
      bar.hidden = list.length === 0;
      document.body.classList.toggle("has-float-bar", list.length > 0);
    }
    document.addEventListener("click", function (e) { if (e.target.closest && e.target.closest("[data-list-add]")) setTimeout(sync, 0); });
    window.addEventListener("storage", sync);
    sync();
  }
})();

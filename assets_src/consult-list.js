/* My Consult List page. The list lives only in this browser (localStorage). */
(function () {
  var KEY = "46h_consult_list", NOTES = "46h_consult_notes";
  var P = {}; (window.PRODUCTS || []).forEach(function (p) { P[p.slug] = p; });
  function get() { try { return JSON.parse(localStorage.getItem(KEY) || "[]").filter(function (s) { return P[s]; }); } catch (e) { return []; } }
  function set(v) { try { localStorage.setItem(KEY, JSON.stringify(v)); } catch (e) {} document.dispatchEvent(new Event("consultlist:change")); }
  var root = document.getElementById("consult-list");
  var actions = document.getElementById("list-actions");
  var notes = document.getElementById("list-notes");
  var msg = document.getElementById("list-msg");
  function el(tag, attrs, text) { var e = document.createElement(tag); for (var k in attrs || {}) e.setAttribute(k, attrs[k]); if (text != null) e.textContent = text; return e; }
  function say(t) { msg.textContent = t; msg.hidden = false; clearTimeout(say.t); say.t = setTimeout(function () { msg.hidden = true; }, 4000); }

  function render() {
    var list = get();
    root.innerHTML = "";
    actions.hidden = list.length === 0;
    document.getElementById("list-count-label").textContent = list.length ? list.length + (list.length === 1 ? " treatment" : " treatments") : "";
    if (!list.length) {
      var empty = el("div", { "class": "list-empty" });
      empty.appendChild(el("p", { "class": "list-empty-title" }, "Your list is empty."));
      empty.appendChild(el("p", null, "Tap the + on any treatment to add it here."));
      var a = el("a", { href: "treatments.html", "class": "list-browse" }, "Browse treatments");
      empty.appendChild(a);
      root.appendChild(empty);
      return;
    }
    // gentle notes for overlapping choices
    var names = {}, notesOut = [];
    list.forEach(function (s) { var n = P[s].name; names[n] = (names[n] || 0) + 1; });
    Object.keys(names).forEach(function (n) { if (names[n] > 1) notesOut.push("You’ve added more than one strength of " + n + ". Your provider will help you choose the right one."); });
    if (list.indexOf("semaglutide") > -1 && list.indexOf("tirzepatide") > -1) notesOut.push("Semaglutide and tirzepatide are alternatives. Your provider will help you choose between them.");
    notesOut.forEach(function (t) { root.appendChild(el("p", { "class": "list-note", role: "note" }, t)); });

    var ul = el("ul", { "class": "list-items" });
    list.forEach(function (s) {
      var p = P[s];
      var li = el("li", { "class": "list-item" });
      var img = el("img", { src: p.img, alt: "", "class": p.photo ? "li-photo" : "li-icon" });
      var thumb = el("a", { href: p.url, "class": "li-thumb", tabindex: "-1", "aria-hidden": "true" }); thumb.appendChild(img);
      var body = el("div", { "class": "li-body" });
      body.appendChild(el("div", { "class": "li-cat" }, p.category));
      var h = el("h3", { "class": "li-title" }); h.appendChild(el("a", { href: p.url }, p.title)); body.appendChild(h);
      if (p.summary) body.appendChild(el("p", { "class": "li-summary" }, p.summary));
      var price = el("div", { "class": "li-price" }, p.price + (p.unit ? " / " + p.unit : ""));
      var rm = el("button", { type: "button", "class": "li-remove no-print", "aria-label": "Remove " + p.title + " from your list" }, "Remove");
      rm.addEventListener("click", function () { set(get().filter(function (x) { return x !== s; })); render(); say("Removed " + p.title + "."); });
      var side = el("div", { "class": "li-side" }); side.appendChild(price); side.appendChild(rm);
      li.appendChild(thumb); li.appendChild(body); li.appendChild(side);
      ul.appendChild(li);
    });
    root.appendChild(ul);
  }

  function asText() {
    var lines = ["My 46 Health consult list", ""];
    get().forEach(function (s) { var p = P[s]; lines.push("• " + p.title + " — " + p.price + (p.unit ? " / " + p.unit : "")); });
    var n = (notes.value || "").trim();
    if (n) { lines.push("", "My questions:", n); }
    lines.push("", "Your provider decides what’s appropriate. This list isn’t an order.");
    return lines.join("\n");
  }

  // notes (saved in this browser only)
  try { notes.value = localStorage.getItem(NOTES) || ""; } catch (e) {}
  notes.addEventListener("input", function () { try { localStorage.setItem(NOTES, notes.value); } catch (e) {} });

  document.getElementById("list-print").addEventListener("click", function () { window.print(); });
  document.getElementById("list-copy").addEventListener("click", function () {
    var t = asText();
    function fallback() { var ta = el("textarea"); ta.value = t; document.body.appendChild(ta); ta.select(); try { document.execCommand("copy"); say("Copied to your clipboard."); } catch (e) { say("Couldn’t copy — try Print instead."); } ta.remove(); }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(function () { say("Copied to your clipboard."); }, fallback); else fallback();
  });
  document.getElementById("list-email").addEventListener("click", function () {
    location.href = "mailto:?subject=" + encodeURIComponent("My 46 Health consult list") + "&body=" + encodeURIComponent(asText());
  });
  var clear = document.getElementById("list-clear"), armed = false;
  clear.addEventListener("click", function () {
    if (!armed) { armed = true; clear.textContent = "Tap again to clear"; setTimeout(function () { armed = false; clear.textContent = "Clear list"; }, 4000); return; }
    set([]); armed = false; clear.textContent = "Clear list"; render(); say("Your list is cleared.");
  });
  render();
})();

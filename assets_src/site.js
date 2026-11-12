/* 46 Health — site settings and small behaviours.
 *
 * CONNECTING SERVICES: fill in the values below. Leave a value empty ("")
 * until the service exists; the site falls back to the waitlist page.
 */
window.SITE_CONFIG = {
  // Where every "Get Started" / "Start Your Consultation" button goes.
  // The product is appended as ?treatment=<slug> (e.g. ?treatment=bpc-157-15-mg).
  INTAKE_URL: "",

  // Patient portal / log in. The "Log In" button is hidden until this is set.
  PORTAL_URL: "",

  // Form endpoints (any service that accepts a POST of form fields and does
  // NOT require you to send health information, e.g. Klaviyo, Formspree).
  // Never point these at a service without a BAA if the form could collect
  // health information. The contact form asks people not to include any.
  FORMS: {
    waitlist: "",
    newsletter: "",
    contact: ""
  }
};

(function () {
  var C = window.SITE_CONFIG;

  // Consultation buttons
  document.querySelectorAll("[data-intake]").forEach(function (a) {
    if (!C.INTAKE_URL) return;
    var slug = a.getAttribute("data-intake");
    var url = C.INTAKE_URL;
    if (slug) url += (url.indexOf("?") === -1 ? "?" : "&") + "treatment=" + encodeURIComponent(slug);
    a.setAttribute("href", url);
  });

  // Portal / log in
  document.querySelectorAll("[data-portal]").forEach(function (a) {
    if (C.PORTAL_URL) a.setAttribute("href", C.PORTAL_URL);
    else a.style.display = "none";
  });

  // Waitlist: carry the treatment from the URL into the form
  var t = new URLSearchParams(location.search).get("treatment");
  document.querySelectorAll("input[name=treatment]").forEach(function (i) { if (t) i.value = t; });
  var tl = document.getElementById("waitlist-treatment");
  if (tl && t) {
    var label = document.querySelector('[data-treatment-name="' + t + '"]');
    tl.textContent = label ? label.textContent : "";
    tl.parentNode.hidden = !tl.textContent;
  }

  // Forms
  document.querySelectorAll("form[data-form]").forEach(function (f) {
    f.addEventListener("submit", function (e) {
      e.preventDefault();
      var kind = f.getAttribute("data-form");
      var endpoint = (C.FORMS || {})[kind];
      var msg = f.querySelector(".form-msg");
      function say(text) { if (msg) { msg.textContent = text; msg.hidden = false; } }
      if (!endpoint) { say("This form isn’t connected yet."); return; }
      fetch(endpoint, { method: "POST", body: new FormData(f), headers: { Accept: "application/json" } })
        .then(function (r) {
          if (!r.ok) throw new Error();
          f.reset();
          say(kind === "contact" ? "Thanks, we’ve got it. Our team will reply within one business day." : "You’re on the list. We’ll be in touch.");
        })
        .catch(function () { say("Something went wrong. Please try again."); });
    });
  });


  // My Consult List (stored only in this browser)
  var LKEY = "46h_consult_list";
  function lget() { try { return JSON.parse(localStorage.getItem(LKEY) || "[]"); } catch (e) { return []; } }
  function lset(v) { try { localStorage.setItem(LKEY, JSON.stringify(v)); } catch (e) {} }
  var toastEl;
  function toast(text, showLink) {
    if (!toastEl) { toastEl = document.createElement("div"); toastEl.className = "toast"; toastEl.setAttribute("role", "status"); document.body.appendChild(toastEl); }
    toastEl.textContent = text;
    if (showLink) { var a = document.createElement("a"); a.href = (document.querySelector(".list-link") || {}).getAttribute ? document.querySelector(".list-link").getAttribute("href") : "consult-list.html"; a.textContent = "View list"; toastEl.appendChild(a); }
    toastEl.hidden = false; clearTimeout(toast.t); toast.t = setTimeout(function () { toastEl.hidden = true; }, 3500);
  }
  function syncList() {
    var list = lget();
    document.querySelectorAll(".list-count").forEach(function (c) { c.textContent = list.length; c.hidden = list.length === 0; });
    document.querySelectorAll(".list-link").forEach(function (a) { a.setAttribute("aria-label", "My Consult List" + (list.length ? ", " + list.length + (list.length === 1 ? " treatment" : " treatments") : "")); });
    document.querySelectorAll("[data-list-add]").forEach(function (b) {
      var on = list.indexOf(b.getAttribute("data-list-add")) > -1, n = b.getAttribute("data-list-name");
      b.setAttribute("aria-pressed", on ? "true" : "false");
      if (b.classList.contains("list-toggle")) { var l = (on ? "Remove " : "Add ") + n + (on ? " from" : " to") + " My Consult List"; b.setAttribute("aria-label", l); b.title = on ? "On your consult list" : "Add to My Consult List"; }
    });
  }
  document.addEventListener("click", function (e) {
    var b = e.target.closest && e.target.closest("[data-list-add]");
    if (!b) return;
    var slug = b.getAttribute("data-list-add"), n = b.getAttribute("data-list-name"), list = lget(), i = list.indexOf(slug);
    if (i > -1) { list.splice(i, 1); toast("Removed " + n + " from your list."); } else { list.push(slug); toast("Added " + n + " to your list.", true); }
    lset(list); syncList();
  });
  document.addEventListener("consultlist:change", syncList);
  window.addEventListener("storage", syncList);
  syncList();

  // Mobile menu
  var btn = document.querySelector(".menu-btn");
  if (btn) btn.addEventListener("click", function () {
    var h = document.querySelector(".site-header");
    var open = h.classList.toggle("open");
    btn.setAttribute("aria-expanded", open ? "true" : "false");
  });
})();

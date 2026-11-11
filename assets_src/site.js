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
          say(kind === "contact" ? "Thanks — we’ll reply within one business day." : "Thanks — you’re on the list.");
        })
        .catch(function () { say("Something went wrong. Please try again."); });
    });
  });

  // Mobile menu
  var btn = document.querySelector(".menu-btn");
  if (btn) btn.addEventListener("click", function () {
    var h = document.querySelector(".site-header");
    var open = h.classList.toggle("open");
    btn.setAttribute("aria-expanded", open ? "true" : "false");
  });
})();

#!/usr/bin/env python3
"""46 Health static site generator.

    python3 build.py        -> writes the site into ./dist

Product names, prices and descriptions live in data/products.json (one place).
Page structure (which products appear in which group) is in PAGES below.
Service URLs (telehealth intake, portal, forms) are set in assets_src/site.js.
"""
import json, os, re, shutil, html

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
PRODUCTS = json.load(open(os.path.join(ROOT, "data", "products.json")))
BY_ID = {p["id"]: p for p in PRODUCTS}
for p in PRODUCTS:
    p.setdefault("groups", [])

# ---------------------------------------------------------------- tokens
BG, WHITE, TAUPE, NAVY, TAN, INK, MUTED, CARD = "#F2F0EA", "#FFFFFF", "#D3CCC4", "#141D21", "#C0AA96", "#141D21", "#4A545B", "#FAF9F6"
SERIF = "'Prata', Georgia, serif"
WRAP = "max-width: 1240px; margin: 0 auto; padding: 0 clamp(20px, 4vw, 40px)"
NARROW = "max-width: 880px; margin: 0 auto; padding: 0 clamp(20px, 4vw, 40px)"
EYEBROW = f"font-size: 13px; letter-spacing: 0.24em; color: {INK}; font-weight: 500; margin: 0 0 18px; text-transform: uppercase"
LABEL = f"font-size: 15px; letter-spacing: 0.04em; font-weight: 600; text-transform: uppercase; color: {INK}"
P = f"margin: 0; font-size: 16px; line-height: 1.6; color: {MUTED}"
ARROW = '<svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 8h12M9 3l5 5-5 5"/></svg>'
CHEV = f'<svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="{INK}" stroke-width="1.6"><path d="M3 6l5 5 5-5"/></svg>'
CHECK = f'<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="{INK}" stroke-width="1.8" aria-hidden="true"><path d="M2.5 7.5l3 3 6-6.5"/></svg>'
E = html.escape

import hashlib
def _asset_version():
    h = hashlib.sha1()
    for f in sorted(os.listdir(os.path.join(ROOT, "assets_src"))):
        p = os.path.join(ROOT, "assets_src", f)
        if os.path.isfile(p):
            h.update(open(p, "rb").read())
    h.update(open(os.path.join(ROOT, "data", "products.json"), "rb").read())
    return h.hexdigest()[:8]
ASSET_V = _asset_version()

PFX = ""  # relative prefix for the page being rendered ("" or "../")
def u(path): return PFX + path

def grid(minpx): return f"display: grid; grid-template-columns: repeat(auto-fit, minmax(min({minpx}px, 100%), 1fr))"
def grid_fill(minpx): return f"display: grid; grid-template-columns: repeat(auto-fill, minmax(min({minpx}px, 100%), 1fr))"

def H(tag, size, text, extra=""):
    lo = max(30, int(size * 0.6))
    return f'<{tag} style="margin: 0; font-family: {SERIF}; font-weight: 400; font-size: clamp({lo}px, {size/14.4:.2f}vw, {size}px); line-height: 1.12; color: {INK}; text-wrap: balance; {extra}">{text}</{tag}>'

def btn(label, href, kind="dark", extra="", attrs=""):
    s = {"dark": f"background: {NAVY}; color: #FFFFFF; border: 1px solid {NAVY}",
         "light": f"background: #FFFFFF; color: {NAVY}; border: 1px solid #FFFFFF",
         "ghost": f"background: #FFFFFF; color: {INK}; border: 1px solid #E4E1DB"}[kind]
    attrs = attrs.replace('class="', 'class="btn ', 1) if 'class="' in attrs else 'class="btn" ' + attrs
    return f'<a href="{href}" {attrs} style="display: inline-flex; align-items: center; justify-content: center; gap: 8px; min-height: 48px; padding: 0 28px; border-radius: 999px; {s}; font-size: 15px; font-weight: 500; text-decoration: none; white-space: nowrap; {extra}">{label}</a>'

def consult(label="Start Your Consultation", slug="", kind="dark", extra=""):
    q = f"?treatment={slug}" if slug else ""
    return btn(label, u("waitlist.html") + q, kind, extra, f'data-intake="{slug}"')

def link(label, href, extra=""):
    return f'<a href="{href}" style="display: inline-flex; align-items: center; gap: 8px; min-height: 44px; font-size: 15px; color: {INK}; text-decoration: none; font-weight: 500; {extra}">{label}{ARROW}</a>'

# ---------------------------------------------------------------- layout
CATEGORY_PAGES = [  # (file, nav title, card title, card blurb, image)
 ("weight-management.html", "Weight Management", "Weight Management", "Provider-guided programs using compounded GLP-1 medications, with ongoing check-ins.", "cat1.jpg"),
 ("peptides.html", "Peptides", "Peptides", "Provider-guided peptide therapies for recovery, vitality and cellular health.", "cat5.jpg"),
 ("skin-aesthetics.html", "Skin & Aesthetics", "Skin &amp; Aesthetics", "Pharmacy-made skin care, formulated for your skin and your goals.", "cat2.jpg"),
 ("mens-health.html", "Men’s Health & Sexual Wellness", "Men’s Health &amp; Sexual Wellness", "Care for energy, drive and healthy aging, built around you and your goals — plus prescription options for desire and intimacy.", "cat3.jpg"),
 ("womens-health.html", "Women’s Health & Sexual Wellness", "Women’s Health &amp; Sexual Wellness", "Care for energy, hormones and healthy aging at every stage of life — plus prescription options for desire and intimacy.", "cat4.jpg"),
]

def logo(size=40):
    return f'''<a href="{u('index.html')}" aria-label="46 Health home" style="display: flex; flex-direction: column; align-items: center; text-decoration: none; color: {INK}; line-height: 1"><span style="font-family: {SERIF}; font-size: {size}px; letter-spacing: -0.04em">46</span><span style="font-size: 8px; letter-spacing: 0.42em; margin-top: 4px; padding-left: 0.42em">HEALTH</span><span style="width: 14px; height: 1px; background: {INK}; margin: 4px 0"></span><span style="font-size: 8px; letter-spacing: 0.3em; padding-left: 0.3em">XX·XY</span></a>'''

def header(active):
    items = [("Treatments", "treatments.html"), ("How it works", "how-it-works.html"), ("Pricing", "pricing.html"), ("About", "about.html"), ("FAQ", "faq.html")]
    cur = ' aria-current="page"'
    links = "".join(f'<a href="{u(h)}"{cur if a == active else ""}>{a}</a>' for a, h in items)
    return f'''<a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="bar">
{logo()}
<nav class="site-nav" aria-label="Main">{links}</nav>
<div class="nav-actions"><a href="{u('consult-list.html')}" class="list-link" aria-label="My Consult List"><svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><rect x="5" y="3.5" width="14" height="17" rx="2"/><path d="M9 3.5V2.5h6v1M8.5 9h7M8.5 13h7M8.5 17h4"/></svg><span class="list-count" hidden></span></a>{btn("Log In", u("waitlist.html"), "ghost", "min-height: 44px; padding: 0 22px; font-size: 14px", 'class="login" data-portal')}{consult("Get Started", extra="min-height: 44px; padding: 0 24px; font-size: 14px").replace('class="btn"', 'class="btn cta"', 1)}
<button class="menu-btn" type="button" aria-label="Menu" aria-expanded="false"><svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true" fill="none" stroke="{INK}" stroke-width="1.5"><path d="M3 7h16M3 15h16"/></svg></button></div>
</div></header>'''

def footer():
    def col(t, ls):
        return f'<div><h2 style="margin: 0 0 18px; font-family: {SERIF}; font-weight: 400; font-size: 24px">{t}</h2><ul style="list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 4px">' + "".join(f'<li><a href="{u(h)}" style="font-size: 14px; letter-spacing: 0.04em; color: {INK}; text-decoration: none; min-height: 32px; display: flex; align-items: center; text-transform: uppercase">{l}</a></li>' for l, h in ls) + '</ul></div>'
    treat = [(c[2], c[0]) for c in CATEGORY_PAGES]
    return f'''<section style="background: {NAVY}; color: #FFFFFF; padding: 56px 0">
<div style="{WRAP}; display: flex; justify-content: space-between; align-items: center; gap: 40px; flex-wrap: wrap">
<div>{H("h2", 44, "Stay informed.<br>Choose excellence.", "color: #ADB7BD")}<p style="margin: 18px 0 0; font-size: 16px; line-height: 1.6; color: #F2F0EA; max-width: 380px">Notes on health, performance and longevity from our providers. No spam.</p></div>
<form data-form="newsletter" style="flex: 0 1 600px; display: flex; gap: 14px; flex-wrap: wrap; align-items: center"><label for="nl-email" class="sr-only">Email address</label><input id="nl-email" name="email" type="email" required autocomplete="email" placeholder="Email address" style="flex: 1 1 260px; min-height: 52px; border-radius: 999px; border: 1.5px solid #FFFFFF; background: transparent; color: #FFFFFF; padding: 0 24px; font: inherit; font-size: 15px"><button type="submit" style="min-height: 52px; padding: 0 34px; border-radius: 999px; background: #FFFFFF; color: {NAVY}; border: 0; font: inherit; font-size: 16px; font-weight: 500; cursor: pointer">Sign Up</button><p class="form-msg" role="status" hidden style="flex-basis: 100%; margin: 4px 0 0; font-size: 14px; color: #F2F0EA"></p></form>
</div></section>
<footer style="background: {BG}; padding: 64px 0 48px">
<div style="{WRAP}; {grid(260)}; gap: 48px">
<div><div style="display: inline-flex; flex-direction: column; align-items: center; line-height: 1"><span style="font-family: {SERIF}; font-size: 96px; letter-spacing: -0.05em">46</span><span style="font-size: 16px; letter-spacing: 0.5em; padding-left: 0.5em; margin-top: 8px">HEALTH</span><span style="width: 28px; height: 1px; background: {INK}; margin: 10px 0"></span><span style="font-size: 15px; letter-spacing: 0.4em; padding-left: 0.4em">XX·XY</span></div>
<p style="margin: 36px 0 0; font-size: 12px; line-height: 1.6; max-width: 360px">46 Health connects patients with independent licensed healthcare providers through telehealth. Prescriptions are issued only at a provider’s discretion after review of each patient’s medical history. Medications are prepared by SureCare Specialty Pharmacy, a licensed 503A compounding pharmacy in El Paso, Texas. Compounded medications are not FDA-approved; FDA does not review them for safety, effectiveness or quality. Information on this site is for educational purposes and is not medical advice. Individual results vary. If you are experiencing a medical emergency, call 911.</p></div>
<div style="display: flex; flex-direction: column; gap: 44px">{col("Treatments", treat)}{col("Support", [("FAQ", "faq.html"), ("Shipping", "faq.html#faq-2"), ("Refills", "faq.html#faq-2"), ("Contact", "contact.html")])}</div>
<div style="display: flex; flex-direction: column; gap: 44px">{col("Company", [("About", "about.html"), ("How it works", "how-it-works.html"), ("Pricing", "pricing.html"), ("Careers", "careers.html")])}{col("Legal", [("Terms of use", "terms.html"), ("Privacy policy", "privacy.html"), ("Notice of privacy practices", "notice-of-privacy-practices.html"), ("Telehealth consent", "telehealth-consent.html")])}</div>
</div></footer>
<div style="background: {TAN}; text-align: center; padding: 18px 16px; font-size: 15px">© 2026 46 Health. All rights reserved.</div>'''

def document(title, desc, body, active="", scripts=""):
    t = f"{title} | 46 Health" if title != "46 Health" else "46 Health — Physician-guided telehealth"
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(t)}</title>
<meta name="description" content="{E(desc)}">
<meta property="og:title" content="{E(t)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="46 Health">
<meta property="og:image" content="https://fortysixhealth.com/assets/img/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="46 Health">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://fortysixhealth.com/assets/img/og.jpg">
<link rel="apple-touch-icon" href="{u('assets/img/apple-touch-icon.png')}">
<link rel="icon" href="{u('assets/favicon.svg')}" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Prata&amp;family=Inter:wght@400;500;600&amp;display=swap" rel="stylesheet">
<link rel="stylesheet" href="{u('assets/site.css') + '?v=' + ASSET_V}">
</head>
<body>
{header(active)}
<main id="main">
{body}
</main>
{footer()}
<script src="{u('assets/site.js') + '?v=' + ASSET_V}"></script>{scripts}
</body>
</html>
'''

# ---------------------------------------------------------------- blocks
def hero(img, bgc, title, body, eyebrow="", buttons=""):
    eb = f'<p style="{EYEBROW}">{eyebrow}</p>' if eyebrow else ""
    rule = "" if eyebrow else f'<div style="width: 96px; height: 2px; background: {INK}; margin: 28px 0"></div>'
    bt = f'<div style="display: flex; gap: 20px; flex-wrap: wrap; align-items: center; margin-top: 36px">{buttons}</div>' if buttons else ""
    return f'''<section style="background: {bgc}; display: flex; flex-wrap: wrap; overflow: hidden">
<div class="hero-text" style="flex: 1 1 520px; display: flex; justify-content: flex-end; padding: 88px 56px 88px 40px">
<div style="width: 100%; max-width: 580px">{eb}{H("h1", 60, title)}{rule}<p style="margin: {"28px" if eyebrow else "0"} 0 0; font-size: 17px; line-height: 1.65; max-width: 540px">{body}</p>{bt}</div></div>
<div class="hero-img" style="flex: 1 1 480px; position: relative">
<img src="{u('assets/img/' + img)}" alt="" style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: center top">
<div style="position: absolute; top: 0; bottom: 0; left: 0; width: 120px; background: linear-gradient(90deg, {bgc}, rgba(0,0,0,0))"></div></div>
</section>'''

def centered_intro(title, body, crumbs=None):
    bc = ""
    if crumbs:
        bc = f'<nav aria-label="Breadcrumb" style="font-size: 13px; color: {MUTED}; margin-bottom: 28px">' + " &nbsp;/&nbsp; ".join(f'<a href="{u(h)}" style="color: {MUTED}">{t}</a>' if h else t for t, h in crumbs) + '</nav>'
    return f'<section style="padding: 56px 0 40px; text-align: center"><div style="{NARROW}">{bc}{H("h1", 60, title, "line-height: 1.08")}<div style="width: 96px; height: 2px; background: {INK}; margin: 28px auto"></div><p style="margin: 0 auto; font-size: 17px; line-height: 1.65; max-width: 620px">{body}</p></div></section>'

def cta_band():
    return f'''<section style="background: #ADB7BD; padding: 80px 0; text-align: center">
<div style="{NARROW}">{H("h2", 64, "Excellence is a practice.<br>Start yours today.", "line-height: 1.08")}
<p style="margin: 28px auto 0; font-size: 17px; line-height: 1.6; max-width: 560px">Start your consultation today for just $35. Your intake takes about 10 minutes, and a provider typically reviews it within 4 hours.</p>
<div style="margin-top: 40px">{consult()}</div></div></section>'''

def bignum_steps(steps):
    items = "".join(f'''<li style="position: relative; text-align: center; padding: 24px 12px; min-height: 220px">
<div aria-hidden="true" style="position: absolute; left: 50%; top: -10px; transform: translateX(-50%); font-family: {SERIF}; font-size: 220px; line-height: 1; color: {TAUPE}">{i}</div>
<div style="position: relative"><h3 style="margin: 0; {LABEL}; font-size: 18px; line-height: 1.4"><span class="sr-only">Step {i}: </span>{t}</h3><p style="margin: 18px auto 0; font-size: 16px; line-height: 1.6; max-width: 300px">{d}</p></div></li>''' for i, (t, d) in enumerate(steps, 1))
    return f'<ol style="list-style: none; margin: 0; padding: 0; {grid(280)}; gap: 56px 40px">{items}</ol>'

def icon(kind):
    paths = {
     "rx": '<rect x="12" y="8" width="24" height="32" rx="3"/><path d="M18 8v-2h12v2M19 20h10M24 15v10M18 31h12M18 35h8"/>',
     "dial": '<circle cx="24" cy="24" r="14"/><path d="M24 14v4M24 30v4M14 24h4M30 24h4M24 24l6-6"/>',
     "shield": '<path d="M24 6l14 5v11c0 9-6 16-14 20-8-4-14-11-14-20V11z"/><path d="M18 24l4 4 8-8"/>',
     "chat": '<path d="M8 12h26v18H18l-8 7v-7H8z"/><path d="M34 18h6v16h-4v6l-7-6h-9"/>',
     "search": '<circle cx="21" cy="21" r="11"/><path d="M29 29l10 10M17 21h8"/>',
     "flask": '<path d="M19 6h10M21 6v12L11 38c-1 2 0 4 3 4h20c3 0 4-2 3-4L27 18V6"/><path d="M15 30h18"/>'}[kind]
    return f'<div style="width: 96px; height: 96px; border-radius: 50%; border: 1px solid #E6E1DA; display: flex; align-items: center; justify-content: center; margin: 0 auto"><svg width="48" height="48" viewBox="0 0 48 48" aria-hidden="true" fill="none" stroke="{INK}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round">{paths}</svg></div>'

def values_panel(title, vals, top=56):
    items = "".join(f'''<div style="text-align: center">{icon(ic)}<h3 style="margin: 28px auto 0; {LABEL}; font-size: 17px; line-height: 1.4; max-width: 240px">{t}</h3><div style="width: 40px; height: 1.5px; background: #61757D; margin: 18px auto"></div><p style="margin: 0 auto; font-size: 15px; line-height: 1.6; max-width: 300px">{d}</p></div>''' for ic, t, d in vals)
    return f'''<section style="background: {TAUPE}; padding: {top}px 0 56px"><div style="{WRAP}"><div style="background: {CARD}; border-radius: 8px; padding: clamp(48px, 7vw, 80px) clamp(20px, 4vw, 40px)">{H("h2", 44, title, "text-align: center; margin-bottom: 48px")}<div style="{grid(280)}; gap: 72px 48px; max-width: 900px; margin: 0 auto">{items}</div></div></div></section>'''

def why_band(vals):
    eye = "font-size: 12px; letter-spacing: 0.24em; font-weight: 500"
    cells = "".join(f'''<div style="padding-top: 22px; border-top: 1px solid rgba(192,170,150,0.55)"><div style="{eye}; color: {TAN}; margin-bottom: 14px">0{i}</div><h3 style="margin: 0; font-family: {SERIF}; font-weight: 400; font-size: 26px; line-height: 1.15; color: {BG}">{t}.</h3><p style="margin: 12px 0 0; font-size: 16px; line-height: 1.6; color: #ADB7BD">{d}</p></div>''' for i, (_, t, d) in enumerate(vals, 1))
    strip = "".join(f'<div class="zoom" style="height: 300px; border-radius: 8px; overflow: hidden"><img src="{u("assets/img/" + k)}" alt="" loading="lazy" style="width: 100%; height: 100%; object-fit: cover; object-position: {pos}; display: block"></div>' for k, pos in [("h_about.jpg", "50% 30%"), ("sema.jpg", "50% 45%"), ("h_how.jpg", "50% 30%")])
    return f'''<section style="background: {NAVY}; padding: 104px 0 96px"><div style="{WRAP}">
<div style="display: flex; flex-wrap: wrap; gap: 56px 72px">
<div style="flex: 1 1 300px; max-width: 380px"><div style="{eye}; color: {TAN}; margin-bottom: 18px">WHY 46 HEALTH</div>{H("h2", 52, "Longevity,<br>made personal.", "color: " + BG + "; line-height: 1.08")}
<p style="margin: 24px 0 32px; font-size: 17px; line-height: 1.65; color: #ADB7BD">A licensed provider, a trusted pharmacy and a plan built around your health and wellness, from first consult to every refill.</p>{btn("See How It Works", u("how-it-works.html"), "light")}</div>
<div style="flex: 2 1 520px; {grid(260)}; gap: 48px">{cells}</div></div>
<div style="{grid(260)}; gap: 20px; margin-top: 80px">{strip}</div></div></section>'''

def cat_card(c, cta="Learn More", tall=False):
    href, _, t, d, img = c
    return f'''<article class="hover-card" style="background: {CARD}; border-radius: 8px; padding: 16px; display: flex; flex-direction: column; box-shadow: 0 1px 2px rgba(20,29,33,0.06)">
<div class="zoom" style="border-radius: 6px; overflow: hidden"><img src="{u('assets/img/' + img)}" alt="" style="width: 100%; height: {300 if tall else 220}px; object-fit: cover; display: block"></div>
<div style="padding: 24px 10px 8px; display: flex; flex-direction: column; gap: 10px; flex: 1"><h3 style="margin: 0; {LABEL}; font-size: 17px; line-height: 1.35">{t}</h3><p style="margin: 0; font-size: 15px; line-height: 1.6">{d}</p><div style="margin-top: auto; padding-top: 8px">{link(cta + f'<span class="sr-only"> about {t}</span>', u(href))}</div></div></article>'''

def cat_grid(cta="Learn More"):
    order = [CATEGORY_PAGES[0], CATEGORY_PAGES[1], CATEGORY_PAGES[2], CATEGORY_PAGES[3], CATEGORY_PAGES[4]]
    top = "".join(cat_card(c, cta) for c in order[:3])
    bottom = "".join(cat_card(c, cta, True) for c in order[3:])
    return f'<div style="{grid(300)}; gap: 28px">{top}</div><div style="{grid(420)}; gap: 28px; margin-top: 28px">{bottom}</div>'

def check_list(items):
    return "".join(f'<li style="display: flex; gap: 14px; align-items: flex-start; font-size: 16px; line-height: 1.5"><span aria-hidden="true" style="flex: 0 0 28px; height: 28px; border-radius: 50%; background: {TAN}; display: flex; align-items: center; justify-content: center">{CHECK}</span><span>{t}</span></li>' for t in items)

# ---------------------------------------------------------------- products
def ppath(p): return f"products/{p['slug']}.html"
def price_text(p): return p["price"] or "Price coming soon"

NEW = f'<span style="position: absolute; top: 14px; left: 14px; font-size: 11px; letter-spacing: 0.14em; font-weight: 500; padding: 4px 9px; border-radius: 999px; background: {WHITE}; color: {INK}">NEW</span>'

ADD_SVG = '<svg class="ic-add" width="18" height="18" viewBox="0 0 18 18" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M9 3v12M3 9h12"/></svg>'
ADDED_SVG = '<svg class="ic-added" width="18" height="18" viewBox="0 0 18 18" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3.5 9.5l3.5 3.5 7.5-8"/></svg>'

def list_toggle(p):
    t = E(p["title"])
    return f'<button type="button" class="list-toggle" data-list-add="{p["slug"]}" data-list-name="{t}" aria-pressed="false" aria-label="Add {t} to My Consult List" title="Add to My Consult List">{ADD_SVG}{ADDED_SVG}</button>'

def product_card(p):
    unit = p["unit"]
    href = u(ppath(p))
    name = E(p["name"])
    if p["photo"]:
        media = f'<div class="zoom" style="overflow: hidden"><img src="{u("assets/img/" + p["image"])}" alt="" loading="lazy" style="display: block; width: 100%; aspect-ratio: 921 / 722; object-fit: cover"></div>'
        title = f'<h3 style="margin: 0; font-size: 14px; letter-spacing: 0.06em; font-weight: 600; text-transform: uppercase">{name}</h3><div style="font-size: 13px; color: {MUTED}">{E(p["detail"])}</div>'
        u_html = f'<span style="font-size: 13px; color: {MUTED}; font-weight: 400"> / {unit}</span>' if unit else ""
        unit_line = ""
    else:
        blend = "; mix-blend-mode: multiply" if p["image"] == "gel.png" else ""
        media = f'<div class="zoom" style="height: 150px; display: flex; align-items: center; justify-content: center; padding-top: 16px"><img src="{u("assets/img/" + p["image"])}" alt="" loading="lazy" style="max-height: 100px; max-width: 60%; object-fit: contain{blend}"></div>'
        title = f'<h3 style="margin: 0; font-size: 13.5px; letter-spacing: 0.03em; font-weight: 500; line-height: 1.4; text-transform: uppercase">{name}</h3>'
        u_html = ""
        unit_line = f'<div style="font-size: 12px; color: {MUTED}">{E(unit)}</div>' if unit else ""
    badge = NEW if p["new"] else ""
    toggle = list_toggle(p)
    return f'''<article class="hover-card" style="position: relative; background: {TAUPE}; border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; text-align: center">
<a href="{href}" class="card-link" style="display: flex; flex-direction: column; flex: 1">{media}{badge}
<div style="padding: 18px 18px 0; display: flex; flex-direction: column; align-items: center; gap: 6px; flex: 1">{title}
<div style="font-size: 20px; font-weight: 500; font-variant-numeric: tabular-nums; margin-top: auto; padding-top: 10px">{'<span style="font-size: 12px; letter-spacing: 0.1em; font-weight: 400; color: ' + MUTED + '">FROM </span>' if p["id"] in ("sema", "tirz") else ""}{E(price_text(p))}{u_html}</div>{unit_line}</div></a>{toggle}
<div style="padding: 12px 18px 22px; display: flex; align-items: center; justify-content: center; gap: 18px; flex-wrap: wrap">{consult("Get Started", p["slug"], extra="min-height: 40px; padding: 0 20px; font-size: 13px")}{link('Learn More<span class="sr-only"> about ' + name + '</span>', href, "font-size: 13px")}</div>
</article>'''

def group_panel(gid, title, prods, sub=""):
    s = f'<p style="{P}; margin-top: 12px; max-width: 640px">{sub}</p>' if sub else ""
    return f'''<section id="{gid}" aria-labelledby="{gid}-h" style="background: {WHITE}; border-radius: 8px; padding: clamp(28px, 4vw, 48px); margin-bottom: 28px; scroll-margin-top: 80px">
<div style="display: flex; justify-content: space-between; align-items: end; gap: 24px; flex-wrap: wrap; margin-bottom: 36px"><div>{H("h2", 40, title).replace("<h2 ", f'<h2 id="{gid}-h" ', 1)}{s}</div><span style="font-size: 14px; color: {MUTED}">{len(prods)} option{"s" if len(prods) != 1 else ""}</span></div>
<div style="{grid_fill(250)}; gap: 20px">{"".join(product_card(p) for p in prods)}</div></section>'''

def chipnav(groups):
    chips = "".join(f'<a href="#{g[0]}" style="display: inline-flex; align-items: center; min-height: 40px; padding: 0 18px; border-radius: 999px; border: 1px solid #D3CCC4; background: {WHITE}; font-size: 14px; color: {INK}; text-decoration: none; white-space: nowrap">{g[1]}</a>' for g in groups)
    return f'<nav aria-label="On this page" style="position: sticky; top: 0; z-index: 2; background: {BG}; border-top: 1px solid #E6E1DA; border-bottom: 1px solid #E6E1DA; padding: 14px 0; margin-bottom: 40px"><div style="{WRAP}; display: flex; gap: 10px; overflow-x: auto">{chips}</div></nav>'

def in_group(gid): return [p for p in PRODUCTS if gid in p["groups"]]
def ids(*xs): return [BY_ID[x] for x in xs]

# Category pages: (file, title html, intro, [(group id, title, products, sub)], extra html after groups)
PAGES = {
 "peptides.html": ("Small molecules,<br>thoughtful care.", "Peptides are short chains of amino acids that act as signals in the body. Your provider reviews your labs and goals before recommending any protocol, and every vial is prepared by SureCare Specialty Pharmacy.", [
    ("recovery", "Recovery &amp; Repair", ids("bpc15", "bpc10", "bpctb30", "bpctb10", "bpctbkpv", "glow", "klow"), "Blends built around BPC-157 and TB-500, concentrated into a single 3 mL vial."),
    ("performance", "Performance &amp; Vitality", ids("serm", "sermipa", "cjc"), "Growth hormone–releasing peptides, dosed and monitored by your provider."),
    ("longevity", "Cellular Health &amp; Longevity", ids("nadinj", "nadnasal", "mots10", "mots40", "epi", "ghkepi"), "NAD+, mitochondrial and longevity peptides."),
    ("skin", "Skin", ids("ghk"), "Copper peptide for skin. See Skin &amp; Aesthetics for compounded skincare."),
    ("sexual", "Sexual Wellness", ids("pt141"), "For desire and arousal, prescribed after a private consult.")]),
 "weight-management.html": ("Lasting change,<br>medically guided.", "GLP-1 medications act on the hormones that regulate appetite and blood sugar. Paired with nutrition, movement and regular check-ins, your provider builds a program that fits your body and your life.", [
    ("glp1", "GLP-1 programs", ids("sema", "tirz"), "Compounded semaglutide and tirzepatide, dosed weekly and adjusted by your provider. Your monthly price follows your dose, with no teaser pricing."),
    ("support", "Supporting peptides", ids("mots10", "mots40", "cjc", "sermipa"), "Peptides your provider may add alongside a weight program.")]),
 "mens-health.html": ("Built around how<br>you want to feel.", "Your provider reviews your health history, labs and goals, then recommends options that fit — from testosterone and hair to prescription options for desire and intimacy. No treatment is prescribed without a consult.", [
    ("testosterone", "Testosterone &amp; Hormones", in_group("m_test"), "Testosterone replacement in gels, creams, tablets and injection, plus the support medications often prescribed alongside it."),
    ("oral", "Sexual Wellness: Oral &amp; Sublingual", in_group("m_oral") + ids("pt141"), "Fast-dissolving tablets and troches, prescribed after a private consult."),
    ("injections", "Sexual Wellness: Injections", in_group("m_inj"), "Trimix and Bimix, titrated by your provider."),
    ("urethral", "Sexual Wellness: Urethral Gels", in_group("m_ureth"), "Needle-free alternatives to injections."),
    ("peyronies", "Peyronie’s", in_group("m_peyr"), "Topical treatment prescribed after a provider review."),
    ("hair", "Hair Growth", in_group("hair"), "Topical and oral options for male-pattern hair loss."),
    ("energy", "Energy &amp; Vitality", ids("serm", "sermipa", "cjc", "nadinj"), "Peptides for energy, drive and healthy aging.")]),
 "womens-health.html": ("Care that keeps<br>up with you.", "Your provider takes the time to understand your health, your history and what you want to change, then recommends options that fit this stage of your life — including prescription options for desire and intimacy.", [
    ("progesterone", "Progesterone &amp; DHEA", in_group("w_prog"), "Bioidentical progesterone and DHEA in gels, creams, capsules and rapid-dissolve tablets."),
    ("estrogen", "Bi-Est &amp; Testosterone", in_group("w_biest"), "Bioidentical estriol/estradiol and low-dose testosterone, in creams, troches and tablets."),
    ("libido", "Libido &amp; Arousal", in_group("w_libido") + ids("pt141"), "Prescription options for desire and intimacy, starting with a private consult."),
    ("dryness", "Vaginal Dryness &amp; Vulvodynia", in_group("w_vag"), "Local hormone and non-hormone options for dryness, tissue comfort and vulvar pain.")]),
 "skin-aesthetics.html": ("Skin &amp; aesthetics", "Pharmacy-made skin care, formulated for your skin and your goals.", [
    ("skincare", "Compounded Skincare", in_group("cosmetic"), "Pharmacy-made serums, creams and gels for tone, texture, hydration and scars."),
    ("peptides", "Skin Peptides", ids("ghk", "glow", "ghkepi"), "Copper-peptide options your provider may recommend alongside topicals."),
    ("hair", "Hair Growth", in_group("hair"), "Topical and oral options for thinning hair.")]),
}
NAV_TITLE = {c[0]: c[1] for c in CATEGORY_PAGES}

# home category for each product (breadcrumbs, related products)
HOME = {}
for f in ["peptides.html", "weight-management.html", "mens-health.html", "womens-health.html", "skin-aesthetics.html"]:
    for gid, gt, prods, _ in PAGES[f][2]:
        for p in prods:
            HOME.setdefault(p["id"], (f, gid, gt, prods))
missing = [p["id"] for p in PRODUCTS if p["id"] not in HOME]
assert not missing, missing

def peptide_extra():
    stats = "".join(f'<div style="background: {CARD}; border-radius: 8px; padding: 24px 16px; text-align: center"><div style="font-family: {SERIF}; font-size: 36px">{a}</div><div style="font-size: 12px; letter-spacing: 0.1em; margin-top: 8px; color: {MUTED}">{b}</div></div>' for a, b in [("3 mL", "PEPTIDE VIALS"), ("$69", "STARTING PRICE"), ("5", "MEDS PER SHIPMENT")])
    return f'''<section style="background: {TAUPE}; padding: 72px 0"><div style="{WRAP}; display: flex; gap: 64px; flex-wrap: wrap; align-items: center">
<div style="flex: 1 1 380px">{H("h2", 44, "Same total milligrams.<br>A smaller vial.")}<p style="margin: 18px 0 0; font-size: 17px; line-height: 1.6; max-width: 520px">Our peptides are concentrated into 3 mL vials that hold the same total mg as a standard 5 mL telehealth vial. NAD+ comes in a 10 mL vial. Every vial has one fixed price, and up to five medications ship for a single shipping fee.</p></div>
<div style="flex: 1 1 340px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px">{stats}</div></div></section>
<section style="padding: 40px 0"><div style="{NARROW}"><p role="note" style="margin: 0; font-size: 14px; line-height: 1.6; color: {MUTED}; text-align: center">Competing in a tested sport? Many peptides, including BPC-157, TB-500 and growth hormone secretagogues, are on the World Anti-Doping Agency prohibited list. Talk with your provider before starting.</p></div></section>'''

def weight_extra():
    return f'<section style="background: {TAUPE}; padding: 72px 0"><div style="{WRAP}; display: flex; gap: 64px; flex-wrap: wrap; align-items: center"><div style="flex: 1 1 340px">{H("h2", 44, "What’s included")}<p style="margin: 18px 0 0; font-size: 17px; line-height: 1.6">Every program is provider-guided from the first consult.</p></div><ul style="flex: 1 1 420px; list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 18px">{check_list(["A licensed provider reviews your history and sets your dose", "Ongoing check-ins and dose adjustments as you progress", "Medication prepared by SureCare Specialty Pharmacy", "Discreet shipping to your door", "[Supplies included — confirm]"])}</ul></div></section>'

def category_page(fname):
    title, intro, groups = PAGES[fname]
    extra = {"peptides.html": peptide_extra, "weight-management.html": weight_extra}.get(fname, lambda: "")()
    body = (centered_intro(title, intro, [("Treatments", "treatments.html"), (NAV_TITLE[fname].replace("&", "&amp;"), None)]) + chipnav(groups)
            + f'<div style="{WRAP}; padding-bottom: 72px">' + "".join(group_panel(*g) for g in groups) + '</div>' + extra + cta_band())
    return body

DISCLAIMER_RX = "This is a compounded prescription drug. Compounded drugs are not FDA-approved and have not been evaluated by the FDA for safety, effectiveness or quality. Descriptions are for education and are not claims of therapeutic efficacy. A licensed prescriber determines whether a product is appropriate for you."
DISCLAIMER_PEPTIDE = "This peptide is not FDA-approved. Much of the research on it comes from laboratory and animal studies, and its long-term effects in humans are not well established. Your provider will discuss potential benefits and risks with you."
DISCLAIMER_GLP1 = "Compounded semaglutide and tirzepatide are not FDA-approved and are not generic versions of any brand-name medication. They are prescribed only when a provider determines they meet a patient’s individual clinical needs. Do not use if you or a family member have had medullary thyroid carcinoma or Multiple Endocrine Neoplasia syndrome type 2. Tell your provider if you have a history of pancreatitis, gallbladder disease, kidney problems or diabetic retinopathy, or are pregnant or planning pregnancy."
DISCLAIMER_COS = "Cosmetic items are not drugs and make no therapeutic claims. Prepared by SureCare Specialty Pharmacy."

TAKEN = {"Injectable": "Self-injected, per your plan", "Injection": "Self-injected, per your plan", "Topical cream": "Applied to the skin", "Topical gel": "Applied to the skin",
         "Topical": "Applied to the skin", "Topical serum": "Applied to the skin", "Topical solution": "Applied to the scalp", "Shampoo": "Used as a shampoo",
         "Rapid-dissolve tablet": "Dissolved in the mouth", "Sublingual troche": "Dissolved under the tongue", "Sublingual tablet": "Dissolved under the tongue",
         "Capsule": "Taken by mouth", "Tablet": "Taken by mouth", "Vaginal gel": "Applied vaginally", "Vaginal cream": "Applied vaginally", "Vaginal": "Applied vaginally",
         "Vaginal suppository": "Inserted vaginally", "Urethral gel": "Applied as directed", "Nasal spray": "Nasal spray"}
CROSS = {"weight-management.html": ["nadinj", "testosterone-5pct-chrysin", "progesterone-100-mg-slow", "ascorbic-acid-10pct"],
         "peptides.html": ["sema", "testosterone-5pct-chrysin", "ascorbic-acid-10pct", "progesterone-100-mg-slow"],
         "mens-health.html": ["sema", "nadinj", "bpc15", "minoxidil-5pct-melatonin"],
         "womens-health.html": ["sema", "nadinj", "ascorbic-acid-10pct", "pt141"],
         "skin-aesthetics.html": ["glow", "ghk", "nadinj", "sema"]}

def quick_facts(p):
    if p["id"] in ("sema", "tirz"):
        size, supply = "Weekly dose set by your provider", "Monthly, with refills"
    elif p["kind"] == "peptide":
        size, supply = p["detail"].split(" · ")[0] + " per vial", "Per vial"
    else:
        size, supply = None, (p["unit"].split(" · ")[0] if p["unit"] else "As prescribed")
    second = ("Strength", size) if size else ("Form", p["form"])
    facts = [("Taken", TAKEN.get(p["form"], p["form"])), second, ("Supply", supply), ("Pharmacy", "SureCare · El Paso, TX")]
    return '<dl class="pp-facts">' + "".join(f'<div><dt>{a}</dt><dd>{E(b)}</dd></div>' for a, b in facts) + '</dl>'

def product_page(p):
    f, gid, gt, siblings = HOME[p["id"]]
    cat = NAV_TITLE[f].replace("&", "&amp;")
    img_src = u("assets/img/" + p["image"])
    alt = E(p["title"]) + (" vial" if p.get("kind") == "peptide" and "nasal" not in p["name"].lower() and "vial" not in p["name"].lower() else "")
    if p["photo"]:
        media = f'<div style="border-radius: 16px; overflow: hidden; background: {TAUPE}"><img src="{img_src}" alt="{alt}" style="display: block; width: 100%; aspect-ratio: 921 / 722; object-fit: cover"></div>'
    else:
        media = f'<div style="background: {WHITE}; border-radius: 16px; aspect-ratio: 4 / 3; display: flex; align-items: center; justify-content: center"><img src="{img_src}" alt="" style="width: 40%; max-height: 55%; object-fit: contain"></div>'
    unit = ""
    if p["unit"]:
        unit = f' <span style="font-size: 15px; color: {MUTED}">/ {E(p["unit"])}</span>'
    desc = E(p["desc"]) if p["desc"] else "[Product description — pending medical and compliance review.]"
    summary_html = ""
    if p.get("summary"):
        summary_html = f'<p style="margin: 14px 0 0; font-family: {SERIF}; font-size: 22px; line-height: 1.35">{E(p["summary"])}</p>'
    if p["kind"] == "peptide":
        monthly = p["size"] == "Monthly"
        spec = [("Dosing" if monthly else "Total per vial", "Weekly, set by your provider" if monthly else p["size"]),
                ("Contents", p["contents"]), ("Concentration × fill", p["concentration"]), ("Form", p["form"]),
                ("Prepared by", "SureCare Specialty Pharmacy, El Paso, TX"), ("Prescription", "Required — online consultation")]
    else:
        spec = [("Form", p["form"]), ("Supply", p["unit"] or "As listed"), ("Prepared by", "SureCare Specialty Pharmacy, El Paso, TX"),
                ("Prescription", "Required — online consultation")]
    row_style = "display: flex; justify-content: space-between; gap: 20px; padding: 12px 0; font-size: 14px; border-top: 1px solid #ECE8E2"
    rows = "".join(f'<div style="{row_style}"><dt style="color: {MUTED}">{a}</dt><dd style="margin: 0; text-align: right; font-weight: 500">{E(b)}</dd></div>' for a, b in spec)
    details = f'<div style="background: {WHITE}; border-radius: 16px; padding: 20px 24px 10px; margin-top: 16px"><h2 style="margin: 0 0 8px; font-size: 12px; letter-spacing: 0.2em; font-weight: 600; text-transform: uppercase; color: {MUTED}">Details</h2><dl style="margin: 0">{rows}</dl></div>'
    other = [q for q in PRODUCTS if q["kind"] == "peptide" and q["name"] == p["name"] and q["id"] != p["id"]]
    other_html = ""
    if other:
        links_html = ", ".join(f'<a href="{u(ppath(q))}">{E(q["size"])} ({E(q["price"])})</a>' for q in other)
        other_html = f'<p style="margin: 14px 0 0; font-size: 15px">Also available: {links_html}</p>'
    shipping = "Ships discreetly to your door. Up to five medications ship together for one shipping fee."
    know = p.get("know")
    safety = ("What to know", E(know)) if know else ("Important safety information", "[Safety information, side effects and contraindications — supplied by medical team and reviewed by counsel.]")
    acc = [safety, ("How it’s used", "Your provider sets your dose and schedule and explains how to use it. [Use instructions — supplied by medical team.]"),
           ("Shipping &amp; refills", shipping + " Refills are managed through your patient portal. [Shipping time.]")]
    accs = "".join(f'<details style="border-top: 1px solid #E2DDD6"{" open" if i == 0 else ""}><summary style="list-style: none; cursor: pointer; display: flex; justify-content: space-between; align-items: center; min-height: 56px; font-size: 15px; font-weight: 600">{q}{CHEV}</summary><p style="{P}; font-size: 15px; padding-bottom: 18px">{a}</p></details>' for i, (q, a) in enumerate(acc))
    same = [q for q in siblings if q["id"] != p["id"]][:2]
    cross = [pid(x) for x in CROSS[f]]
    related, seen = [], {p["id"]}
    for q in same + cross:
        if q["id"] not in seen and len(related) < 4:
            related.append(q); seen.add(q["id"])
    rel = ""
    if related:
        cards = "".join(product_card(q) for q in related)
        rel = f'<section style="background: {TAUPE}; padding: 56px 0"><div style="{WRAP}"><div style="display: flex; justify-content: space-between; align-items: end; gap: 24px; flex-wrap: wrap; margin-bottom: 32px"><div><p style="{EYEBROW}; font-size: 12px; color: #61757D; margin-bottom: 10px">Across your care</p>{H("h2", 36, "Often discussed alongside")}</div><p style="margin: 0; font-size: 15px; color: {MUTED}; max-width: 360px">Add any of these to your list. One consultation covers them all.</p></div><div style="{grid_fill(250)}; gap: 20px">{cards}</div></div></section>'
    if p["id"] in ("sema", "tirz"):
        disc = DISCLAIMER_GLP1
    elif "pregnyl" in p["id"]:
        disc = "Pregnyl is a brand-name, FDA-approved medication dispensed by prescription. Descriptions are for education and are not claims of therapeutic efficacy. A licensed prescriber determines whether it is appropriate for you."
    elif p["kind"] == "peptide" and p["id"] not in ("nadinj", "nadnasal"):
        disc = DISCLAIMER_PEPTIDE
    elif p["kind"] == "cosmetic":
        disc = DISCLAIMER_COS
    else:
        disc = DISCLAIMER_RX
    newtag = ""
    if p["new"]:
        newtag = f'<span style="display: inline-block; margin-left: 12px; vertical-align: middle; font-family: Inter, sans-serif; font-size: 11px; letter-spacing: 0.14em; font-weight: 500; padding: 4px 9px; border-radius: 999px; background: {WHITE}; border: 1px solid #E2DDD6">NEW</span>'
    title_html = f'<span data-treatment-name="{p["slug"]}">{E(p["title"])}</span>{newtag}'
    cta = consult("Start Your Consultation", p["slug"], extra="width: 100%; min-height: 56px; margin-top: 28px; font-size: 16px")
    crumbs = f'<a href="{u("treatments.html")}" style="color: {MUTED}">Treatments</a> &nbsp;/&nbsp; <a href="{u(f)}" style="color: {MUTED}">{cat}</a> &nbsp;/&nbsp; <a href="{u(f)}#{gid}" style="color: {MUTED}">{gt}</a>'
    body = f"""<section style="padding: 32px 0 64px"><div style="{WRAP}">
<nav aria-label="Breadcrumb" style="font-size: 13px; color: {MUTED}; margin-bottom: 28px">{crumbs}</nav>
<div style="{grid(400)}; gap: clamp(32px, 5vw, 64px); align-items: start">
<div class="pp-media">{media}{details}</div>
<div style="max-width: 560px">
<p style="{EYEBROW}; font-size: 12px; color: {MUTED}; margin-bottom: 12px">{cat}</p>
{H("h1", 48, title_html)}
<div style="font-size: 28px; margin-top: 18px; font-variant-numeric: tabular-nums">{'<span style="font-size: 14px; letter-spacing: 0.12em; color: ' + MUTED + '">FROM </span>' if p["id"] in ("sema", "tirz") else ""}{E(price_text(p))}{unit}</div>
{summary_html}<p style="margin: 18px 0 0; font-size: 17px; line-height: 1.6">{desc}</p>{other_html}
{quick_facts(p)}
{cta}
<button type="button" class="list-btn" data-list-add="{p["slug"]}" data-list-name="{E(p["title"])}" aria-pressed="false"><span class="when-off">+ Add to My Consult List</span><span class="when-on">✓ On your consult list</span></button>
<p style="margin: 12px 0 0; font-size: 13px; color: {MUTED}; text-align: center">Prescribed only if appropriate after a provider review. <a href="{u('consult-list.html')}">View my list</a></p>
<div class="pp-note">{LIST_ICON}<span><b>Bring this and anything else to one consultation.</b> Up to 5 medications ship together for one fee.</span></div>
<div class="pp-incl"><h2>Included with your plan</h2><ul>{"".join(f"<li>{CHECK_DOT}<span>{t}</span></li>" for t in ["Provider consultation and ongoing check-ins", "Dose adjustments as you progress", "Prepared by SureCare Specialty Pharmacy", "Discreet shipping, up to 5 meds for one fee"])}</ul></div>
<div style="margin-top: 40px; border-bottom: 1px solid #E2DDD6">{accs}</div>
<p style="margin: 24px 0 0; font-size: 12px; line-height: 1.6; color: {MUTED}">{disc}</p>
</div></div></div></section>
{rel}{cta_band()}"""
    plain = re.sub("<[^>]+>", "", p["desc"] or p["detail"])[:150]
    return document(p["title"], f"{p['title']} — {price_text(p)}. {plain}", body, "Treatments")

# ---------------------------------------------------------------- core pages
CHECK_W = '<svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M2.5 7.5l3 3 6-6.5"/></svg>'

def chip(text, dark=False):
    bg = NAVY if dark else "#EFEBE4"
    fg = "#fff" if dark else INK
    return f'<span style="display: inline-flex; align-items: center; gap: 6px; font-size: 12px; padding: 5px 10px; border-radius: 999px; background: {bg}; color: {fg}">{text}</span>'

def vframe(inner):
    return f'<div aria-hidden="true" style="background: {WHITE}; border-radius: 14px; box-shadow: 0 10px 30px rgba(20,29,33,0.10); padding: 20px; width: 100%; max-width: 360px; text-align: left">{inner}</div>'

def v_list(n=3, label=""):
    items = [("bpc15.jpg", "BPC-157 15 mg", "$79"), ("nadinj.jpg", "NAD+ Injectable", "$99"), ("sema.jpg", "Semaglutide", "$139 / mo")][:n]
    rows = "".join(f'<div style="display: flex; align-items: center; gap: 12px; padding: 9px 0; border-top: 1px solid #EFEBE4"><img src="{u("assets/img/" + i)}" alt="" style="width: 44px; height: 34px; object-fit: cover; border-radius: 6px"><div style="flex: 1; font-size: 13px; font-weight: 600">{t}</div><div style="font-size: 13px">{pr}</div></div>' for i, t, pr in items)
    tag = chip(label) if label else chip(f"{n} treatments")
    return vframe(f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; gap: 8px"><div style="font-family: {SERIF}; font-size: 19px">My Consult List</div>{tag}</div>{rows}<div style="margin-top: 10px; padding: 9px 12px; border-radius: 8px; background: {BG}; font-size: 12px; color: {MUTED}">Questions for my provider: “Which strength is right for me?”</div>')

def v_intake():
    return vframe(f'''<div style="display: flex; justify-content: space-between; font-size: 12px; color: {MUTED}"><span>Step 2 of 5</span><span>About 10 min</span></div>
<div style="height: 6px; border-radius: 999px; background: #EFEBE4; margin: 10px 0 16px"><div style="width: 40%; height: 100%; border-radius: 999px; background: {NAVY}"></div></div>
<div style="font-family: {SERIF}; font-size: 19px; line-height: 1.25">Your health history</div>
<p style="margin: 10px 0 12px; font-size: 13px">Are you currently taking any prescription medications?</p>
<div style="display: flex; gap: 8px">{chip("Yes", True)}{chip("No")}</div>''')

def v_provider():
    items = "".join(f'<div style="display: flex; gap: 10px; align-items: flex-start; padding: 8px 0; border-top: 1px solid #EFEBE4; font-size: 13px"><span style="flex: 0 0 20px; height: 20px; border-radius: 50%; background: {TAN}; display: inline-flex; align-items: center; justify-content: center; color: {INK}">{CHECK_W}</span>{t}</div>' for t in ["Reviews your intake and consult list", "May request recent labs", "Talks through options with you"])
    return vframe(f'<div style="display: flex; gap: 12px; align-items: center; margin-bottom: 10px"><div style="width: 38px; height: 38px; border-radius: 50%; background: {TAUPE}; display: flex; align-items: center; justify-content: center; font-family: {SERIF}; font-size: 15px">46</div><div><div style="font-size: 14px; font-weight: 600">Your licensed provider</div><div style="font-size: 12px; color: {MUTED}">Decides with you what’s appropriate</div></div></div>{items}')

def v_delivery():
    steps = [("Prescription sent to SureCare", True), ("Prepared for you", True), ("Shipped in discreet packaging", True), ("First check-in", False)]
    rows = ""
    for t, done in steps:
        bg = NAVY if done else WHITE
        mark = CHECK_W if done else ""
        col = "" if done else f"color: {MUTED}"
        rows += f'<div style="display: flex; gap: 12px; align-items: center; padding: 7px 0"><span style="flex: 0 0 20px; height: 20px; border-radius: 50%; border: 1.5px solid {NAVY}; background: {bg}; color: #fff; display: inline-flex; align-items: center; justify-content: center">{mark}</span><span style="font-size: 13px; {col}">{t}</span></div>'
    return vframe(f'<div style="font-family: {SERIF}; font-size: 19px; margin-bottom: 6px">Your order is on its way</div>{rows}')

HOME_STEPS = [
 ("Build your consult list", "Browse treatments and tap + on anything you’d like to ask about. Your list stays private on your device.", v_list),
 ("Complete a 10-minute intake", "Answer questions about your health history, medications and goals. Reviewed only by your care team.", v_intake),
 ("Meet your licensed provider", "Your provider reviews your intake and your list, may request labs, and decides with you what’s appropriate.", v_provider),
 ("Delivered, then ongoing care", "If prescribed, SureCare Specialty Pharmacy ships your medication to your door. Check-ins and refills from there.", v_delivery),
]

def page_products(f):
    seen, out = set(), []
    for _, _, prods, _ in PAGES[f][2]:
        for p in prods:
            if p["id"] not in seen:
                seen.add(p["id"]); out.append(p)
    return out

def price_num(p):
    m = re.match(r"\$([\d,]+)", p["price"] or "")
    return int(m.group(1).replace(",", "")) if m else None

def from_price(f):
    prods = PAGES[f][2][0][2] if f == "weight-management.html" else page_products(f)
    nums = [n for n in (price_num(p) for p in prods if "10 count" not in p["name"]) if n]
    lo = min(nums)
    suffix = " / month" if f == "weight-management.html" else (" per vial" if f == "peptides.html" else "")
    return f"From ${lo}{suffix}"

def pid(prefix):
    for p in PRODUCTS:
        if p["id"] == prefix or p["id"].startswith(prefix):
            return p
    raise KeyError(prefix)

def num_text(p):
    n = price_num(p)
    return f"${n}" if n else price_text(p)

CHECK_DOT = f'<span aria-hidden="true" style="flex: 0 0 20px; height: 20px; border-radius: 50%; background: #61757D; color: #fff; display: inline-flex; align-items: center; justify-content: center">{CHECK_W}</span>'
LIST_ICON = '<svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><rect x="5" y="3.5" width="14" height="17" rx="2"/><path d="M9 3.5V2.5h6v1M8.5 9h7M8.5 13h7M8.5 17h4"/></svg>'

HOME_AREAS = [  # (category file, name, count label, example chips, image). Lifestyle photos kept as cat1-cat5.jpg (weight, skin, mens, womens, peptides) if we switch back.
 ("weight-management.html", "Weight care", "2 GLP-1 programs", ["Semaglutide", "Tirzepatide"], "hero_weight.jpg"),
 ("peptides.html", "Peptides &amp; longevity", None, ["BPC-157", "NAD+", "GLOW", "CJC / Ipamorelin"], "hero_peptides.jpg"),
 ("mens-health.html", "Men’s health &amp; sexual wellness", None, ["Testosterone", "Tadalafil", "Finasteride"], "hero_mens.jpg"),
 ("womens-health.html", "Women’s health &amp; sexual wellness", None, ["Progesterone", "Bi-Est", "DHEA"], "hero_womens.jpg"),
 ("skin-aesthetics.html", "Skin &amp; hair", None, ["Vitamin C serum", "Kojic acid gel", "Hair solutions"], "hero_skin.jpg"),
]

def area_slide(i, a):
    f, name, count, chips, img = a
    n = len(HOME_AREAS)
    count = count or f"{len(page_products(f))} treatments"
    lo = from_price(f).replace("From ", "").replace(" / month", "/mo").replace(" per vial", "")
    chip_html = "".join(f'<span class="hc-chip">{c}</span>' for c in chips)
    plain = re.sub("<[^>]+>", "", name).replace("&amp;", "&")
    lazy = "" if i == 0 else 'loading="lazy" '
    return (f'<article class="hc-slide" role="group" aria-roledescription="slide" aria-label="{i + 1} of {n}: {E(plain)}">'
            f'<a href="{u(f)}" class="hc-media zoom" tabindex="-1" aria-hidden="true"><img src="{u("assets/img/" + img)}" alt="" {lazy}><span class="hc-num">{i + 1} / {n}</span></a>'
            f'<div class="hc-body"><div class="hc-head"><h3>{name}</h3><span>{count}</span></div>'
            f'<div class="hc-chips">{chip_html}</div>'
            f'<div class="hc-foot"><div><span class="hc-from">FROM</span> <span class="hc-price">{lo}</span></div>'
            f'{btn("Explore " + ARROW + f"<span class=sr-only> {E(plain)}</span>", u(f), extra="min-height: 42px; padding: 0 18px; font-size: 14px")}</div></div></article>')

def home_carousel():
    slides = "".join(area_slide(i, a) for i, a in enumerate(HOME_AREAS))
    dots = "".join(f'<button type="button" class="hc-dot" aria-label="Show slide {i + 1}"' + (' aria-current="true"' if i == 0 else "") + '></button>' for i in range(len(HOME_AREAS)))
    def chev(d):
        return f'<svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="{d}"/></svg>'
    return (f'<div class="hc" aria-roledescription="carousel" aria-label="Areas of care"><div class="hc-back" aria-hidden="true"></div>'
            f'<div class="hc-card"><div class="hc-track" tabindex="0">{slides}</div>'
            f'<div class="hc-controls"><div class="hc-dots">{dots}</div><div class="hc-arrows">'
            f'<button type="button" class="hc-prev" aria-label="Previous slide">{chev("M11 4L6 9l5 5")}</button>'
            f'<button type="button" class="hc-next" aria-label="Next slide">{chev("M7 4l5 5-5 5")}</button></div></div></div></div>')

def example_list():
    items = [(pid("sema"), "Weight care", "Semaglutide"), (pid("testosterone-5pct-chrysin"), "Men’s health", "Testosterone / Chrysin cream"), (pid("ascorbic-acid-10pct"), "Skin", "Vitamin C 10% serum"), (pid("bpc15"), "Peptides", "BPC-157")]
    rows = "".join(f'<div class="ex-row"><img src="{u("assets/img/" + p["image"])}" alt="" loading="lazy"><div style="flex: 1; min-width: 0"><div class="ex-cat">{c}</div><div class="ex-name">{n}</div></div><div class="ex-price">{num_text(p)}{"/mo" if p["unit"] == "per month" else ""}</div></div>' for p, c, n in items)
    return (f'<figure class="ex-wrap" style="margin: 0"><div class="ex-back" aria-hidden="true"></div><div class="ex-card">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; gap: 12px"><div style="display: flex; align-items: center; gap: 10px; font-size: 18px; font-weight: 600">{LIST_ICON}My Consult List</div><span class="ex-tag">Example</span></div>'
            f'<div style="font-size: 14px; color: {MUTED}; margin: 6px 0 4px">Four areas of care. One consultation.</div>{rows}'
            f'<div class="ex-ship">{CHECK_DOT}<span><b style="font-weight: 600">Ships together</b> &middot; up to 5 medications for one shipping fee</span></div></div>'
            f'<figcaption class="sr-only">Example consult list with semaglutide, a testosterone cream, a vitamin C serum and BPC-157</figcaption></figure>')

GOALS = [
 ("popular", "Most popular", ["sema", "testosterone-5pct-chrysin", "ascorbic-acid-10pct", "progesterone-100-mg-slow", "bpc15"]),
 ("weight", "Weight care", ["sema", "tirz"]),
 ("hormones", "Hormones", ["testosterone-cypionate", "testosterone-5pct-chrysin", "testosterone-0-1pct-10pct", "progesterone-100-mg-slow", "bi-est-topical-cream"]),
 ("sexual", "Sexual wellness", ["tadalafil-22", "pt141", "sildenafil-25-mg-tadalafil", "sildenafil-1pct-arginine", "tadalafil-20-mg-oxytocin"]),
 ("recovery", "Recovery", ["bpc15", "bpctb30", "klow", "bpctbkpv", "cjc"]),
 ("longevity", "Longevity", ["nadinj", "nadnasal", "mots10", "epi", "serm"]),
 ("skin", "Skin &amp; hair", ["ascorbic-acid-10pct", "kojic", "glow", "ghk", "minoxidil-5pct-melatonin"]),
]

def shop_by_goal():
    tabs = "".join(f'<button type="button" role="tab" id="goal-tab-{g}" aria-controls="goal-{g}" aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}">{t}</button>' for i, (g, t, _) in enumerate(GOALS))
    panels = "".join(f'<div role="tabpanel" id="goal-{g}" aria-labelledby="goal-tab-{g}" class="goal-panel"' + ("" if i == 0 else " hidden") + f'><div style="{grid_fill(210)}; gap: 18px">{"".join(product_card(pid(x)) for x in xs)}</div></div>' for i, (g, _, xs) in enumerate(GOALS))
    return (f'<section style="background: {BG}; padding: clamp(64px, 8vw, 96px) 0"><div style="{WRAP}">'
            f'<div style="display: flex; justify-content: space-between; align-items: end; gap: 24px; flex-wrap: wrap; margin-bottom: 24px"><div><p style="{EYEBROW}; font-size: 12px; color: #61757D; margin-bottom: 12px">Find your program</p>{H("h2", 46, "Shop by goal")}</div>{link("View all treatments", u("treatments.html"))}</div>'
            f'<div class="goal-tabs" role="tablist" aria-label="Goals">{tabs}</div>{panels}</div></section>')

RAIL_STEPS = [("Your list", "Add anything", "Tap + on any treatment, from any category.", "Stays on your device"),
              ("10 minutes", "One intake", "Health history, medications and goals, once.", "One form for everything"),
              ("Within 4 hrs", "One provider", "A licensed provider reviews your whole list with you.", "Typical review time"),
              ("1 fee", "One shipment", "SureCare prepares everything prescribed.", "Up to 5 medications")]

def rail_section():
    steps = "".join(
        f'<li class="rail-step{" last" if i == len(RAIL_STEPS) - 1 else ""}"><span class="rail-node" aria-hidden="true"></span>'
        f'<div class="rail-n">0{i + 1}</div><div class="rail-big">{big}</div>'
        f'<h3>{t}</h3><p>{d}</p><span class="rail-pill">{CHECK_DOT}{pill}</span></li>'
        for i, (big, t, d, pill) in enumerate(RAIL_STEPS))
    return (f'<section class="rail-sec"><div style="{WRAP}">'
        f'<div class="rail-head"><div><p style="{EYEBROW}; font-size: 12px; color: #61757D; margin-bottom: 14px">How it works</p>'
        + H("h2", 52, "Bring everything to<br>one consultation.", "line-height: 1.08")
        + f'<p style="margin: 18px 0 0; font-size: 17px; line-height: 1.6; color: {MUTED}">One list, one intake, one provider and one shipment, whatever you’re treating.</p></div>'
        f'<div class="rail-cta">{consult()}</div></div>'
        f'<ol class="rail">{steps}</ol></div></section>')

def home():
    checks = ["Men’s and women’s care", f"{len(PRODUCTS)} pharmacy-made treatments", "One consult for everything", "Up to 5 meds ship for one fee", "Licensed U.S. providers", "No membership required"]
    checkgrid = "".join(f'<li style="display: flex; align-items: center; gap: 10px; font-size: 15px">{CHECK_DOT}<span>{c}</span></li>' for c in checks)
    hero_html = (f'<section class="home-hero"><div class="home-hero-in" style="{WRAP}">'
        f'<div class="home-hero-copy"><p style="{EYEBROW}; font-size: 12px; color: #61757D">Physician-guided telehealth</p>'
        + H("h1", 60, "One team to become the best version of you.", "line-height: 1.08")
        + f'<p style="margin: 16px 0 0; font-family: {SERIF}; font-size: 24px; color: #8A7663">Your health. Your life. Our science.</p>'
        + f'<p style="margin: 22px 0 0; max-width: 540px; font-size: 18px; line-height: 1.6; color: {MUTED}">Build a list of everything you want to ask about. A licensed provider reviews it with you in one consultation, and SureCare Specialty Pharmacy prepares what’s prescribed.</p>'
        f'<ul class="hero-checks">{checkgrid}</ul>'
        f'<div style="display: flex; gap: 12px; flex-wrap: wrap; align-items: center; margin-top: 34px">{consult()}{btn("Explore All Treatments", u("treatments.html"), "ghost")}</div>'
        f'<p style="margin: 14px 0 0; font-size: 14px; color: {MUTED}"><b style="color: #141D21; font-weight: 600">Start your consultation for just $35.</b> Intake takes about 10 minutes, and a provider typically reviews it within 4 hours.</p></div>'
        f'{home_carousel()}</div></section>')
    trust = "".join(f'<li style="flex: 1 1 200px; text-align: center; font-size: 13px; letter-spacing: 0.16em; line-height: 1.5; padding: 8px 16px">{t}</li>' for t in ["LICENSED U.S. PROVIDERS", "PREPARED BY SURECARE PHARMACY", "DISCREET SHIPPING", "NO MEMBERSHIP REQUIRED"])
    steps = [("Add anything", "Tap + on any treatment, from any category. Your list stays on your device."),
             ("One intake", "Health history, medications and goals, once. About 10 minutes."),
             ("One provider", "A licensed provider reviews your whole list and decides with you what’s appropriate."),
             ("One shipment", "SureCare prepares everything prescribed. Up to 5 medications ship for one fee.")]
    steps_html = "".join(f'<li style="display: flex; gap: 16px; padding: 16px 0; border-top: 1px solid #E3DED6"><span style="font-size: 12px; letter-spacing: 0.2em; font-weight: 600; color: #8A7663; padding-top: 4px">0{i}</span><div><h3 style="margin: 0; font-size: 18px; font-weight: 600">{t}</h3><p style="margin: 4px 0 0; font-size: 15px; line-height: 1.55; color: {MUTED}">{d}</p></div></li>' for i, (t, d) in enumerate(steps, 1))
    one = (f'<section style="background: {BG}; padding: clamp(64px, 8vw, 96px) 0"><div style="{WRAP}; display: flex; flex-wrap: wrap; gap: clamp(40px, 6vw, 80px); align-items: center">'
        f'<div style="flex: 1 1 440px"><p style="{EYEBROW}; font-size: 12px; color: #61757D; margin-bottom: 14px">How it works</p>' + H("h2", 48, "Bring everything to one consultation.")
        + f'<p style="margin: 20px 0 24px; font-size: 17px; line-height: 1.65; color: {MUTED}">Most telehealth brands treat one thing. Your weight, hormones, skin and recovery are connected, so your provider looks at them together.</p>'
        f'<ol style="list-style: none; margin: 0; padding: 0; border-bottom: 1px solid #E3DED6">{steps_html}</ol>'
        f'<div style="display: flex; gap: 18px; flex-wrap: wrap; align-items: center; margin-top: 28px">{consult()}{link("See how it works", u("how-it-works.html"))}</div></div>'
        f'<div style="flex: 1 1 380px; display: flex; justify-content: center">{example_list()}</div></div></section>')
    chromo = (f'<section class="chromo-panel" style="position: relative; background: #061A23 url({u("assets/img/chromo.jpg")}) 70% center / cover no-repeat; color: {BG}; overflow: hidden"><div style="{WRAP}; position: relative; z-index: 1"><div style="max-width: 620px; padding: 104px 0">'
        + H("h2", 64, "46 chromosomes.<br>Only one of you.", "color: " + BG + "; line-height: 1.06")
        + f'<div style="width: 64px; height: 1.5px; background: {TAN}; margin: 32px 0"></div><p style="margin: 0; font-size: 13px; letter-spacing: 0.26em; line-height: 1.8; color: {TAN}">MEN’S &nbsp;·&nbsp; WOMEN’S &nbsp;·&nbsp; WEIGHT &nbsp;·&nbsp; PEPTIDES &nbsp;·&nbsp; SKIN</p>'
        f'<p style="margin: 24px 0 0; max-width: 480px; font-size: 17px; line-height: 1.65; color: #ADB7BD">Care built for the whole person, not one condition. Men’s and women’s health, weight, recovery and skin, under one licensed provider.</p></div></div></section>')
    vals = [("rx", "Your journey starts with a physician, not a shopping cart", "Every prescription begins with a licensed medical provider who reviews your health history before anything is prescribed."),
            ("dial", "Optimization based on your medical needs", "Your dosing and protocols are set for your body and your goals, then adjusted as you progress."),
            ("shield", "Compounded by a pharmacy you can trust", "Your medication is prepared to order by SureCare Specialty Pharmacy, a licensed 503A compounding pharmacy in El Paso, Texas."),
            ("chat", "Ongoing support and care throughout your journey", "Follow-ups, dosage changes and refills are all handled in your patient portal, with your provider a message away.")]
    prices = "".join(f'<div style="flex: 1 1 200px; border-top: 1px solid #3A464C; padding-top: 18px"><div style="font-family: {SERIF}; font-size: 40px; color: #FFFFFF">{re.sub(r"(\d+)", r'<span data-to="\1">\1</span>', a)}</div><div style="margin-top: 8px; font-size: 14px; letter-spacing: 0.06em; color: #ADB7BD">{b}</div></div>' for a, b in [("$69", "PEPTIDES FROM, PER VIAL"), ("$139", "GLP-1 PROGRAMS FROM, PER MONTH"), ("Up to 5", "MEDICATIONS SHIP FOR ONE FEE"), ("$35", "CONSULTATION")])
    pricing_band = (f'<section style="background: {NAVY}; color: #FFFFFF; padding: 0 0 80px"><div style="{WRAP}"><div style="border-top: 1px solid rgba(192,170,150,0.3); padding-top: 80px"><div style="text-align: center; max-width: 640px; margin: 0 auto">'
        + H("h2", 56, "Clear pricing.<br>No surprises.", "color: #F2F0EA; line-height: 1.08")
        + f'<p style="margin: 24px 0 0; font-size: 17px; line-height: 1.6; color: #F2F0EA">Your consultation is just $35, and your medication price is shown before you commit. No teaser prices that jump later.</p></div>'
        f'<div style="display: flex; flex-wrap: wrap; gap: 32px; margin-top: 64px">{prices}</div><div style="text-align: center; margin-top: 56px">{btn("See Pricing", u("pricing.html"), "light")}</div></div></div></section>')
    qs = [FAQ[0][1][0], FAQ[0][1][1], FAQ[1][1][0], FAQ[0][1][3], FAQ[3][1][0]]
    faq_items = "".join(f'<details class="home-faq"><summary>{q}{CHEV}</summary><p>{a}</p></details>' for q, a in qs)
    faq_html = (f'<section style="background: {WHITE}; padding: clamp(64px, 8vw, 96px) 0"><div style="{WRAP}; display: flex; flex-wrap: wrap; gap: clamp(32px, 6vw, 72px)">'
        f'<div style="flex: 1 1 300px"><p style="{EYEBROW}; font-size: 12px; color: #61757D; margin-bottom: 12px">FAQ</p>' + H("h2", 46, "Questions, answered")
        + f'<div style="margin-top: 20px">{link("See all FAQs", u("faq.html"))}</div></div>'
        f'<div style="flex: 2 1 520px; border-bottom: 1px solid #E3DED6">{faq_items}</div></div></section>')
    floatbar = (f'<div class="float-bar" hidden><a href="{u("consult-list.html")}" class="float-count">{LIST_ICON}<span><b class="float-num">0</b> on your consult list</span></a>'
        + consult("Start Your Consultation", extra="min-height: 44px; padding: 0 22px; font-size: 14px") + '</div>')
    body = (hero_html
      + f'<section aria-label="Why patients choose us" style="background: #61757D; color: #FFFFFF; padding: 22px 0"><ul style="{WRAP}; list-style: none; margin-top: 0; margin-bottom: 0; display: flex; flex-wrap: wrap; gap: 8px; justify-content: space-between">{trust}</ul></section>'
      + rail_section() + chromo + shop_by_goal() + why_band(vals) + pricing_band + faq_html + cta_band() + floatbar)
    return document("46 Health", "Physician-guided telehealth for men and women: weight care, peptides, hormones, sexual wellness and skin from licensed providers, prepared by SureCare Specialty Pharmacy.", body,
                    scripts=f'\n<script src="{u("assets/home.js") + "?v=" + ASSET_V}"></script><script src="{u("assets/motion.js") + "?v=" + ASSET_V}"></script>')

def treatments():
    body = (hero("h_treat.jpg", "#D9D3D0", "Therapies built around your goals.",
        "Every 46 Health treatment is prescribed by a licensed provider after a review of your health, and prepared by SureCare Specialty Pharmacy, a licensed compounding pharmacy in El Paso, Texas. Compounded medications are not FDA-approved; your provider will explain what that means for you.")
      + f'<section style="background: {TAUPE}; padding: 72px 0"><div style="{WRAP}">{H("h2", 44, "Treatments", "margin-bottom: 40px")}{cat_grid("View Products")}</div></section>'
      + f'<section style="padding: 72px 0"><div style="{WRAP}; display: flex; justify-content: space-between; align-items: center; gap: 40px; flex-wrap: wrap"><div style="max-width: 620px">{H("h2", 44, "Not sure where to start?")}<p style="margin: 18px 0 0; font-size: 17px; line-height: 1.6">Tell us your goals in the intake. Your provider will recommend what makes sense — and tell you when something doesn’t.</p></div>{consult()}</div></section>')
    return document("Treatments", "Weight management, peptides, men’s and women’s health, and skin care — prescribed by licensed providers.", body, "Treatments")

def how():
    steps = [("Choose your goal", "Browse treatments or start with what you want to improve: weight, recovery, energy, skin or intimacy. Not sure? Your provider can help you decide."),
             ("Complete your health intake", "Answer questions about your health history, medications and goals. It takes about 10 minutes and is reviewed only by your care team."),
             ("Consult with a licensed provider", "Your provider reviews your intake, may request recent labs or order new ones, and talks with you about options, risks and expectations. Prescribing is always at your provider’s discretion."),
             ("Get your personalized prescription", "If treatment is right for you, your provider sends a prescription for your specific dose to SureCare Specialty Pharmacy."),
             ("Delivered to your door", "Your medication ships in discreet, temperature-appropriate packaging with clear instructions. [Typical delivery time.]"),
             ("Ongoing care", "Scheduled check-ins let your provider track progress, adjust your plan and handle refills through your patient portal.")]
    need = check_list(["A government-issued ID", "Your current medications and supplements", f"Recent lab results, if you have them<br><span style='color:{MUTED}'>(not required to start)</span>", f"A U.S. shipping address<br><span style='color:{MUTED}'>(all 50 states)</span>"])
    body = (hero("h_how.jpg", "#C9CDCD", "How 46 Health works.",
        "You complete a brief medical intake covering your health history and treatment goals. A licensed 46 Health provider reviews your intake and, if treatment is clinically appropriate, issues your prescription. Your medication is compounded to order by SureCare Specialty Pharmacy, a licensed 503A compounding pharmacy in El Paso, Texas, and shipped directly to you. Ongoing care — follow-up evaluations, dose adjustments and refills — is managed by your 46 Health provider through your patient portal.")
      + f'''<section style="padding: 80px 0"><div style="{WRAP}">{H("h2", 44, "Here’s exactly what happens", "text-align: center; margin-bottom: 56px")}{bignum_steps(steps)}
<div style="background: {TAUPE}; border-radius: 8px; padding: 56px clamp(20px, 4vw, 40px); margin-top: 88px"><h2 style="margin: 0 0 40px; {LABEL}; font-size: 18px; text-align: center">What you’ll need</h2><ul style="list-style: none; margin: 0 auto; padding: 0; {grid(280)}; gap: 28px 56px; max-width: 760px">{need}</ul></div>
<p style="text-align: center; margin: 32px auto 0; max-width: 680px; font-size: 15px; line-height: 1.6">Not everyone is a candidate for every treatment. If your provider decides a therapy isn’t right for you, they’ll explain why and what else to consider.</p>
<div style="text-align: center; margin-top: 40px">{consult()}</div></div></section>''')
    return document("How it works", "From a 10-minute online intake to a licensed provider review and pharmacy delivery — here’s exactly what happens.", body, "How it works")

SURECARE_FACTS = [("2013", "Serving patients since"), ("5", "Licensed pharmacists"),
                  ("Sterile &amp; non-sterile", "Compounding capabilities"), ("Clean room", "For sterile preparations")]

def surecare_section():
    facts = "".join(f'<div style="background: {WHITE}; border-radius: 12px; padding: 20px 22px"><dt style="font-family: {SERIF}; font-size: 26px; line-height: 1.15">{a}</dt><dd style="margin: 8px 0 0; font-size: 14px; color: {MUTED}">{b}</dd></div>' for a, b in SURECARE_FACTS)
    return (f'<section style="background: {TAUPE}; padding: clamp(64px, 8vw, 88px) 0"><div style="{WRAP}"><div style="display: flex; flex-wrap: wrap; gap: 40px 72px; align-items: flex-start">'
            f'<div style="flex: 1 1 420px; max-width: 620px"><p style="{EYEBROW}">Our pharmacy partner</p>' + H("h2", 44, "SureCare Specialty Pharmacy")
            + '<p style="margin: 18px 0 0; font-size: 17px; line-height: 1.65">A locally owned, independent pharmacy in El Paso, Texas, compounding patient-specific prescriptions since 2013. SureCare prepares both sterile and non-sterile medications, with sterile formulations made in its on-site clean room.</p>'
            '<p style="margin: 14px 0 0; font-size: 17px; line-height: 1.65">Every 46 Health prescription is prepared to order for the individual patient, checked by a licensed pharmacist and shipped directly to you.</p></div>'
            f'<dl style="flex: 1 1 340px; margin: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 14px">{facts}</dl></div></div></section>')

IMG = lambda k: u("assets/img/" + k)
EYE = "font-size: 12px; letter-spacing: 0.24em; font-weight: 500; text-transform: uppercase; margin: 0 0 18px"
LEDE = "46 Health is a health and longevity company built for the whole person. One team of licensed providers looks at all of you, from weight and hormones to recovery, skin and long-term health, and builds a plan around your body and your goals."
VALS = [("One team, the whole you", "Men’s and women’s health, weight, recovery, skin and longevity under one team of providers, so nothing is treated in isolation.", "cat1.jpg", "50% 40%"),
        ("Physicians first", "Every prescription begins with a licensed provider who reviews your health history before anything is prescribed.", "h_about.jpg", "50% 25%"),
        ("Honest about evidence", "Some therapies have decades of clinical use; others are newer. We tell you which is which, so you can decide with clear eyes.", "h_treat.jpg", "50% 30%"),
        ("Care that continues", "Follow-ups, dosage changes and refills are all handled in your patient portal, with your provider a message away.", "cat4.jpg", "70% 40%")]
AREAS = ["Weight", "Hormones", "Recovery", "Skin", "Longevity", "Men’s health", "Women’s health", "Peptides"]
STATS = [("46", "", "chromosomes. One of you."), ("50", "", "states served"), ("$", "35", "consultation"), ("10", " min", "online intake")]

def stat_strip(dark=False):
    c, m, line = (BG, "#ADB7BD", "rgba(192,170,150,.35)") if dark else (INK, MUTED, "#D3CCC4")
    cells = ""
    for i, (a, b, l) in enumerate(STATS):
        num = f'<span data-to="{a}">{a}</span>' if a.isdigit() else a
        if b and not a.isdigit():
            num = f'{a}<span data-to="{b}">{b}</span>'
        cells += f'<div class="rv d{i}" style="padding: 28px 0 0; border-top: 1px solid {line}"><div style="font-family: {SERIF}; font-size: clamp(44px, 5vw, 64px); line-height: 1; color: {c}">{num}<span style="font-size: .45em">{b if a.isdigit() else ""}</span></div><div style="margin-top: 12px; font-size: 14px; letter-spacing: .06em; color: {m}">{l}</div></div>'
    return f'<div style="{grid(150)}; gap: 32px 24px">{cells}</div>'


def closing(img=None):
    if img:
        return (f'<section style="position: relative; overflow: hidden; color: {BG}; text-align: center"><img class="kb" src="{IMG(img)}" alt="" style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: 50% 35%">'
                f'<div style="position: absolute; inset: 0; background: linear-gradient(180deg, rgba(20,29,33,.35), rgba(20,29,33,.75))"></div>'
                f'<div class="rv" style="position: relative; {NARROW}; padding-top: clamp(96px, 12vw, 160px); padding-bottom: clamp(96px, 12vw, 160px)">' + H("h2", 56, "One team to become<br>the best version of you.", f"color: {BG}; line-height: 1.08")
                + f'<p style="margin: 22px auto 0; font-size: 17px; color: #DDE2E4">Start your consultation today for just $35.</p><div style="margin-top: 32px">{consult(kind="light")}</div></div></section>')
    return (f'<section style="padding: clamp(80px, 10vw, 120px) 0; text-align: center"><div class="rv" style="{NARROW}">' + H("h2", 56, "One team to become<br>the best version of you.", "line-height: 1.08")
            + f'<p style="margin: 22px auto 0; font-size: 17px; color: {MUTED}">Start your consultation today for just $35.</p><div style="margin-top: 32px">{consult()}</div></div></section>')


def why46(big_number=False):
    num = (f'<div aria-hidden="true" class="hide-m pulse" style="position: absolute; right: clamp(20px, 6vw, 96px); bottom: -0.18em; font-family: {SERIF}; font-size: clamp(200px, 26vw, 380px); line-height: 1; color: rgba(192,170,150,.14)">46</div>' if big_number else "")
    return (f'<section class="why46" style="position: relative; overflow: hidden; background: #061A23 url({IMG("chromo.jpg")}) 70% center / cover no-repeat; color: {BG}">{num}<div style="position: relative; {WRAP}"><div class="rv" style="max-width: 600px; padding: clamp(96px, 11vw, 140px) 0">'
            f'<p style="{EYE}; color: {TAN}">Why 46</p>' + H("h2", 60, "46 chromosomes.<br>Only one of you.", f"color: {BG}; line-height: 1.06")
            + '<p style="margin: 24px 0 0; font-size: 17px; line-height: 1.7; color: #ADB7BD">Every cell in your body carries 46 chromosomes, the blueprint that makes you, you. No two people are built the same, so no two plans should be either.</p>'
            '<p style="margin: 14px 0 0; font-size: 17px; line-height: 1.7; color: #ADB7BD">We named the company for that idea. Care at 46 Health starts with the individual, not the product.</p></div></div></section>')


def journey():
    steps = [("10 min", "Online intake", "Tell us about your health, history and goals."), ("~4 hrs", "Provider review", "A licensed provider reviews and messages you."),
             ("Made to order", "Pharmacy", "SureCare compounds and checks your prescription."), ("Ongoing", "Follow-up", "Check-ins, dose changes and refills in your portal.")]
    cells = "".join(f'<li class="rv d{i}" style="position: relative; padding-top: 34px"><span style="position: absolute; top: 0; left: 0; width: 13px; height: 13px; border-radius: 50%; background: {NAVY}; box-shadow: 0 0 0 6px {BG}"></span><div style="font-family: {SERIF}; font-size: 30px; line-height: 1.1">{a}</div><div style="margin-top: 10px; font-size: 13px; letter-spacing: .14em; font-weight: 600; text-transform: uppercase">{b}</div><p style="margin: 8px 0 0; font-size: 15px; line-height: 1.55; color: {MUTED}; max-width: 240px">{c}</p></li>' for i, (a, b, c) in enumerate(steps))
    return (f'<section style="padding: clamp(72px, 9vw, 112px) 0"><div style="{WRAP}"><div class="rv" style="max-width: 640px"><p style="{EYE}; color: #61757D">Our care team</p>' + H("h2", 48, "Real providers. Real follow-up.")
            + f'<p style="margin: 20px 0 0; font-size: 17px; line-height: 1.65; color: {MUTED}">Licensed U.S. medical providers review every intake, prescribe only when treatment is clinically appropriate, and stay with you through dose changes and refills.</p></div>'
            f'<div style="position: relative; margin-top: 56px"><div class="hide-m" style="position: absolute; top: 6px; left: 0; right: 0; height: 1px; background: #C8C0B6"></div><ol style="list-style: none; margin: 0; padding: 0; position: relative; {grid(220)}; gap: 40px">{cells}</ol></div></div></section>')


def about():
    hero = (f'<section style="position: relative; min-height: min(88vh, 820px); display: flex; align-items: flex-end; overflow: hidden; color: {BG}">'
            f'<img class="kb" src="{IMG("h_home.jpg")}" alt="" style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: 50% 12%">'
            f'<div style="position: absolute; inset: 0; background: linear-gradient(180deg, rgba(20,29,33,0) 20%, rgba(20,29,33,.85))"></div>'
            f'<div style="position: relative; {WRAP}; width: 100%; padding-bottom: clamp(56px, 8vw, 96px)"><div class="rv" style="max-width: 760px"><p style="{EYE}; color: #DDE2E4">About 46 Health</p>'
            + H("h1", 76, "Your health. Your life. Our science.", f"color: {BG}; line-height: 1.04")
            + f'<p style="margin: 24px 0 0; font-size: 18px; line-height: 1.65; color: #DDE2E4; max-width: 600px">{LEDE}</p></div></div></section>')
    stats = f'<section style="padding: clamp(56px, 7vw, 88px) 0"><div style="{WRAP}">{stat_strip()}</div></section>'
    rows = ""
    for i, (t, d, img, pos) in enumerate(VALS):
        rev = "row-reverse" if i % 2 else "row"
        rows += (f'<div class="zz" style="display: flex; flex-direction: {rev}; gap: clamp(32px, 6vw, 88px); align-items: center; margin-top: {0 if i == 0 else 96}px">'
                 f'<div class="rv tile" style="flex: 1 1 0; min-width: 0; width: 100%; height: clamp(320px, 38vw, 480px); border-radius: 12px; overflow: hidden"><img src="{IMG(img)}" alt="" style="width: 100%; height: 100%; object-fit: cover; object-position: {pos}"></div>'
                 f'<div class="rv d1" style="flex: 1 1 0; min-width: 0"><div style="font-family: {SERIF}; font-size: 20px; color: {TAN}">0{i+1}</div>' + H("h3", 42, t, "margin-top: 14px")
                 + f'<p style="margin: 18px 0 0; font-size: 17px; line-height: 1.7; color: {MUTED}; max-width: 460px">{d}</p></div></div>')
    values = f'<section style="background: {CARD}; padding: clamp(80px, 9vw, 120px) 0"><div style="{WRAP}"><div class="rv" style="text-align: center; margin-bottom: 72px"><p style="{EYE}; color: #61757D">How we practice</p>' + H("h2", 52, "Care built around you.") + f'</div>{rows}</div></section>'
    body = hero + stats + values + why46() + journey() + surecare_section() + closing("cat5.jpg")
    return document("About", "46 Health is a health and longevity company: one team of licensed providers for the whole you, with medications compounded to order by SureCare Specialty Pharmacy.", body, "About",
                    scripts=f'\n<script src="{u("assets/motion.js") + "?v=" + ASSET_V}"></script>')

def contact():
    def field(i, l, t="text", opt="", ac=""):
        return f'<div style="display: flex; flex-direction: column; gap: 12px"><label for="{i}" style="{LABEL}; font-size: 15px">{l}{opt}</label><input id="{i}" name="{i[2:]}" type="{t}" {ac} {"" if opt else "required"} style="min-height: 52px; border: 1px solid #DDD8D0; background: {BG}; border-radius: 6px; padding: 0 16px; font: inherit; font-size: 15px"></div>'
    radios = "".join(f'<label style="display: inline-flex; align-items: center; gap: 12px; min-height: 44px; font-size: 16px; cursor: pointer"><input type="radio" name="topic" value="{v}" {"required" if v == "treatments" else ""} style="width: 22px; height: 22px; accent-color: {NAVY}; margin: 0">{t}</label>' for v, t in [("treatments", "Treatments"), ("orders", "Orders &amp; Shipping"), ("billing", "Billing"), ("other", "Other")])
    info = "".join(f'<div><div style="{LABEL}; font-size: 13px; color: {MUTED}">{a}</div><div style="font-size: 16px; margin-top: 8px">{b}</div></div>' for a, b in [("Email", "[care@ email]"), ("Phone", "[Phone number]"), ("Hours", "[Mon–Fri, hours, time zone]")])
    body = f'''<section style="padding: 72px 0 40px"><div style="{WRAP}; {grid(420)}; gap: 56px; align-items: start">
<div>{H("h1", 64, "We’re here to help.")}<p style="margin: 28px 0 0; font-size: 17px; line-height: 1.6; max-width: 460px">Questions about treatments, your order or your account? Reach our care team and we’ll respond within one business day.</p><div style="display: flex; gap: 40px; flex-wrap: wrap; margin-top: 40px">{info}</div></div>
<div style="background: {TAUPE}; border-radius: 8px; padding: 40px; text-align: center"><h2 style="margin: 0; font-size: 20px; letter-spacing: 0.1em; font-weight: 500">EXISTING PATIENTS</h2><p style="margin: 16px auto 0; font-size: 16px; line-height: 1.6; max-width: 360px">For medical questions, message your provider through your patient portal.</p><div style="margin-top: 24px">{btn("Open Patient Portal", u("waitlist.html"), attrs="data-portal")}</div></div>
</div></section>
<section style="padding: 0 0 112px"><div style="{WRAP}"><p role="note" style="margin: 0 0 24px; text-align: center; font-size: 16px; font-weight: 500">If you are having a medical emergency, call 911 or go to the nearest emergency room. Do not use this form.</p>
<form data-form="contact" style="background: {WHITE}; border-radius: 8px; padding: clamp(32px, 6vw, 72px) clamp(20px, 8vw, 104px)">
<div style="{grid(260)}; gap: 36px 64px">{field("c-first", "First name", ac='autocomplete="given-name"')}{field("c-last", "Last name", ac='autocomplete="family-name"')}{field("c-email", "Email", "email", ac='autocomplete="email"')}{field("c-phone", "Phone", "tel", " <span style='font-weight:400;text-transform:none;letter-spacing:0;color:#4A545B'>(optional)</span>", 'autocomplete="tel"')}</div>
<fieldset style="border: 0; padding: 0; margin: 44px 0 0"><legend style="{LABEL}; font-size: 15px; padding: 0; margin-bottom: 16px">Topic</legend><div style="display: flex; gap: 16px 48px; flex-wrap: wrap">{radios}</div></fieldset>
<div style="display: flex; flex-direction: column; gap: 10px; margin-top: 44px"><label for="c-msg" style="{LABEL}; font-size: 15px">Message</label><p id="c-msg-help" style="margin: 0; font-size: 14px; color: {MUTED}">Please don’t include medical information here; your patient portal is the secure place for that.</p><textarea id="c-msg" name="message" required aria-describedby="c-msg-help" rows="6" style="margin-top: 6px; border: 1px solid #DDD8D0; background: {BG}; border-radius: 6px; padding: 16px; font: inherit; font-size: 15px; resize: vertical"></textarea></div>
<div style="text-align: center; margin-top: 44px"><button type="submit" style="min-height: 52px; padding: 0 40px; border-radius: 999px; background: {NAVY}; color: #FFFFFF; border: 0; font: inherit; font-size: 16px; font-weight: 500; cursor: pointer">Send Message</button><p class="form-msg" role="status" hidden style="margin: 16px 0 0; font-size: 15px"></p></div>
</form></div></section>'''
    return document("Contact", "Questions about treatments, your order or your account? Reach the 46 Health care team.", body)

FAQ = [
 ("Getting started", [
   ("Do I need a prescription?", "Yes. Every treatment requires a consultation with a licensed provider, who decides whether it’s appropriate for you."),
   ("How long does the consultation take?", "The online intake takes about 10 minutes. A provider typically reviews it within 4 hours and may follow up by message or video."),
   ("Do I need lab work?", "Not to start. Depending on the treatment and your history, your provider may order labs. If you have recent results, you can share them in your intake."),
   ("Which states do you serve?", "All 50 U.S. states. We don’t currently serve U.S. territories or patients outside the United States."),
   ("What if I’m not approved?", "Not everyone is a candidate for every treatment. If your provider decides a therapy isn’t right for you, they’ll explain why and what else to consider. [Refund policy for the consultation fee.]")]),
 ("About the medications", [
   ("What is a compounded medication?", "A medication prepared by a licensed pharmacy for an individual patient’s prescription, often to provide a specific strength or combination. Compounded medications are not FDA-approved, meaning FDA hasn’t reviewed them for safety, effectiveness or quality."),
   ("Who makes my medication?", "SureCare Specialty Pharmacy, a licensed 503A compounding pharmacy in El Paso, Texas."),
   ("Is compounded semaglutide the same as Ozempic or Wegovy?", "No. It contains the same active ingredient but is a different, compounded product that is not FDA-approved. Your provider will prescribe it only when it fits your individual clinical needs."),
   ("Are these safe for competitive athletes?", "Many peptides — including BPC-157, TB-500 and growth hormone secretagogues — are on the World Anti-Doping Agency prohibited list. If you compete in a tested sport, talk with your provider before starting.")]),
 ("Orders and shipping", [
   ("How is my medication shipped?", "In discreet packaging, with cold packs when required, directly from SureCare Specialty Pharmacy. Up to five medications ship together for one shipping fee. Most orders arrive within [X] business days after the prescription is approved."),
   ("Are needles and supplies included?", "Yes. Injectable medications ship with the needles and alcohol pads you need."),
   ("How do refills work?", "Your provider reviews your progress at each check-in and authorizes refills when appropriate."),
   ("Can I cancel?", "Medication orders can’t be cancelled once placed, and prescription medications can’t be returned.")]),
 ("Costs", [
   ("How much does it cost?", "Your consultation is $35. Your medication price is shown before you commit. Peptides start at $69 per vial and GLP-1 programs at $139 per month. See every price on our <a href=\"pricing.html\">pricing page</a>."),
   ("Do you take insurance?", "[Insurance policy — e.g. HSA/FSA eligibility.]")]),
 ("Privacy", [
   ("Is my information private?", "Your health information is protected under HIPAA and shared only with your care team and pharmacy as needed for your treatment. See our <a href=\"privacy.html\">Privacy Policy</a> and <a href=\"notice-of-privacy-practices.html\">Notice of Privacy Practices</a>.")]),
]

def faq():
    jump = "".join(f'<a href="#faq-{i}" style="display: inline-flex; align-items: center; min-height: 40px; padding: 0 18px; border-radius: 999px; border: 1px solid #D3CCC4; background: {WHITE}; font-size: 14px; color: {INK}; text-decoration: none">{t}</a>' for i, (t, _) in enumerate(FAQ))
    secs = ""
    for i, (t, qs) in enumerate(FAQ):
        items = "".join(f'<details style="background: {WHITE}; border-radius: 8px; box-shadow: 0 1px 2px rgba(20,29,33,0.06)"{" open" if i == 0 and j == 0 else ""}><summary style="list-style: none; cursor: pointer; display: flex; justify-content: space-between; align-items: center; gap: 24px; min-height: 64px; padding: 0 clamp(18px, 3vw, 30px); font-size: 16px; font-weight: 600">{q}{CHEV}</summary><p style="margin: 0; padding: 0 clamp(18px, 3vw, 30px) 26px; font-size: 15px; line-height: 1.6">{a}</p></details>' for j, (q, a) in enumerate(qs))
        secs += f'<section id="faq-{i}" style="margin-top: 64px; scroll-margin-top: 24px"><h2 style="margin: 0 0 20px; font-size: 22px; letter-spacing: 0.08em; font-weight: 500; text-transform: uppercase">{t}</h2><div style="display: flex; flex-direction: column; gap: 14px">{items}</div></section>'
    body = f'''<section style="padding: 72px 0 88px"><div style="{NARROW}">{H("h1", 64, "FAQ", "text-align: center")}<nav aria-label="FAQ sections" style="display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; margin-top: 36px">{jump}</nav>{secs}
<div style="text-align: center; margin-top: 72px"><p style="margin: 0; font-size: 16px">Still have a question?</p><div style="margin-top: 20px">{btn("Contact Us", u("contact.html"))}</div></div></div></section>'''
    return document("FAQ", "Answers about consultations, compounded medications, shipping, costs and privacy at 46 Health.", body, "FAQ")

NEWPILL = ' <span style="font-size:11px;letter-spacing:0.12em;border:1px solid #D3CCC4;border-radius:999px;padding:2px 7px;margin-left:6px">NEW</span>'

def pricing():
    order = ["weight-management.html", "peptides.html", "mens-health.html", "womens-health.html", "skin-aesthetics.html"]
    blocks = ""
    for n, f in enumerate(order):
        _, _, groups = PAGES[f]
        rows = ""
        for gid, gt, prods, _ in groups:
            rows += f'<tr class="pr-group"><th colspan="4" scope="colgroup">{gt}</th></tr>'
            for p in prods:
                num = price_num(p) or 0
                monthly = "1" if "month" in (p["unit"] or "") else "0"
                isnew = "1" if p["new"] else "0"
                newpill = NEWPILL if p["new"] else ""
                tog = list_toggle(p).replace('class="list-toggle"', 'class="list-toggle inline"', 1)
                rows += f'<tr class="pr-row" data-price="{num}" data-monthly="{monthly}" data-new="{isnew}"><td><a href="{u(ppath(p))}">{E(p["title"])}</a>{newpill}</td><td class="pr-unit">{E(p["unit"] or "")}</td><td class="num">{E(price_text(p))}</td><td class="pr-add">{tog}</td></tr>'
        count = len(page_products(f))
        label = NAV_TITLE[f].replace("&", "&amp;")
        opened = " open" if n == 0 else ""
        blocks += f'''<details class="pr-cat" id="{f[:-5]}"{opened}><summary><span class="pr-name">{label}</span><span class="pr-count">{count} treatments</span><span class="pr-from">{from_price(f)}</span>{CHEV}</summary>
<div class="pr-body"><div class="table-wrap"><table class="price-table"><thead><tr><th scope="col">Treatment</th><th scope="col">Supply</th><th scope="col" style="text-align: right">Price</th><th scope="col"><span class="sr-only">Add to list</span></th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="pr-empty" hidden>No treatments in this category match that filter.</p><div style="margin-top: 12px">{link("View " + label, u(f))}</div></div></details>'''
    filters = "".join(f'<button type="button" class="pr-filter" data-filter="{k}" aria-pressed="{"true" if k == "all" else "false"}">{t}</button>' for k, t in [("all", "All"), ("under100", "Under $100"), ("monthly", "Monthly programs"), ("new", "New")])
    body = (centered_intro("Clear pricing.<br>No surprises.", "Every treatment has one listed price. Your $35 consultation and medication price are shown before you commit. No membership is required, and up to five medications ship together for one shipping fee.")
            + f'''<div style="max-width: 1000px; margin: 0 auto; padding: 0 clamp(20px, 4vw, 40px) 80px">
<div style="display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 16px"><div role="group" aria-label="Filter prices" style="display: flex; gap: 8px; flex-wrap: wrap">{filters}</div><button type="button" id="pr-expand" class="pr-expand">Expand all</button></div>
{blocks}<p style="margin: 24px 0 0; font-size: 13px; color: {MUTED}; line-height: 1.6">Prices are for medication only and are subject to change. [Consultation fee and shipping cost.] Treatments require a consultation with a licensed provider and are prescribed only when appropriate.</p></div>'''
            + cta_band())
    scripts = f'<script src="{u("assets/pricing.js") + "?v=" + ASSET_V}"></script>'
    return document("Pricing", "Every 46 Health treatment and its price — peptides from $69 per vial, GLP-1 programs from $139 per month.", body, "Pricing", scripts=scripts)


def waitlist():
    names = "".join(f'<span hidden data-treatment-name="{p["slug"]}">{E(p["title"])}</span>' for p in PRODUCTS)
    body = f'''<section style="padding: 80px 0 96px"><div style="{NARROW}; text-align: center">
<p style="{EYEBROW}">Opening soon</p>{H("h1", 60, "Be first to know.")}
<p style="margin: 24px auto 0; font-size: 17px; line-height: 1.65; max-width: 560px">Consultations open soon. We’ll email you the moment they do. Joining doesn’t commit you to anything.</p>
<p hidden style="margin: 20px 0 0; font-size: 15px">You were looking at: <strong id="waitlist-treatment"></strong></p>
<form data-form="waitlist" style="margin: 40px auto 0; max-width: 560px; display: flex; gap: 12px; flex-wrap: wrap; justify-content: center"><label for="wl-email" class="sr-only">Email address</label><input id="wl-email" name="email" type="email" required autocomplete="email" placeholder="Email address" style="flex: 1 1 280px; min-height: 52px; border-radius: 999px; border: 1px solid #D3CCC4; background: {WHITE}; padding: 0 24px; font: inherit; font-size: 15px"><input type="hidden" name="treatment" value=""><button type="submit" style="min-height: 52px; padding: 0 32px; border-radius: 999px; background: {NAVY}; color: #FFFFFF; border: 0; font: inherit; font-size: 16px; font-weight: 500; cursor: pointer">Notify Me</button><p class="form-msg" role="status" hidden style="flex-basis: 100%; margin: 8px 0 0; font-size: 15px"></p></form>
<p style="margin: 20px auto 0; font-size: 13px; color: {MUTED}; max-width: 480px">We only ask for your email here — please don’t share health information.</p>
<div style="margin-top: 48px">{link("Browse treatments", u("treatments.html"))}</div>{names}
</div></section>'''
    return document("Join the waitlist", "Consultations open soon — leave your email to be notified.", body)

LEGAL = {"terms.html": "Terms of use", "privacy.html": "Privacy policy", "notice-of-privacy-practices.html": "Notice of privacy practices",
         "telehealth-consent.html": "Telehealth consent", "careers.html": "Careers"}
def legal(title):
    body = f'<section style="padding: 80px 0 96px"><div style="{NARROW}">{H("h1", 56, title)}<p style="margin: 28px 0 0; font-size: 17px; line-height: 1.65">[{title} — {"to be supplied by counsel" if title != "Careers" else "open roles coming soon"}.]</p><div style="margin-top: 40px">{link("Back to home", u("index.html"))}</div></div></section>'
    return document(title, f"46 Health {title.lower()}.", body)

def consult_list_page():
    actions_btn = "min-height: 44px; padding: 0 20px; border-radius: 999px; border: 1px solid #D3CCC4; background: #FFFFFF; color: #141D21; font: inherit; font-size: 14px; font-weight: 500; cursor: pointer"
    body = f'''<section style="padding: 64px 0 88px"><div style="max-width: 920px; margin: 0 auto; padding: 0 clamp(20px, 4vw, 40px)">
<p style="{EYEBROW}; margin-bottom: 12px">A private note for your consultation</p>
<div style="display: flex; justify-content: space-between; align-items: baseline; gap: 16px; flex-wrap: wrap">{H("h1", 56, "My Consult List")}<span id="list-count-label" style="font-size: 15px; color: {MUTED}"></span></div>
<p style="margin: 18px 0 0; font-size: 16px; line-height: 1.6; max-width: 640px">Save treatments you’d like to ask about. Your provider will review them with you and decide what’s appropriate — this isn’t an order, and you won’t be charged for anything here.</p>
<p style="margin: 10px 0 0; font-size: 14px; line-height: 1.6; color: {MUTED}; max-width: 640px">Your list is saved only in this browser on this device. Nothing is sent to 46 Health.</p>
<noscript><p style="margin-top: 24px">Turn on JavaScript to use your consult list.</p></noscript>
<div id="consult-list" style="margin-top: 36px"></div>
<div id="list-actions" hidden>
<div style="margin-top: 28px"><label for="list-notes" style="display: block; font-size: 15px; font-weight: 600; margin-bottom: 10px">Questions for my provider <span style="font-weight: 400; color: {MUTED}">(optional, saved on this device)</span></label>
<textarea id="list-notes" rows="4" style="width: 100%; border: 1px solid #DDD8D0; background: #FFFFFF; border-radius: 8px; padding: 14px 16px; font: inherit; font-size: 15px; resize: vertical" placeholder="e.g. Which strength is right for me? How long until I’d see a change?"></textarea></div>
<div class="no-print" style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 20px">
<button type="button" id="list-print" style="{actions_btn}">Print or save as PDF</button>
<button type="button" id="list-copy" style="{actions_btn}">Copy list</button>
<button type="button" id="list-email" style="{actions_btn}">Email to myself</button>
<button type="button" id="list-clear" style="{actions_btn}; margin-left: auto; border-color: transparent; background: transparent; text-decoration: underline">Clear list</button>
</div>
<p id="list-msg" role="status" hidden style="margin: 14px 0 0; font-size: 14px"></p>
<div class="no-print" style="margin-top: 40px; padding-top: 32px; border-top: 1px solid #E2DDD6; display: flex; justify-content: space-between; align-items: center; gap: 24px; flex-wrap: wrap"><p style="margin: 0; font-size: 16px; max-width: 440px">Ready to talk it through? Your consultation takes about 10 minutes.</p>{consult()}</div>
<p class="print-only" style="margin-top: 28px; font-size: 12px; color: {MUTED}">Your provider decides what’s appropriate. This list isn’t an order. 46 Health · Prepared by SureCare Specialty Pharmacy, El Paso, TX.</p>
</div></div></section>'''
    scripts = f'<script src="{u("assets/products.js") + "?v=" + ASSET_V}"></script><script src="{u("assets/consult-list.js") + "?v=" + ASSET_V}"></script>'
    return document("My Consult List", "A private list of treatments to discuss with your 46 Health provider.", body, scripts=scripts)

def products_js():
    out = []
    for p in PRODUCTS:
        f = HOME[p["id"]][0]
        summ = p.get("summary") or ""
        if not summ and p.get("desc"):
            first = re.split(r"(?<=[.!?])\s", p["desc"].strip())[0]
            summ = first if len(first) <= 160 else first[:157].rsplit(" ", 1)[0] + "…"
        out.append({"slug": p["slug"], "id": p["id"], "name": p["name"], "title": p["title"], "price": price_text(p), "unit": p["unit"] or "",
                    "img": "assets/img/" + p["image"], "photo": bool(p["photo"]), "url": "products/" + p["slug"] + ".html",
                    "category": NAV_TITLE[f], "summary": summ})
    return "window.PRODUCTS = " + json.dumps(out, ensure_ascii=False) + ";\n"

def notfound():
    body = f'<section style="padding: 96px 0"><div style="{NARROW}; text-align: center">{H("h1", 56, "This page has wandered off.")}<p style="margin: 24px 0 0; font-size: 17px">Let’s get you back on track.</p><div style="margin-top: 36px; display: flex; gap: 20px; justify-content: center; flex-wrap: wrap">{btn("Go Home", u("index.html"))}{link("Browse treatments", u("treatments.html"))}</div></div></section>'
    return document("Page not found", "Page not found.", body)

FAVICON = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="{NAVY}"/><text x="32" y="43" text-anchor="middle" font-family="Georgia, serif" font-size="32" fill="#F2F0EA">46</text></svg>'

# ---------------------------------------------------------------- build
CLEAN_URL = re.compile(r'(["\'(=])((?:\.\./)*(?:[\w-]+/)*[\w-]+)\.html(?=[#?"\')])')

def clean_urls(text):
    # GitHub Pages serves /page.html at /page, so links drop the .html
    def rep(m):
        q, p = m.group(1), m.group(2)
        if p == "index" or p.endswith("/index"):
            p = p[:-5] or "./"
        return q + p
    return CLEAN_URL.sub(rep, text)

def write(path, text):
    if path.endswith((".html", ".js")):
        text = clean_urls(text)
    full = os.path.join(DIST, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w", encoding="utf-8").write(text)

def main():
    global PFX
    os.makedirs(os.path.join(DIST, "assets"), exist_ok=True)
    for f in ("site.css", "site.js"):
        shutil.copy(os.path.join(ROOT, "assets_src", f), os.path.join(DIST, "assets", f))
    shutil.copytree(os.path.join(ROOT, "assets_src", "img"), os.path.join(DIST, "assets", "img"), dirs_exist_ok=True)
    write("assets/favicon.svg", FAVICON)
    write("CNAME", "fortysixhealth.com\n")
    for js in ("consult-list.js", "pricing.js", "home.js", "motion.js"):
        shutil.copy(os.path.join(ROOT, "assets_src", js), os.path.join(DIST, "assets", js))
    PFX = ""
    pages = {"index.html": home(), "treatments.html": treatments(), "how-it-works.html": how(), "about.html": about(),
             "contact.html": contact(), "faq.html": faq(), "pricing.html": pricing(), "waitlist.html": waitlist(), "404.html": notfound(), "consult-list.html": consult_list_page()}
    for f in PAGES:
        t = NAV_TITLE[f]
        pages[f] = document(t, re.sub("<[^>]+>", "", PAGES[f][1]), category_page(f), "Treatments")
    for f, t in LEGAL.items():
        pages[f] = legal(t)
    for f, t in pages.items():
        write(f, t)
    PFX = "../"
    for p in PRODUCTS:
        write(ppath(p), product_page(p))
    write("assets/products.js", products_js())
    PFX = ""
    print(f"Built {len(pages)} pages + {len(PRODUCTS)} product pages into dist/")

if __name__ == "__main__":
    main()

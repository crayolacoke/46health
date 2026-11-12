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
<div class="nav-actions"><a href="{u('consult-list.html')}" class="list-link" aria-label="My Consult List"><svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><rect x="5" y="3.5" width="14" height="17" rx="2"/><path d="M9 3.5V2.5h6v1M8.5 9h7M8.5 13h7M8.5 17h4"/></svg><span class="list-count" hidden></span></a>{btn("Log In", u("waitlist.html"), "ghost", "min-height: 44px; padding: 0 22px; font-size: 14px", 'class="login" data-portal')}{consult("Get Started", extra="min-height: 44px; padding: 0 24px; font-size: 14px").replace("<a ", '<a class="cta" ', 1)}
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
<p style="margin: 28px auto 0; font-size: 17px; line-height: 1.6; max-width: 560px">Your consultation takes about 10 minutes. A provider will be in touch within [X] business days.</p>
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
    items = "".join(f'''<div style="text-align: center">{icon(ic)}<h3 style="margin: 28px auto 0; {LABEL}; font-size: 17px; line-height: 1.4; max-width: 240px">{t}</h3><div style="width: 40px; height: 1.5px; background: {TAN}; margin: 18px auto"></div><p style="margin: 0 auto; font-size: 15px; line-height: 1.6; max-width: 300px">{d}</p></div>''' for ic, t, d in vals)
    return f'''<section style="background: {TAUPE}; padding: {top}px 0 56px"><div style="{WRAP}"><div style="background: {CARD}; border-radius: 8px; padding: clamp(48px, 7vw, 80px) clamp(20px, 4vw, 40px)">{H("h2", 44, title, "text-align: center; margin-bottom: 48px")}<div style="{grid(280)}; gap: 72px 48px; max-width: 900px; margin: 0 auto">{items}</div></div></div></section>'''

def cat_card(c, cta="Learn More", tall=False):
    href, _, t, d, img = c
    return f'''<article style="background: {CARD}; border-radius: 8px; padding: 16px; display: flex; flex-direction: column; box-shadow: 0 1px 2px rgba(20,29,33,0.06)">
<img src="{u('assets/img/' + img)}" alt="" style="width: 100%; height: {300 if tall else 220}px; object-fit: cover; border-radius: 6px; display: block">
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
        media = f'<img src="{u("assets/img/" + p["image"])}" alt="" loading="lazy" style="display: block; width: 100%; aspect-ratio: 921 / 722; object-fit: cover">'
        title = f'<h3 style="margin: 0; font-size: 14px; letter-spacing: 0.06em; font-weight: 600; text-transform: uppercase">{name}</h3><div style="font-size: 13px; color: {MUTED}">{E(p["detail"])}</div>'
        u_html = f'<span style="font-size: 13px; color: {MUTED}; font-weight: 400"> / {unit}</span>' if unit else ""
        unit_line = ""
    else:
        blend = "; mix-blend-mode: multiply" if p["image"] == "gel.png" else ""
        media = f'<div style="height: 150px; display: flex; align-items: center; justify-content: center; padding-top: 16px"><img src="{u("assets/img/" + p["image"])}" alt="" loading="lazy" style="max-height: 100px; max-width: 60%; object-fit: contain{blend}"></div>'
        title = f'<h3 style="margin: 0; font-size: 13.5px; letter-spacing: 0.03em; font-weight: 500; line-height: 1.4; text-transform: uppercase">{name}</h3>'
        u_html = ""
        unit_line = f'<div style="font-size: 12px; color: {MUTED}">{E(unit)}</div>' if unit else ""
    badge = NEW if p["new"] else ""
    toggle = list_toggle(p)
    return f'''<article style="position: relative; background: {TAUPE}; border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; text-align: center">
<a href="{href}" class="card-link" style="display: flex; flex-direction: column; flex: 1">{media}{badge}
<div style="padding: 18px 18px 0; display: flex; flex-direction: column; align-items: center; gap: 6px; flex: 1">{title}
<div style="font-size: 20px; font-weight: 500; font-variant-numeric: tabular-nums; margin-top: auto; padding-top: 10px">{E(price_text(p))}{u_html}</div>{unit_line}</div></a>{toggle}
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
    ("glp1", "GLP-1 programs", ids("sema", "tirz"), "Compounded semaglutide and tirzepatide, dosed weekly and adjusted by your provider. One monthly price at every dose."),
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

def product_page(p):
    f, gid, gt, siblings = HOME[p["id"]]
    cat = NAV_TITLE[f].replace("&", "&amp;")
    img_src = u("assets/img/" + p["image"])
    alt = E(p["title"]) + " vial"
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
    related = [q for q in siblings if q["id"] != p["id"]][:4]
    rel = ""
    if related:
        cards = "".join(product_card(q) for q in related)
        rel = f'<section style="background: {TAUPE}; padding: 56px 0"><div style="{WRAP}">{H("h2", 36, "More in " + gt, "margin-bottom: 32px")}<div style="{grid_fill(250)}; gap: 20px">{cards}</div></div></section>'
    if p["id"] in ("sema", "tirz"):
        disc = DISCLAIMER_GLP1
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
<div style="font-size: 28px; margin-top: 18px; font-variant-numeric: tabular-nums">{E(price_text(p))}{unit}</div>
{summary_html}<p style="margin: 18px 0 0; font-size: 17px; line-height: 1.6">{desc}</p>{other_html}
{cta}
<button type="button" class="list-btn" data-list-add="{p["slug"]}" data-list-name="{E(p["title"])}" aria-pressed="false"><span class="when-off">+ Add to My Consult List</span><span class="when-on">✓ On your consult list</span></button>
<p style="margin: 12px 0 0; font-size: 13px; color: {MUTED}; text-align: center">Prescribed only if appropriate after a provider review. <a href="{u('consult-list.html')}">View my list</a></p>
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
    nums = [n for n in (price_num(p) for p in prods) if n]
    lo = min(nums)
    suffix = " / month" if f == "weight-management.html" else (" per vial" if f == "peptides.html" else "")
    return f"From ${lo}{suffix}"

def home():
    hero_html = f'''<section style="background: #ECE6DA; overflow: hidden"><div style="display: flex; flex-wrap: wrap">
<div class="hero-text" style="flex: 1 1 520px; display: flex; justify-content: flex-end; padding: 80px 56px 80px 40px"><div style="width: 100%; max-width: 560px"><p style="{EYEBROW}">Physician-guided telehealth</p>{H("h1", 60, "The pursuit of excellence.")}
<p style="margin: 24px 0 0; font-size: 17px; line-height: 1.65; max-width: 520px">Browse {len(PRODUCTS)} provider-guided treatments, save the ones you’re curious about, and talk them through with a licensed provider. Prepared by SureCare Specialty Pharmacy and delivered to your door.</p>
<div style="display: flex; gap: 20px; flex-wrap: wrap; align-items: center; margin-top: 32px">{consult()}{link("Browse &amp; build your list", u("treatments.html"))}</div></div></div>
<div class="hero-img" style="flex: 1 1 480px; position: relative"><img src="{u("assets/img/h_home.jpg")}" alt="" style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: center top"><div style="position: absolute; top: 0; bottom: 0; left: 0; width: 120px; background: linear-gradient(90deg, #ECE6DA, rgba(0,0,0,0))"></div></div></div></section>'''
    trust = "".join(f'<li style="flex: 1 1 200px; text-align: center; font-size: 13px; letter-spacing: 0.1em; line-height: 1.5; padding: 6px 16px">{t}</li>' for t in ["LICENSED U.S.<br>PROVIDERS", "PREPARED BY SURECARE<br>SPECIALTY PHARMACY", "DISCREET<br>SHIPPING", "NO MEMBERSHIP<br>FEES"])
    trust_html = f'<section aria-label="Why patients choose us" style="background: {NAVY}; color: #FFFFFF; padding: 24px 0"><ul style="{WRAP}; list-style: none; margin-top: 0; margin-bottom: 0; display: flex; flex-wrap: wrap; gap: 8px; justify-content: space-between">{trust}</ul></section>'
    cols = ""
    for i, (t, d, vig) in enumerate(HOME_STEPS, 1):
        cols += f'''<li style="display: flex; flex-direction: column; gap: 16px"><div class="hiw-visual">{vig()}</div>
<div style="display: flex; align-items: center; gap: 12px"><span aria-hidden="true" style="flex: 0 0 32px; height: 32px; border-radius: 50%; background: {NAVY}; color: #fff; display: inline-flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 600">{i}</span><h3 style="margin: 0; {LABEL}; font-size: 15px"><span class="sr-only">Step {i}: </span>{t}</h3></div>
<p style="margin: 0; font-size: 15px; line-height: 1.6">{d}</p></li>'''
    hiw = f'''<section style="padding: 80px 0"><div style="{WRAP}">
<div style="display: flex; justify-content: space-between; align-items: end; gap: 32px; flex-wrap: wrap; margin-bottom: 40px"><div><p style="{EYEBROW}">How it works</p>{H("h2", 48, "Start with a list, not a checkout.")}</div><p style="margin: 0; font-size: 16px; line-height: 1.6; max-width: 420px">Save what you’re curious about, then talk it through with a licensed provider. Nothing is charged until they decide a treatment is right for you.</p></div>
<ol style="list-style: none; margin: 0; padding: 0; {grid(250)}; gap: 28px">{cols}</ol>
<div style="display: flex; gap: 20px; align-items: center; margin-top: 44px; flex-wrap: wrap">{consult()}{link("See the full process", u("how-it-works.html"))}</div></div></section>'''
    pills = "".join(f'<a href="{u(c[0])}" style="display: inline-flex; align-items: center; gap: 10px; min-height: 48px; padding: 0 20px; border-radius: 999px; background: {WHITE}; border: 1px solid #D3CCC4; text-decoration: none; color: {INK}; font-size: 15px; white-space: nowrap">{c[2]}<span style="font-size: 12px; color: {MUTED}">{from_price(c[0])}</span></a>' for c in CATEGORY_PAGES)
    feat = "".join(product_card(BY_ID[i]) for i in ("sema", "bpc15", "nadinj", "pt141"))
    shop = f'''<section style="background: {TAUPE}; padding: 64px 0"><div style="{WRAP}">
<div style="display: flex; justify-content: space-between; align-items: end; gap: 24px; flex-wrap: wrap; margin-bottom: 24px">{H("h2", 40, "Shop by goal")}{link(f"View all {len(PRODUCTS)} treatments", u("treatments.html"))}</div>
<nav aria-label="Treatment categories" style="display: flex; gap: 10px; flex-wrap: wrap">{pills}</nav>
<div style="display: flex; justify-content: space-between; align-items: baseline; gap: 16px; flex-wrap: wrap; margin: 40px 0 16px"><h3 style="margin: 0; {LABEL}; font-size: 14px">Popular places to start</h3><span style="font-size: 13px; color: {MUTED}">Tap + to save for your consult</span></div>
<div style="{grid_fill(240)}; gap: 16px">{feat}</div></div></section>'''
    ladder = "".join(f'<a href="{u("pricing.html")}#{c[0][:-5]}" class="ladder-row"><span>{c[2]}</span><span class="ladder-from">from <strong>{from_price(c[0]).replace("From ", "").replace(" per vial", "").replace(" / month", "/mo")}</strong></span></a>' for c in CATEGORY_PAGES)
    pricing_band = f'''<section style="background: {NAVY}; color: #fff; padding: 64px 0"><div style="{WRAP}; display: grid; grid-template-columns: repeat(auto-fit, minmax(min(380px, 100%), 1fr)); gap: 48px; align-items: center">
<div>{H("h2", 40, "Clear pricing.<br>No surprises.", "color: #F2F0EA")}<p style="margin: 14px 0 0; font-size: 15px; line-height: 1.6; color: #F2F0EA; max-width: 420px">Every price is listed. No membership fees. Up to five medications ship for one fee.</p><div style="margin-top: 22px">{btn("See all prices", u("pricing.html"), "light", "min-height: 44px")}</div></div>
<nav aria-label="Starting prices by category" class="ladder">{ladder}</nav></div></section>'''
    cta = f'''<section style="background: #ADB7BD; padding: 80px 0; text-align: center"><div style="{NARROW}">{H("h2", 52, "Excellence is a practice.<br>Start yours today.", "line-height: 1.08")}
<p style="margin: 22px auto 0; font-size: 17px; line-height: 1.6; max-width: 560px">Your consultation takes about 10 minutes. A provider will be in touch within [X] business days.</p>
<div style="margin-top: 32px; display: flex; gap: 16px; justify-content: center; flex-wrap: wrap">{consult()}{btn("View my consult list", u("consult-list.html"), "light")}</div></div></section>'''
    body = hero_html + trust_html + hiw + shop + pricing_band + cta
    return document("46 Health", "Physician-guided telehealth: browse provider-guided treatments, save the ones you’re curious about, and talk them through with a licensed provider.", body)

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
    need = check_list(["A government-issued ID", "Your current medications and supplements", f"Recent lab results, if you have them<br><span style='color:{MUTED}'>(not required to start)</span>", f"A shipping address in a state we serve<br><span style='color:{MUTED}'>[List states]</span>"])
    body = (hero("h_how.jpg", "#C9CDCD", "From first question to your front door.",
        "46 Health pairs licensed medical providers with SureCare Specialty Pharmacy, a licensed compounding pharmacy in El Paso, Texas, so you get real medical oversight without the waiting room.")
      + f'''<section style="padding: 80px 0"><div style="{WRAP}">{H("h2", 44, "Here’s exactly what happens", "text-align: center; margin-bottom: 56px")}{bignum_steps(steps)}
<div style="background: {TAUPE}; border-radius: 8px; padding: 56px clamp(20px, 4vw, 40px); margin-top: 88px"><h2 style="margin: 0 0 40px; {LABEL}; font-size: 18px; text-align: center">What you’ll need</h2><ul style="list-style: none; margin: 0 auto; padding: 0; {grid(280)}; gap: 28px 56px; max-width: 760px">{need}</ul></div>
<p style="text-align: center; margin: 32px auto 0; max-width: 680px; font-size: 15px; line-height: 1.6">Not everyone is a candidate for every treatment. If your provider decides a therapy isn’t right for you, they’ll explain why and what else to consider.</p>
<div style="text-align: center; margin-top: 40px">{consult()}</div></div></section>''')
    return document("How it works", "From a 10-minute online intake to a licensed provider review and pharmacy delivery — here’s exactly what happens.", body, "How it works")

def about():
    vals = [("rx", "Providers first", "Every treatment begins with a licensed provider who reviews your history and decides with you what’s appropriate."),
            ("search", "Honest about evidence", "Some therapies have decades of clinical use; others are newer. We tell you which is which."),
            ("flask", "Pharmacy-grade preparation", "Medications are prepared by SureCare Specialty Pharmacy, a licensed 503A compounding pharmacy in El Paso, Texas."),
            ("chat", "Care that continues", "Dosing and protocols are adjusted as you progress, with follow-ups along the way.")]
    team = "".join(f'''<article style="display: flex; flex-direction: column; gap: 16px"><div role="img" aria-label="Photo coming soon" style="aspect-ratio: 4 / 5; background: #D9D9D9; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 13px; color: #555">[Photo]</div><div><h3 style="margin: 0; {LABEL}; font-size: 16px">[Firstname Lastname]</h3><div style="font-size: 14px; font-weight: 600; margin-top: 6px">[Credentials]</div><p style="{P}; font-size: 14px; margin-top: 10px">[Two-sentence bio.]</p></div></article>''' for _ in range(3))
    body = (hero("h_about.jpg", "#EDE8E1", "Better health, on your terms.",
        "46 Health is a telehealth practice built on a simple idea: good care should fit into your life, not the other way around. Our licensed providers take the time to understand your health and your goals, then recommend treatments that make sense for you. When a prescription is right, it’s prepared by a licensed pharmacy and shipped to your door.")
      + values_panel("How we practice", vals)
      + f'''<section style="padding: 80px 0"><div style="{WRAP}">{H("h2", 44, "Our team", "text-align: center; margin-bottom: 56px")}
<div style="{grid(400)}; gap: 56px; align-items: center; margin-bottom: 72px"><div role="img" aria-label="Photo coming soon" style="aspect-ratio: 1 / 1; background: #D9D9D9; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 14px; color: #555">[Medical director photo]</div><div><p style="{EYEBROW}; font-size: 12px; color: {MUTED}">Medical director</p><h3 style="margin: 0; font-size: 24px; font-weight: 400; letter-spacing: 0.06em; text-transform: uppercase">[Firstname Lastname]</h3><div style="font-size: 16px; font-weight: 600; margin-top: 10px">[Credentials]</div><p style="margin: 24px 0 0; font-size: 16px; line-height: 1.6">[Bio — training, areas of focus, and why they practice telehealth medicine.]</p></div></div>
<div style="{grid(260)}; gap: 32px">{team}</div></div></section>'''
      + f'''<section style="background: {TAUPE}; padding: 72px 0"><div style="{WRAP}; display: flex; justify-content: space-between; align-items: center; gap: 48px; flex-wrap: wrap"><div style="max-width: 640px"><p style="{EYEBROW}">Our pharmacy partner</p>{H("h2", 40, "SureCare Specialty Pharmacy")}<p style="margin: 18px 0 0; font-size: 16px; line-height: 1.6">A licensed 503A compounding pharmacy in El Paso, Texas, preparing each prescription for the individual patient. [Accreditations / licensure details.]</p></div></div></section>'''
      + f'<section style="padding: 80px 0; text-align: center"><div style="{NARROW}">{H("h2", 52, "Your best is still ahead.<br>Let’s pursue it together.", "line-height: 1.1")}<div style="margin-top: 36px">{consult()}</div></div></section>')
    return document("About", "46 Health is a telehealth practice built on a simple idea: good care should fit into your life.", body, "About")

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
   ("How long does the consultation take?", "The online intake takes about 10 minutes. A provider typically reviews it within [X] business days and may follow up by message or video."),
   ("Do I need lab work?", "Not to start. Depending on the treatment and your history, your provider may order labs. If you have recent results, you can share them in your intake."),
   ("Which states do you serve?", "[List of states served.]"),
   ("What if I’m not approved?", "Not everyone is a candidate for every treatment. If your provider decides a therapy isn’t right for you, they’ll explain why and what else to consider. [Refund policy for the consultation fee.]")]),
 ("About the medications", [
   ("What is a compounded medication?", "A medication prepared by a licensed pharmacy for an individual patient’s prescription, often to provide a specific strength or combination. Compounded medications are not FDA-approved, meaning FDA hasn’t reviewed them for safety, effectiveness or quality."),
   ("Who makes my medication?", "SureCare Specialty Pharmacy, a licensed 503A compounding pharmacy in El Paso, Texas."),
   ("Is compounded semaglutide the same as Ozempic or Wegovy?", "No. It contains the same active ingredient but is a different, compounded product that is not FDA-approved. Your provider will prescribe it only when it fits your individual clinical needs."),
   ("Are these safe for competitive athletes?", "Many peptides — including BPC-157, TB-500 and growth hormone secretagogues — are on the World Anti-Doping Agency prohibited list. If you compete in a tested sport, talk with your provider before starting.")]),
 ("Orders and shipping", [
   ("How is my medication shipped?", "In discreet packaging, with cold packs when required, directly from SureCare Specialty Pharmacy. Up to five medications ship together for one shipping fee. Most orders arrive within [X] business days after the prescription is approved."),
   ("Are needles and supplies included?", "[Confirm which supplies ship with each order.]"),
   ("How do refills work?", "Your provider reviews your progress at each check-in and authorizes refills when appropriate."),
   ("Can I cancel?", "[Cancellation and refund policy.] Prescription medications generally cannot be returned once shipped.")]),
 ("Costs", [
   ("How much does it cost?", "Your consultation fee and medication price are shown before you commit. Peptides start at $69 per vial and GLP-1 programs at $139 per month. See every price on our <a href=\"pricing.html\">pricing page</a>. [Consultation fee.]"),
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
    body = (centered_intro("Clear pricing.<br>No surprises.", "Every treatment has one listed price. Your consultation fee and medication price are shown before you commit, with no membership fees. Up to five medications ship together for one shipping fee.")
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
def write(path, text):
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
    for js in ("consult-list.js", "pricing.js"):
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

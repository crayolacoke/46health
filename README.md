# 46 Health website

A static catalog site: 19 pages plus one page for each of the 72 products. There's no server code and no database, so it can be hosted almost anywhere for free.

## What's in here

| Path | What it is |
|---|---|
| `dist/` | **The finished website.** Upload this folder to your host. |
| `data/products.json` | Every product's name, price, supply, description, image and NEW flag. **Change prices here.** |
| `build.py` | Turns `products.json` into the pages in `dist/`. Also holds the page copy and which products appear in which group. |
| `assets_src/site.js` | **Settings:** telehealth intake link, patient portal link, form endpoints. |
| `assets_src/site.css` | Base styles (header, mobile menu, tables). |
| `assets_src/img/` | Photos and product images. |

## Changing something

1. Edit `data/products.json` (prices, names, NEW tags) or `build.py` (page wording, grouping).
2. Run `python3 build.py` (needs only Python 3, no packages).
3. Commit and push to GitHub: the site rebuilds and goes live automatically in about a minute.

## Putting it online

The easiest route is **Cloudflare Pages**, **Netlify** or **Vercel** (all free at this size):

- **Quickest:** drag the `dist/` folder into Netlify Drop or Cloudflare Pages "Direct upload".
- **Better long-term:** put this folder in a GitHub repository and connect it to the host, with build command `python3 build.py` and output directory `dist`. Every change you push then goes live automatically.
- Point your domain at the host once you have it. `404.html` is already in place.

## Connecting the telehealth platform

Open `assets_src/site.js` and fill in:

- `INTAKE_URL`: the platform's intake/sign-up link. Every "Get Started" and "Start Your Consultation" button on the site goes there, with the product added as `?treatment=<product-slug>` (for example `?treatment=bpc-157-15-mg`). Until this is set, the buttons go to the waitlist page.
- `PORTAL_URL`: the patient log-in link. The "Log In" button stays hidden until this is set.
- `FORMS.waitlist`, `FORMS.newsletter`, `FORMS.contact`: where the email and contact forms post to (for example Klaviyo or Formspree). Until these are set, the forms say "This form isn't connected yet."

Then run `python3 build.py`.

**Keep patient health information off this site.** Medical history, symptoms and prescriptions belong in the telehealth platform's intake, which must be covered by a BAA. The site's own forms only ask for an email address or a general message.

## Before launch

- Fill in every placeholder shown in square brackets, like `[List states]` or `[Shipping time.]`. Run `grep -rn "\[" dist --include=*.html` to list them.
- Have counsel review product descriptions, the FAQ, the legal pages and the vial label images.
- Add ad or analytics tracking only after a privacy review. Don't send which treatments a visitor looked at to ad platforms.
- The Niacinamide 5% / Retinol cream still needs a price in `products.json`.

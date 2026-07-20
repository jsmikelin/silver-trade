# Silver Trade Website — Developer Onboarding

## Project Overview

| Item | Detail |
|------|--------|
| **Site** | https://www.helinsilver.com |
| **Brand** | HK Changjiang International Limited (香港长江国际有限公司) |
| **Business** | Silver bars/grains/powder export, Hong Kong based |
| **Stack** | Django 4.2 + Gunicorn + static HTML |
| **Hosting** | Render.com (auto-deploy from GitHub) |
| **Repo** | https://github.com/jsmikelin/silver-trade |
| **Domain** | helinsilver.com (DNS managed separately) |

## Project Structure

```
silver-trade/
├── index.html              # Homepage (main marketing page)
├── products/               # Product pages
├── about/                  # About us
├── blog/                   # Market insights
├── contact/                # Contact form
├── jp/                     # Japanese version
├── css/style.css           # Styles
├── js/main.js              # JavaScript
├── images/                 # Product images
├── config/                 # Django settings
├── trading/                # Trading app
├── manage.py               # Django CLI
├── requirements.txt        # Python deps
├── render.yaml             # Render deploy config
└── Procfile                # Process definition
```

## Local Setup

```bash
git clone https://github.com/jsmikelin/silver-trade.git
cd silver-trade
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Deployment

Push to `main` branch → Render auto-deploys.

```bash
git add .
git commit -m "description"
git push origin main
```

Render config is in `render.yaml`. DO NOT modify `render.yaml` without approval.

## Important Rules

1. **Never commit secrets** — API keys, tokens, passwords go in Render Environment Variables, NOT in code
2. **All changes via PR** — create feature branch, submit Pull Request, get approval before merge
3. **Test locally first** — always run `python manage.py runserver` and check before pushing
4. **Don't change Render config** — `render.yaml`, `Procfile`, `requirements.txt` changes need explicit approval
5. **Keep the static HTML in sync** — the homepage is `index.html`, Django serves the rest

## Verification Checklist (every PR must include)

Before submitting a PR, verify ALL of the following:

### Functionality
- [ ] `python manage.py runserver` starts without errors
- [ ] Homepage loads correctly at http://localhost:8000
- [ ] All navigation links work (Home, Products, About, Insights, Contact)
- [ ] WhatsApp button opens wa.me/447599094629
- [ ] Telegram button opens t.me/mikelinsuperbot
- [ ] Contact form submits without errors
- [ ] Japanese version (/jp/) loads correctly
- [ ] Mobile responsive: check at 375px, 768px widths
- [ ] All images load (silver-bar.jpg, silver-grains.jpg, silver-powder.jpg)

### SEO (every PR must include before/after screenshots)
- [ ] `<title>` tag is correct and under 60 chars
- [ ] `<meta name="description">` is under 160 chars and unique
- [ ] `<meta name="keywords">` is relevant
- [ ] All images have `alt` attributes
- [ ] `<h1>` exists exactly once per page
- [ ] Heading hierarchy correct (h1 → h2 → h3, no skips)
- [ ] `<link rel="canonical">` is correct
- [ ] `hreflang` tags present (en, ja, x-default)
- [ ] Structured data (JSON-LD) is valid: test at https://validator.schema.org
- [ ] Open Graph tags (og:title, og:description, og:url) are correct
- [ ] Twitter Card tags are correct
- [ ] `robots.txt` allows crawling
- [ ] `sitemap.xml` is up to date
- [ ] No broken internal links
- [ ] PageSpeed: run https://pagespeed.web.dev and attach screenshot

### SEO Tools
```bash
# Validate structured data
curl -s https://validator.schema.org/validate -F "url=https://www.helinsilver.com"

# Check meta tags
python manage.py check  # Django system checks

# Link checker (local)
pip install linkchecker
linkchecker http://localhost:8000
```

### Before Merge (owner review)
- [ ] PR description explains what changed and why
- [ ] Screenshot of desktop + mobile attached
- [ ] SEO check screenshots attached
- [ ] No changes to pricing, payment terms, or legal text
- [ ] No new external scripts/domains added

## Contact Channels (on website)

| Channel | Link | Type |
|---------|------|------|
| WhatsApp | wa.me/447599094629 | Direct chat |
| Telegram | t.me/mikelinsuperbot | Bot (auto-reply) |
| Email | mikelin88999@gmail.com | Business email |

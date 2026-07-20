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

## Contact Channels (on website)

| Channel | Link | Type |
|---------|------|------|
| WhatsApp | wa.me/447599094629 | Direct chat |
| Telegram | t.me/mikelinsuperbot | Bot (auto-reply) |
| Email | mikelin88999@gmail.com | Business email |

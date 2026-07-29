#!/usr/bin/env python3
"""PR Review Script — 自动验证 silver-trade 网站的 PR。

用法:
  python verify_pr.py [--branch BRANCH] [--pr NUMBER]

检查项:
  1. HTML 结构完整性
  2. SEO 元数据
  3. 结构化数据 (JSON-LD)
  4. 链接有效性
  5. 敏感变更检测
"""
import json
import re
import sys
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from pathlib import Path
from html.parser import HTMLParser

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent
SITE_ORIGIN = "https://helinsilver.com"

class SEOValidator(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = None
        self.title_count = 0
        self.meta_desc = None
        self.keywords = None
        self.h1_count = 0
        self.h2_count = 0
        self.h3_count = 0
        self.imgs_without_alt = 0
        self.links = []
        self.read_more_links = []
        self.scripts = []
        self.json_ld = []
        self.canonical = None
        self.robots = None
        self.og_title = None
        self.og_desc = None
        self.current_tag = None
        self.in_title = False
        self.in_script = False
        self.script_type = ""
        self.script_content = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        self.current_tag = tag

        if tag == "title":
            self.in_title = True
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "h2":
            self.h2_count += 1
        elif tag == "h3":
            self.h3_count += 1
        elif tag == "img":
            if "alt" not in attrs_dict or not attrs_dict["alt"]:
                self.imgs_without_alt += 1
        elif tag == "a" and "href" in attrs_dict:
            self.links.append(attrs_dict["href"])
            if "read-more" in attrs_dict.get("class", "").split():
                self.read_more_links.append(attrs_dict["href"])
        elif tag == "script":
            self.in_script = True
            self.script_type = attrs_dict.get("type", "")
            self.script_content = ""
            if "src" in attrs_dict:
                self.scripts.append(attrs_dict["src"])
        elif tag == "meta":
            name = attrs_dict.get("name", "")
            prop = attrs_dict.get("property", "")
            content = attrs_dict.get("content", "")
            if name == "description":
                self.meta_desc = content
            elif name == "keywords":
                self.keywords = content
            elif name == "robots":
                self.robots = content
            elif prop == "og:title":
                self.og_title = content
            elif prop == "og:description":
                self.og_desc = content
        elif tag == "link" and attrs_dict.get("rel") == "canonical":
            self.canonical = attrs_dict.get("href")

    def handle_data(self, data):
        if self.in_title:
            self.title = (self.title or "") + data
        if self.in_script and "ld+json" in self.script_type:
            self.script_content += data

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "script" and self.in_script:
            self.in_script = False
            if "ld+json" in self.script_type and self.script_content.strip():
                try:
                    self.json_ld.append(json.loads(self.script_content.strip()))
                except json.JSONDecodeError:
                    pass


def check_html(html_path: Path) -> dict:
    """Analyze HTML file for SEO and structure issues."""
    content = html_path.read_text(encoding="utf-8", errors="replace")
    v = SEOValidator()
    v.feed(content)

    issues = []
    warnings = []

    # Title checks
    if not v.title:
        issues.append("Missing <title>")
    elif len(v.title.strip()) > 60:
        warnings.append(f"Title too long ({len(v.title.strip())} chars): {v.title.strip()[:80]}...")

    # Meta description
    if not v.meta_desc:
        issues.append("Missing <meta name='description'>")
    elif len(v.meta_desc) > 160:
        warnings.append(f"Meta description too long ({len(v.meta_desc)} chars)")

    # H1
    if v.h1_count == 0:
        issues.append("Missing <h1>")
    elif v.h1_count > 1:
        issues.append(f"Multiple <h1> tags ({v.h1_count})")

    # Images
    if v.imgs_without_alt > 0:
        warnings.append(f"{v.imgs_without_alt} images missing alt text")

    # Canonical
    if not v.canonical:
        warnings.append("Missing canonical link")
    else:
        canonical = urlparse(v.canonical)
        if canonical.scheme != "https" or canonical.netloc != "helinsilver.com":
            issues.append(f"Canonical must use {SITE_ORIGIN}: {v.canonical}")

    # Open Graph
    if not v.og_title:
        warnings.append("Missing og:title")
    if not v.og_desc:
        warnings.append("Missing og:description")

    # JSON-LD
    if v.json_ld:
        print(f"  ✓ {len(v.json_ld)} JSON-LD blocks found")
    else:
        warnings.append("No JSON-LD structured data found")

    # Prevent recurrence of the About-page corruption introduced by auto-fix branches.
    if html_path.as_posix().endswith("about/index.html"):
        if "S..." in (v.title or "") or "gl..." in (v.meta_desc or ""):
            issues.append("About metadata contains auto-truncated placeholder text")
        if "About Us - Hong Kong Changjiang International Limited | S..." in content:
            issues.append("About page contains an auto-injected duplicate heading")
        if any(block.get("@type") == "Article" for block in v.json_ld if isinstance(block, dict)):
            issues.append("About page must not use Article structured data")

    if "/>/>" in content or "/>>" in content:
        issues.append("Malformed self-closing tag")

    if re.search(
        r"<body>\s*<(?:h1|h2)\b[^>]*>.*?</(?:h1|h2)>\s*<header",
        content,
        re.IGNORECASE | re.DOTALL,
    ):
        issues.append("Auto-injected heading appears before the site header")

    if "..." in (v.title or "") or "..." in (v.meta_desc or ""):
        issues.append("Metadata contains auto-truncated placeholder text")

    article_schemas = [
        block for block in v.json_ld
        if isinstance(block, dict) and block.get("@type") in {"Article", "NewsArticle"}
    ]
    if len(article_schemas) > 1:
        issues.append("Multiple article structured-data blocks")

    if re.search(
        r'<a\b(?=[^>]*\bclass=["\'][^"\']*\bread-more\b[^"\']*["\'])'
        r'(?=[^>]*\bhref=["\']#["\'])[^>]*>',
        content,
        re.IGNORECASE,
    ):
        issues.append("Read More link uses a placeholder href")

    for href in v.read_more_links:
        if href.startswith(("#", "http://", "https://", "mailto:", "tel:")):
            continue
        path = urlparse(href).path.lstrip("/")
        target = REPO / path if Path(path).suffix else REPO / path / "index.html"
        if not target.exists():
            issues.append(f"Read More link points to missing local page: {href}")

    # External scripts
    for s in v.scripts:
        if "googletagmanager" not in s:
            warnings.append(f"External script: {s}")

    return {
        "file": str(html_path.name),
        "title": v.title.strip() if v.title else None,
        "description": v.meta_desc,
        "h1_count": v.h1_count,
        "h2_count": v.h2_count,
        "h3_count": v.h3_count,
        "images_no_alt": v.imgs_without_alt,
        "links": len(v.links),
        "issues": issues,
        "warnings": warnings,
    }


def check_sensitive_changes(diff_output: str) -> list:
    """Check git diff for suspicious changes."""
    alerts = []
    sensitive_patterns = [
        (r'\.env', 'Environment file modified'),
        (r'render\.yaml', 'Render config modified'),
        (r'Procfile', 'Procfile modified'),
        (r'eval\(', 'eval() call detected'),
        (r'exec\(', 'exec() call detected'),
        (r'base64', 'base64 usage detected'),
        (r'document\.write', 'document.write detected'),
        (r'innerHTML\s*=', 'innerHTML assignment detected'),
        (r'\.php', 'PHP file reference'),
        (r'cript:.*\(', 'javascript: URL detected'),
    ]
    for pattern, desc in sensitive_patterns:
        if re.search(pattern, diff_output, re.IGNORECASE):
            alerts.append(f"⚠ {desc}")
    return alerts


def sitemap_urls(sitemap_path: Path) -> list[str]:
    """Parse sitemap locations with an XML parser."""
    root = ET.parse(sitemap_path).getroot()
    return [
        element.text.strip()
        for element in root.findall(".//{*}loc")
        if element.text and element.text.strip()
    ]


def check_sitemap_origin_urls(sitemap_path: Path) -> list[str]:
    """Return sitemap URLs that do not use the canonical HTTPS origin."""
    invalid = []
    for url in sitemap_urls(sitemap_path):
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != "helinsilver.com":
            invalid.append(url)
    return invalid


def check_sitemap_local_urls(sitemap_path: Path) -> list[str]:
    """Return same-site sitemap URLs whose static target does not exist."""
    missing = []

    for url in sorted(set(sitemap_urls(sitemap_path))):
        if urlparse(url).netloc not in {"helinsilver.com", "www.helinsilver.com"}:
            continue
        path = urlparse(url).path.lstrip("/")
        if not path:
            target = REPO / "index.html"
        elif Path(path).suffix:
            target = REPO / path
        else:
            target = REPO / path / "index.html"

        if not target.exists():
            missing.append(url)

    return missing


def check_static_canonical_urls() -> list[str]:
    """Return published static pages whose canonical is not self-referencing."""
    html_paths = [REPO / "index.html", REPO / "404.html"]
    for directory in ("about", "blog", "contact", "products", "jp"):
        html_paths.extend((REPO / directory).rglob("*.html"))

    issues = []
    for html_path in html_paths:
        if not html_path.exists():
            continue
        validator = SEOValidator()
        validator.feed(html_path.read_text(encoding="utf-8", errors="replace"))
        if not validator.canonical or "noindex" in (validator.robots or "").lower():
            continue

        relative = html_path.relative_to(REPO).as_posix()
        if relative == "index.html":
            web_path = "/"
        elif relative.endswith("/index.html"):
            web_path = f"/{relative[:-10]}"
        else:
            web_path = f"/{relative}"
        expected = f"{SITE_ORIGIN}{web_path}"
        if validator.canonical != expected:
            issues.append(
                f"{relative}: canonical {validator.canonical} does not match {expected}"
            )

    return issues


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Verify silver-trade PR")
    parser.add_argument("--diff", help="Path to git diff output")
    args = parser.parse_args()

    print("=" * 50)
    print("Silver Trade PR Verification")
    print("=" * 50)

    all_ok = True

    # 1. HTML checks
    pages = [
        ("Homepage", REPO / "index.html"),
        ("About page", REPO / "about" / "index.html"),
        ("About template", REPO / "trading" / "templates" / "about" / "index.html"),
        ("Contact page", REPO / "contact" / "index.html"),
        ("Contact template", REPO / "trading" / "templates" / "contact" / "index.html"),
        ("Products page", REPO / "products" / "index.html"),
        ("Products template", REPO / "trading" / "templates" / "products" / "index.html"),
        ("Blog index", REPO / "blog" / "index.html"),
        ("Blog template", REPO / "trading" / "templates" / "blog" / "index.html"),
        ("Silver outlook article", REPO / "blog" / "silver-price-outlook-2026.html"),
        ("Hong Kong export article", REPO / "blog" / "hong-kong-silver-export-guide.html"),
        ("US import article", REPO / "blog" / "us-silver-import-guide.html"),
        ("Japan market article", REPO / "blog" / "japan-silver-market-opportunities" / "index.html"),
        ("LBMA article", REPO / "blog" / "lbma-standards-guide" / "index.html"),
        ("Shipping article", REPO / "blog" / "silver-shipping-air-vs-sea" / "index.html"),
        ("LME pricing article", REPO / "blog" / "lme-silver-pricing" / "index.html"),
        ("Japanese homepage", REPO / "jp" / "index.html"),
        ("Japanese homepage template", REPO / "trading" / "templates" / "jp" / "index.html"),
        ("Japanese About page", REPO / "jp" / "about" / "index.html"),
        ("Japanese About template", REPO / "trading" / "templates" / "jp" / "about" / "index.html"),
        ("Japanese Contact page", REPO / "jp" / "contact" / "index.html"),
        ("Japanese Contact template", REPO / "trading" / "templates" / "jp" / "contact" / "index.html"),
        ("Japanese Products page", REPO / "jp" / "products" / "index.html"),
        ("Japanese Products template", REPO / "trading" / "templates" / "jp" / "products" / "index.html"),
        ("Japanese Blog index", REPO / "jp" / "blog" / "index.html"),
        ("Japanese Blog template", REPO / "trading" / "templates" / "jp" / "blog" / "index.html"),
        ("Japanese silver outlook article", REPO / "jp" / "blog" / "silver-price-outlook-2026.html"),
        ("Japanese Hong Kong export article", REPO / "jp" / "blog" / "hong-kong-silver-export-guide.html"),
        ("Japanese US import article", REPO / "jp" / "blog" / "us-silver-import-guide.html"),
        ("Japanese Q3 market article", REPO / "jp" / "blog" / "silver-market-q3-2026" / "index.html"),
        ("Japanese market opportunity article", REPO / "jp" / "blog" / "japan-silver-market-opportunities" / "index.html"),
        ("Japanese LBMA article", REPO / "jp" / "blog" / "lbma-standards-guide" / "index.html"),
        ("Japanese shipping article", REPO / "jp" / "blog" / "silver-shipping-air-vs-sea" / "index.html"),
        ("Japanese LME pricing article", REPO / "jp" / "blog" / "lme-silver-pricing" / "index.html"),
    ]

    # Cover every HTML file, including newly added pages that were not manually listed.
    listed_paths = {path for _, path in pages}
    for index in sorted(REPO.rglob("*.html")):
        if any(part in {".git", ".venv", "node_modules"} for part in index.parts):
            continue
        if index.parent == REPO and index.name.lower().startswith("google"):
            continue
        if index not in listed_paths:
            pages.append((str(index.relative_to(REPO)), index))

    for label, index in pages:
        if not index.exists():
            print(f"\n❌ {label}: expected file is missing: {index.relative_to(REPO)}")
            all_ok = False
            continue
        print(f"\n📄 {label} SEO Check:")
        result = check_html(index)
        print(f"  Title: {result['title']}")
        description = result['description'] or ""
        print(f"  Description: {description[:100]}...")
        print(f"  H1: {result['h1_count']}, H2: {result['h2_count']}, H3: {result['h3_count']}")
        print(f"  Links: {result['links']}")

        for issue in result["issues"]:
            print(f"  ❌ {issue}")
            all_ok = False
        for w in result["warnings"]:
            print(f"  ⚠️  {w}")

    print("\n🗺️  Sitemap local-target check:")
    missing_sitemap_urls = check_sitemap_local_urls(REPO / "sitemap.xml")
    if missing_sitemap_urls:
        all_ok = False
        for url in missing_sitemap_urls:
            print(f"  ❌ Sitemap URL has no local page: {url}")
    else:
        print("  ✅ All same-site sitemap URLs have local targets")

    invalid_sitemap_origins = check_sitemap_origin_urls(REPO / "sitemap.xml")
    if invalid_sitemap_origins:
        all_ok = False
        for url in invalid_sitemap_origins:
            print(f"  ❌ Sitemap URL must use {SITE_ORIGIN}: {url}")
    else:
        print(f"  ✅ All sitemap URLs use {SITE_ORIGIN}")

    try:
        ET.parse(REPO / "feed.xml")
        print("  ✅ RSS feed is valid XML")
    except ET.ParseError as exc:
        all_ok = False
        print(f"  ❌ RSS feed is invalid XML: {exc}")

    canonical_issues = check_static_canonical_urls()
    if canonical_issues:
        all_ok = False
        for issue in canonical_issues:
            print(f"  ❌ {issue}")
    else:
        print("  ✅ All published static pages use self-referencing canonicals")

    # 2. Diff checks
    if args.diff:
        diff_path = Path(args.diff)
        if diff_path.exists():
            print("\n🔍 Sensitive Change Check:")
            diff = diff_path.read_text(encoding="utf-8", errors="replace")
            alerts = check_sensitive_changes(diff)
            if alerts:
                for a in alerts:
                    print(f"  {a}")
            else:
                print("  ✓ No sensitive changes detected")

    print("\n" + "=" * 50)
    if all_ok:
        print("✅ All checks passed")
    else:
        print("❌ Issues found — fix before merging")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())

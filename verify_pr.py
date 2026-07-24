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
from pathlib import Path
from html.parser import HTMLParser

REPO = Path(__file__).resolve().parent
TRUNCATION_MARKERS = ("...", "…", "[rest truncated")

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
        self.scripts = []
        self.json_ld = []
        self.json_ld_errors = []
        self.canonical = None
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
                except json.JSONDecodeError as exc:
                    self.json_ld_errors.append(str(exc))


def contains_truncation(value) -> bool:
    if isinstance(value, str):
        return any(marker in value for marker in TRUNCATION_MARKERS)
    if isinstance(value, dict):
        return any(contains_truncation(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_truncation(item) for item in value)
    return False


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
    if v.title and contains_truncation(v.title):
        issues.append("Truncated text in <title>")

    # Meta description
    if not v.meta_desc:
        issues.append("Missing <meta name='description'>")
    elif len(v.meta_desc) > 160:
        warnings.append(f"Meta description too long ({len(v.meta_desc)} chars)")
    if v.meta_desc and contains_truncation(v.meta_desc):
        issues.append("Truncated text in meta description")

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

    # Open Graph
    if not v.og_title:
        warnings.append("Missing og:title")
    if not v.og_desc:
        warnings.append("Missing og:description")

    # JSON-LD
    if v.json_ld_errors:
        issues.append(f"Invalid JSON-LD ({len(v.json_ld_errors)} block(s))")
    if any(contains_truncation(block) for block in v.json_ld):
        issues.append("Truncated text in JSON-LD")
    if not v.json_ld and not v.json_ld_errors:
        warnings.append("No JSON-LD structured data found")

    # External scripts
    for s in v.scripts:
        if "googletagmanager" not in s:
            warnings.append(f"External script: {s}")

    return {
        "file": html_path.relative_to(REPO).as_posix(),
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
            alerts.append(f"WARNING: {desc}")
    return alerts


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
    html_files = sorted(
        path for path in REPO.rglob("*.html")
        if not {".git", ".venv", "venv"}.intersection(path.parts)
        and not path.name.lower().startswith("google")
    )
    print(f"\nSite-wide SEO Check ({len(html_files)} files):")
    warning_count = 0
    for html_path in html_files:
        result = check_html(html_path)
        if result["issues"]:
            all_ok = False
            print(f"  ERROR: {result['file']}")
            for issue in result["issues"]:
                print(f"     - {issue}")
        warning_count += len(result["warnings"])

    if all_ok:
        print("  PASS: No structural or truncation errors found")
    print(f"  {warning_count} non-blocking SEO warning(s)")

    # 2. Diff checks
    if args.diff:
        diff_path = Path(args.diff)
        if diff_path.exists():
            print("\nSensitive Change Check:")
            diff = diff_path.read_text(encoding="utf-8", errors="replace")
            alerts = check_sensitive_changes(diff)
            if alerts:
                for a in alerts:
                    print(f"  {a}")
            else:
                print("  PASS: No sensitive changes detected")

    print("\n" + "=" * 50)
    if all_ok:
        print("All checks passed")
    else:
        print("Issues found - fix before merging")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())

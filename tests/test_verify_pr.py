import json
import tempfile
import unittest
from pathlib import Path

from verify_pr import check_html, check_sitemap_local_urls


def page(body: str, *, extra_head: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<title>Regression Test Page</title>
<meta name="description" content="A complete regression test description for the published website page.">
<link rel="canonical" href="https://helinsilver.com/test/">
<meta property="og:title" content="Regression Test Page">
<meta property="og:description" content="Regression test description">
{extra_head}
</head>
<body>{body}</body>
</html>
"""


class HtmlRegressionTests(unittest.TestCase):
    def check(self, content: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.html"
            path.write_text(content, encoding="utf-8")
            return check_html(path)["issues"]

    def test_rejects_malformed_self_closing_tag(self):
        issues = self.check(page("<header></header><h1>Test</h1>", extra_head="<link rel=\"dns-prefetch\" href=\"https://example.com\"/>>"))
        self.assertIn("Malformed self-closing tag", issues)

    def test_rejects_heading_injected_before_header(self):
        issues = self.check(page("<h1>Injected title</h1><header></header>"))
        self.assertIn("Auto-injected heading appears before the site header", issues)

    def test_rejects_placeholder_read_more_link(self):
        issues = self.check(page('<header></header><h1>Test</h1><a class="read-more" href="#">Read More</a>'))
        self.assertIn("Read More link uses a placeholder href", issues)

    def test_rejects_duplicate_article_schemas(self):
        schemas = "".join(
            f'<script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@type": schema_type})}</script>'
            for schema_type in ("NewsArticle", "Article")
        )
        issues = self.check(page("<header></header><h1>Test</h1>", extra_head=schemas))
        self.assertIn("Multiple article structured-data blocks", issues)

    def test_accepts_real_article_link(self):
        issues = self.check(page('<header></header><h1>Test</h1><a class="read-more" href="/jp/blog/lme-silver-pricing/">続きを読む</a>'))
        self.assertEqual([], issues)

    def test_rejects_missing_read_more_target(self):
        issues = self.check(page('<header></header><h1>Test</h1><a class="read-more" href="/jp/blog/missing/">続きを読む</a>'))
        self.assertIn("Read More link points to missing local page: /jp/blog/missing/", issues)

    def test_accepts_valid_self_closing_tag(self):
        issues = self.check(page("<header></header><h1>Test</h1>", extra_head='<link rel="dns-prefetch" href="https://example.com"/>'))
        self.assertEqual([], issues)

    def test_sitemap_rejects_missing_same_site_target(self):
        with tempfile.TemporaryDirectory() as directory:
            sitemap = Path(directory) / "sitemap.xml"
            sitemap.write_text(
                '<urlset><url><loc>https://www.helinsilver.com/jp/blog/missing/</loc></url></urlset>',
                encoding="utf-8",
            )
            self.assertEqual(
                ["https://www.helinsilver.com/jp/blog/missing/"],
                check_sitemap_local_urls(sitemap),
            )


if __name__ == "__main__":
    unittest.main()

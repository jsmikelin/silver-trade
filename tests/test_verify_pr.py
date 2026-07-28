import json
import tempfile
import unittest
from pathlib import Path

from verify_pr import check_html


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
        issues = self.check(page('<header></header><h1>Test</h1><a class="read-more" href="/blog/article/">Read More</a>'))
        self.assertEqual([], issues)


if __name__ == "__main__":
    unittest.main()

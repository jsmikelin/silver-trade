import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import Client, TestCase, override_settings

from scripts.update_silver_price import build_price_payload, update_price_file


class SilverPriceUpdaterTests(TestCase):
    def test_builds_daily_feed_and_rejects_invalid_records(self):
        records = [
            {"day": "2026-07-24 00:00:00", "avg_price": "58.325"},
            {"day": "2026-07-27 00:00:00", "avg_price": "59.035"},
            {"day": "2026-07-28", "avg_price": 57.555},
            {"day": "2026-07-26", "avg_price": 58.9},
            {"day": "2027-01-01", "avg_price": 80},
            {"day": "invalid", "avg_price": 99},
        ]

        payload = build_price_payload(
            records,
            fetched_at=datetime(2026, 7, 28, 3, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["schema_version"], 2)
        self.assertEqual(payload["benchmark"], "GoldAPI Silver Daily Average")
        self.assertEqual(payload["market_date"], "2026-07-27")
        self.assertEqual(payload["price"], 59.035)
        self.assertEqual(payload["change"], 0.71)
        self.assertEqual(len(payload["history"]), 2)
        self.assertEqual(
            payload["source"]["data_url"],
            "https://api.gold-api.com/history",
        )

    def test_does_not_rewrite_feed_when_provider_has_no_new_market_data(self):
        records = [
            {"day": "2026-07-24", "avg_price": 58.325},
            {"day": "2026-07-27", "avg_price": 59.035},
        ]
        with TemporaryDirectory() as temporary_dir:
            output = Path(temporary_dir) / "live-price.json"
            with patch(
                "scripts.update_silver_price.fetch_gold_api_history",
                return_value=records,
            ):
                update_price_file(output, api_key="test-key")
                first_content = output.read_text(encoding="utf-8")
                update_price_file(output, api_key="test-key")

            self.assertEqual(output.read_text(encoding="utf-8"), first_content)

    def test_missing_key_fails_before_existing_feed_is_overwritten(self):
        with TemporaryDirectory() as temporary_dir:
            output = Path(temporary_dir) / "live-price.json"
            output.write_text('{"price": 55}\n', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "GOLD_API_KEY is required"):
                update_price_file(output, api_key="")

            self.assertEqual(output.read_text(encoding="utf-8"), '{"price": 55}\n')


class SilverPriceApiTests(TestCase):
    @override_settings(
        STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    def test_homepage_includes_daily_price_widget(self):
        response = Client().get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="priceTrendChart"', count=0)
        self.assertContains(response, 'id="priceDataStatus"')
        self.assertContains(response, "static/js/silver-pricing.js")

    def test_serves_validated_feed_with_cache_headers(self):
        payload = {
            "schema_version": 2,
            "benchmark": "GoldAPI Silver Daily Average",
            "price": 59.035,
            "history": [
                {"date": "2026-07-24", "price": 58.325},
                {"date": "2026-07-27", "price": 59.035},
            ],
        }
        with TemporaryDirectory() as temporary_dir:
            api_dir = Path(temporary_dir) / "api"
            api_dir.mkdir()
            (api_dir / "live-price.json").write_text(
                json.dumps(payload),
                encoding="utf-8",
            )
            with override_settings(BASE_DIR=Path(temporary_dir)):
                response = Client().get("/api/live-price.json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["price"], 59.035)
        self.assertIn("max-age=300", response["Cache-Control"])

    def test_returns_503_when_validated_feed_is_missing(self):
        with TemporaryDirectory() as temporary_dir:
            with override_settings(BASE_DIR=Path(temporary_dir)):
                response = Client().get("/api/live-price.json")

        self.assertEqual(response.status_code, 503)

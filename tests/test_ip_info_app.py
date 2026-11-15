"""Offline unit tests (network mocked). Run: python -m unittest discover tests"""
import os, sys, unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
import ip_info_app as app


def resp(status=200, payload=None, bad_json=False):
    r = mock.Mock(status_code=status)
    if bad_json:
        r.json.side_effect = ValueError()
    else:
        r.json.return_value = payload
    return r


class FetchJsonTests(unittest.TestCase):
    def test_ok(self):
        with mock.patch("requests.get", return_value=resp(payload={"a": 1})):
            self.assertEqual(app.fetch_json("x"), {"a": 1})

    def test_timeout(self):
        with mock.patch("requests.get", side_effect=requests.exceptions.Timeout):
            with self.assertRaisesRegex(app.ApiError, "timed out"):
                app.fetch_json("x")

    def test_rate_limit(self):
        with mock.patch("requests.get", return_value=resp(429)):
            with self.assertRaisesRegex(app.ApiError, "Rate limit"):
                app.fetch_json("x")

    def test_bad_json(self):
        with mock.patch("requests.get", return_value=resp(bad_json=True)):
            with self.assertRaisesRegex(app.ApiError, "valid JSON"):
                app.fetch_json("x")

    def test_api_error_payload(self):
        with mock.patch("requests.get",
                        return_value=resp(payload={"error": True, "reason": "RateLimited"})):
            with self.assertRaisesRegex(app.ApiError, "RateLimited"):
                app.fetch_json("x")


class IpTests(unittest.TestCase):
    def test_ipv4_ok(self):
        with mock.patch.object(app, "fetch_json", return_value={"ip": "203.0.113.5"}):
            self.assertEqual(app.get_public_ip(4), "203.0.113.5")

    def test_wrong_version_rejected(self):
        with mock.patch.object(app, "fetch_json", return_value={"ip": "203.0.113.5"}):
            self.assertIsNone(app.get_public_ip(6))

    def test_ipv6_unavailable(self):
        with mock.patch.object(app, "fetch_json", side_effect=app.ApiError("x")):
            self.assertIsNone(app.get_public_ip(6))

    def test_details_normalised(self):
        raw = {"city": "Manila", "org": "PLDT", "asn": "AS9299", "country_code": "PH"}
        with mock.patch.object(app, "fetch_json", return_value=raw):
            d = app.get_ip_details("1.2.3.4")
        self.assertEqual((d["isp"], d["asn"], d["region"]), ("PLDT", "AS9299", "N/A"))


class MainTests(unittest.TestCase):
    def test_full_report_and_exit_code(self):
        details = {"city": "Manila", "region": "NCR", "country_name": "Philippines",
                   "country_code": "PH", "postal": "1000", "latitude": 14.6,
                   "longitude": 121.0, "timezone": "Asia/Manila", "org": "PLDT",
                   "asn": "AS9299"}
        def fake(url):
            if "api4" in url: return {"ip": "203.0.113.5"}
            if "api6" in url: raise app.ApiError("no ipv6")
            return details
        with mock.patch.object(app, "fetch_json", side_effect=fake):
            rep = app.collect_report()
            text = app.format_report(rep, use_color=False)
            self.assertIn("203.0.113.5", text)
            self.assertIn("No public IPv6", text)
            self.assertIn("Philippines (PH)", text)
            self.assertEqual(app.main(["--no-color"]), 0)

    def test_invalid_manual_ip(self):
        self.assertEqual(app.main(["--ip", "nope"]), 2)

    def test_nothing_found_exit_1(self):
        with mock.patch.object(app, "fetch_json", side_effect=app.ApiError("x")):
            self.assertEqual(app.main(["--no-color"]), 1)


if __name__ == "__main__":
    unittest.main()


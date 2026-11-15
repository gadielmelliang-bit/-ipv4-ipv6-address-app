#!/usr/bin/env python3
"""
IPv4 / IPv6 Address Application
================================
Project Activity 3 (Social Coding) - Option 2: New Code. Section 4ITB.

PURPOSE
    Prototype tool for network technicians. It retrieves and prints the
    computer's CURRENT PUBLIC IPv4 and IPv6 address plus geolocation, ISP,
    ASN and country code, using public REST APIs (no API key needed).

HOW IT WORKS (read this first if you are continuing the projaect)
    1. get_public_ip()      - asks api4.ipify.org / api6.ipify.org for the
                              IPv4 / IPv6 address. Using separate IPv4-only
                              and IPv6-only hosts is how we reliably get BOTH.
    2. get_ip_details()     - asks https://ipapi.co/<ip>/json/ for location,
                              ISP, ASN and country code of that address.
    3. format_report()      - turns the data into an aligned text table.
    4. main()               - ties the steps together and handles CLI options.a

    All network calls go through fetch_json(), the single place where
    timeouts, rate limits (HTTP 429) and bad JSON are handled. Every function
    returns data or raises ApiError, so main() never crashes with a traceback.

USAGE
    python ip_info_app.py              # show IPv4 + IPv6 info
    python ip_info_app.py --ip 8.8.8.8 # look up any address instead
    python ip_info_app.py --json       # raw JSON output (for scripting)
    python ip_info_app.py --no-color   # disable ANSI colours

REQUIREMENTS
    Python 3.8+  and  `pip install requests`

HOW TO CONTINUE THE PROJECT
    See BACKLOG.md. To add a new API provider, write a function with the same
    signature as get_ip_details() and call it from collect_report().
"""

import argparse
import ipaddress
import json
import sys

import requests

# --------------------------------------------------------------------------
# Configuration constants (change here, not deep inside functions)
# --------------------------------------------------------------------------
IPV4_URL = "https://api4.ipify.org?format=json"   # returns {"ip": "x.x.x.x"}
IPV6_URL = "https://api6.ipify.org?format=json"   # returns {"ip": "xxxx::..."}
DETAILS_URL = "https://ipapi.co/{ip}/json/"       # geolocation / ISP / ASN
TIMEOUT_SECONDS = 8                               # per-request network timeout

# ANSI colour codes used for console output.
CYAN, GREEN, YELLOW, RED, BOLD, RESET = (
    "\033[96m", "\033[92m", "\033[93m", "\033[91m", "\033[1m", "\033[0m")


class ApiError(Exception):
    """Raised for any problem talking to a REST API (timeout, 429, bad JSON)."""


# --------------------------------------------------------------------------
# Networking helpers
# --------------------------------------------------------------------------
def fetch_json(url):
    """GET `url` and return the parsed JSON dict.

    Raises ApiError with a human-readable message for:
      * timeouts and connection failures (no internet, no IPv6 route, ...)
      * HTTP 429 (rate limit - ipapi.co free tier is ~1000 requests/day)
      * any other non-200 status code
      * responses that are not valid JSON
      * JSON error payloads such as {"error": true, "reason": "..."}
    """
    try:
        response = requests.get(url, timeout=TIMEOUT_SECONDS)
    except requests.exceptions.Timeout:
        raise ApiError(f"Request timed out after {TIMEOUT_SECONDS}s")
    except requests.exceptions.ConnectionError:
        raise ApiError("Could not connect (check internet / IPv6 availability)")
    except requests.exceptions.RequestException as exc:
        raise ApiError(f"Request failed: {exc}")

    if response.status_code == 429:
        raise ApiError("Rate limit reached (HTTP 429). Wait a while and retry.")
    if response.status_code != 200:
        raise ApiError(f"Server returned HTTP {response.status_code}")

    try:
        data = response.json()
    except ValueError:
        raise ApiError("Server did not return valid JSON")

    if not isinstance(data, dict):
        raise ApiError("Unexpected JSON structure from server")
    if data.get("error"):
        raise ApiError(f"API error: {data.get('reason', 'unknown reason')}")
    return data


def get_public_ip(version):
    """Return our public IP address as a string for `version` (4 or 6).

    Returns None if that IP version is unavailable (common for IPv6 on
    networks without IPv6 - this is NOT treated as a fatal error).
    """
    url = IPV4_URL if version == 4 else IPV6_URL
    try:
        ip = fetch_json(url).get("ip")
    except ApiError:
        return None
    # Validate before trusting it, and make sure it is the version we asked for.
    try:
        parsed = ipaddress.ip_address(ip)
    except (ValueError, TypeError):
        return None
    return str(parsed) if parsed.version == version else None


def get_ip_details(ip):
    """Return a normalised dict of details for `ip` using ipapi.co.

    Keys: city, region, country_name, country_code, postal, latitude,
    longitude, timezone, isp, asn. Missing values become "N/A".
    """
    raw = fetch_json(DETAILS_URL.format(ip=ip))
    return {
        "city": raw.get("city") or "N/A",
        "region": raw.get("region") or "N/A",
        "country_name": raw.get("country_name") or "N/A",
        "country_code": raw.get("country_code") or "N/A",
        "postal": raw.get("postal") or "N/A",
        "latitude": raw.get("latitude", "N/A"),
        "longitude": raw.get("longitude", "N/A"),
        "timezone": raw.get("timezone") or "N/A",
        "isp": raw.get("org") or "N/A",     # ipapi.co calls the ISP "org"
        "asn": raw.get("asn") or "N/A",
    }


# --------------------------------------------------------------------------
# Data collection and formatting
# --------------------------------------------------------------------------
def collect_report(manual_ip=None):
    """Gather everything into a list of entries, one per IP address.

    Each entry: {"version": 4|6, "ip": str, "details": dict | None,
                 "error": str | None}
    """
    if manual_ip:                                   # --ip option
        version = ipaddress.ip_address(manual_ip).version
        targets = [(version, str(ipaddress.ip_address(manual_ip)))]
    else:
        targets = [(v, get_public_ip(v)) for v in (4, 6)]

    report = []
    for version, ip in targets:
        entry = {"version": version, "ip": ip, "details": None, "error": None}
        if ip is None:
            entry["error"] = f"No public IPv{version} address detected"
        else:
            try:
                entry["details"] = get_ip_details(ip)
            except ApiError as exc:
                entry["error"] = str(exc)
        report.append(entry)
    return report


def colorize(text, color, use_color):
    """Wrap `text` in an ANSI colour only when colour is enabled."""
    return f"{color}{text}{RESET}" if use_color else str(text)


def format_report(report, use_color=True):
    """Return the report as a printable, aligned multi-line string."""
    lines = []
    for entry in report:
        title = f" IPv{entry['version']} INFORMATION "
        lines.append(colorize(f"{title:=^50}", CYAN + BOLD, use_color))
        if entry["ip"] is None:
            lines.append(colorize(f"  {entry['error']}", YELLOW, use_color))
            lines.append("")
            continue
        rows = [("IP Address", entry["ip"])]
        d = entry["details"]
        if d:
            rows += [
                ("ISP / Provider", d["isp"]),
                ("ASN", d["asn"]),
                ("Country", f"{d['country_name']} ({d['country_code']})"),
                ("Region / City", f"{d['region']} / {d['city']}"),
                ("Postal Code", d["postal"]),
                ("Coordinates", f"{d['latitude']}, {d['longitude']}"),
                ("Timezone", d["timezone"]),
            ]
        for label, value in rows:
            lines.append(f"  {colorize(f'{label:<16}', GREEN, use_color)}: {value}")
        if entry["error"]:
            lines.append(colorize(f"  ! Details unavailable: {entry['error']}",
                                  RED, use_color))
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Command-line interface
# --------------------------------------------------------------------------
def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Show public IPv4/IPv6 address, location, ISP and ASN.")
    parser.add_argument("--ip", help="look up this IP instead of your own")
    parser.add_argument("--json", action="store_true", help="print raw JSON")
    parser.add_argument("--no-color", action="store_true",
                        help="disable coloured output")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.ip:
        try:
            ipaddress.ip_address(args.ip)
        except ValueError:
            print(f"Error: '{args.ip}' is not a valid IPv4/IPv6 address.",
                  file=sys.stderr)
            return 2

    report = collect_report(args.ip)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        use_color = not args.no_color and sys.stdout.isatty()
        print(format_report(report, use_color))

    # Exit code 1 if we could not get ANY address, so scripts can detect failure.
    return 0 if any(e["ip"] for e in report) else 1


if __name__ == "__main__":
    sys.exit(main())

def test_main_json_returns_zero(self):
        assert main(['--json']) == 0

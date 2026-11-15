# Product Backlog (carried into Project Activity 4)

| ID | Item | Priority | Notes |
|----|------|----------|-------|
| B1 | Fallback API provider (e.g. ipwho.is / ip-api.com) when ipapi.co is rate limited | High | Add a function with the same signature as `get_ip_details()` |
| B2 | Local caching of lookups (JSON file, 1-hour expiry) | High | Avoids burning the free daily quota |
| B3 | Export report to CSV / TXT | Medium | Useful for technicians' tickets |
| B4 | Retry with exponential backoff on timeouts | Medium | Wrap `fetch_json()` |
| B5 | Bulk lookup from a text file of IPs | Medium | `--file ips.txt` |
| B6 | Reverse DNS / hostname and VPN/proxy detection | Low | Needs a provider that offers it |
| B7 | Unit tests in CI (GitHub Actions) | Medium | `python -m unittest discover tests` |
| B8 | Simple GUI or web front end (Tkinter / Flask) | Low | After CLI is stable |
| B9 | Compare IPv4 vs IPv6 provider/location mismatch warning | Low | Useful for tunnel detection |
| B10 | Package as pip-installable CLI (`pyproject.toml`) | Low | |

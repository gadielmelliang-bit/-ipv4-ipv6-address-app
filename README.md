# IPv4/IPv6 Address Application

Project Activity 3 - Social Coding (DEVASC, Section 4ITB), Option 2: New Code.
Shows the computer's current public IPv4 and IPv6 address with geolocation, ISP, ASN and country code.

**Team:** Bariuad, Lemuel Jerome - Fajardo, Zander - Melliang, Gadiel - Penuela, Stephen

## Setup
```bash
git clone https://github.com/4ITB-SocialCoding/ipv4-ipv6-address-app.git
cd ipv4-ipv6-address-app
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage
```bash
python ip_info_app.py              # your public IPv4 + IPv6
python ip_info_app.py --ip 8.8.8.8 # look up any address
python ip_info_app.py --json       # JSON output
python ip_info_app.py --no-color   # plain text
```

## APIs used (free, no key)
- `https://api4.ipify.org` / `https://api6.ipify.org` - public IPv4 / IPv6 address
- `https://ipapi.co/<ip>/json/` - location, ISP (`org`), ASN, country code (free tier is rate limited)

## Tests
```bash
python -m unittest discover tests     # offline, network is mocked
```

## Code map
`fetch_json()` (all HTTP + error handling) -> `get_public_ip()` / `get_ip_details()` -> `collect_report()` -> `format_report()` -> `main()`.
Full comments are in `ip_info_app.py`. Next steps are in `BACKLOG.md`.

## Branch / contribution workflow
`main` is protected. Work on `feature/*`, `docs/*`, `test/*` branches, open a pull request, get one teammate's review, then merge.

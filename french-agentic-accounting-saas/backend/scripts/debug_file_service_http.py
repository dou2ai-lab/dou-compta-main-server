import json
import sys
from typing import Optional

import requests


def _print_resp(label: str, r: requests.Response):
    ct = r.headers.get("content-type")
    print(f"\n--- {label} ---")
    print("status:", r.status_code)
    print("content-type:", ct)
    body = r.text
    print("body (first 1500 chars):")
    print(body[:1500])
    if ct and "application/json" in ct.lower():
        try:
            print("json:")
            print(json.dumps(r.json(), indent=2)[:1500])
        except Exception as e:
            print("json parse error:", type(e).__name__, str(e))


def main(base_url: str = "http://localhost:8005"):
    # Basic GET checks
    for path in ("/health", "/api/v1/test"):
        try:
            r = requests.get(base_url + path, timeout=5)
            _print_resp(f"GET {path}", r)
        except Exception as e:
            print(f"\n--- GET {path} ---")
            print("ERROR:", type(e).__name__, str(e))

    # Upload check
    url = base_url + "/api/v1/receipts/upload"
    headers = {"Authorization": "Bearer dev_mock_token_local"}
    files = {"file": ("debug-test.jpg", b"hello", "image/jpeg")}

    try:
        r = requests.post(url, headers=headers, files=files, timeout=30)
        _print_resp("POST /api/v1/receipts/upload (multipart)", r)
    except Exception as e:
        print("\n--- POST /api/v1/receipts/upload (multipart) ---")
        print("ERROR:", type(e).__name__, str(e))


if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8005"
    main(base)


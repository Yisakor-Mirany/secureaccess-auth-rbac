# SecureAccess: AI Security Audit

This audit reviews the AI-generated first version of SecureAccess. It explains
the security decisions behind the design, then lists weaknesses found by reading
the code **and by attacking the running application**. Finding F1 was reproduced
end to end against the live server.

> **Passing tests is not proof of security.** The automated tests show that the
> controls listed below behave as designed in the scenarios that were tested.
> They do not prove the absence of other flaws. Finding F1 shows this: all 36
> original tests passed while a real denial-of-service weakness was present.

---

## 1. Security decisions and why they were made

| Area | Decision | Reason |
|---|---|---|
| Password storage | Argon2id via `argon2-cffi` (t=3, m=64 MiB, p=4, a random salt per hash) | It's memory-hard, which makes GPU and ASIC cracking expensive. The salt and parameters are stored inside the hash string. |
| Rehashing | `check_needs_rehash()` on successful login | Old hashes are upgraded automatically if the cost parameters are raised later. |
| Login errors | One message: "Invalid username or password." | The response doesn't reveal whether a username exists. |
| Login timing | A dummy Argon2 verify when the user doesn't exist | Without it, unknown usernames would get a measurably faster answer (no Argon2 work), revealing which usernames are valid. |
| Sessions | Flask-Session server-side store. The cookie holds only a random 256-bit ID. | Logout deletes the record on the server, so a copied cookie stops working. Flask's default signed cookie can't be revoked this way. |
| Session fixation | The session ID is regenerated at login | An ID planted before login is useless afterwards. |
| Cookie flags | `HttpOnly`, `SameSite=Lax`, `Secure` set by environment variable, 30-minute lifetime | JavaScript can't read the cookie. It isn't sent on cross-site POSTs. It's HTTPS-only in production. |
| CSRF | Flask-WTF `CSRFProtect` on every POST. JavaScript sends the token in the `X-CSRFToken` header. | A malicious site can't make a logged-in browser log in, log out, or register on its behalf. |
| RBAC | `@login_required` returns 401 and `@role_required("Admin")` returns 401 or 403, enforced on the server | Hidden buttons are cosmetic. The server decides. |
| Role freshness | The role is re-read from the database on every request. Only `user_id` is stored in the session. | A demoted or deleted account loses access immediately. |
| Least privilege | Registration hardcodes `'User'` and ignores any `role` field in the request. A database `CHECK` constraint allows only `User` or `Admin`, defaulting to `User`. | Defense in depth: even a buggy route can't insert an arbitrary role. |
| Admin creation | CLI only (`flask create-admin`) with a hidden, confirmed password prompt | No web path to Admin, no hardcoded credentials, no password in shell history. |
| SQL injection | Every query uses `?` placeholders | User input is sent as data and can never become SQL. |
| Input validation | An allow-list regex for usernames (3–30 characters). Passwords are 12–128 characters, any character allowed. Bodies must be JSON objects. Requests are capped at 16 KB. | Rejects malformed input early. The upper bounds stop huge inputs from tying up the hasher. |
| XSS | Jinja autoescaping, `textContent` in JavaScript (never `innerHTML`), and a strict CSP with no inline scripts | Stored or reflected text can't run as code. |
| Errors | Generic error pages and JSON. Stack traces go only to the server log. | Internals aren't leaked to users. |
| Debug | `FLASK_DEBUG=0` by default. The dev server binds to 127.0.0.1. | The Werkzeug debugger allows remote code execution. |
| Secrets | `SECRET_KEY` comes from `.env`. The app refuses to start if it's missing or still the placeholder. | No secrets in source control. |
| Rate limiting | Flask-Limiter: login allows 5 per minute and 20 per hour per IP, registration allows 10 per hour per IP | Slows online password guessing from a single machine. |
| Caching | `Cache-Control: no-store` on every page | After logout, the Back button can't show a cached dashboard. |

---

## 2. Findings

Severity is my judgment for this app's context, a small internal web app.
"Verified" means I reproduced it against the running app or by inspecting
runtime behavior, not only by reading the code.

### F1: Anonymous request flood logs out every user (Denial of Service). **Verified. High (availability).**

**What's wrong.** Every page includes a CSRF token. Flask-WTF stores that token
in the session, so every visitor *without a cookie* creates a new server-side
session file. The file-based store (`cachelib.FileSystemCache`) is capped at
1,000 files. When it's full, it deletes the sessions **closest to expiry
first**, and those are the real users who logged in earliest.

**How it's exploited.** An attacker needs no account. They send about 1,000
cookieless `GET /login` requests:

```bash
for i in $(seq 1100); do curl -s -o /dev/null http://127.0.0.1:5000/login; done
```

**Evidence (my run against the live server):**

```
Victim /dashboard before flood: 200
Sending 1100 anonymous requests...
Victim /dashboard after flood:  401
VULNERABLE: victim was logged out.
```

The flood took about 25 seconds from one machine. The per-IP login rate limit
doesn't help, because it covers only `POST /login`, not page views. You can
reproduce it yourself with `python scripts/demo_session_flood.py --username <user>`.

**Fix (validated).** Store sessions in a database table instead of a size-capped
file cache. A database never evicts live sessions to make room. Expired rows are
cleaned up every ~100 requests.

1. `pip install Flask-SQLAlchemy==3.1.1` and add it to `requirements.txt`.
2. `app/config.py`:
   ```diff
   -    SESSION_TYPE = "cachelib"           # SESSION_CACHELIB is built in create_app()
   +    SESSION_TYPE = "sqlalchemy"         # SESSION_SQLALCHEMY is set in create_app()
   +    SESSION_CLEANUP_N_REQUESTS = 100    # Delete expired sessions about every 100 requests
   ```
3. `app/__init__.py`:
   ```diff
   -from cachelib.file import FileSystemCache
    from flask import Flask, jsonify, render_template, request
   +from flask_sqlalchemy import SQLAlchemy
   ...
   -    if "SESSION_CACHELIB" not in app.config:
   -        app.config["SESSION_CACHELIB"] = FileSystemCache(
   -            os.path.join(app.instance_path, "flask_session"), threshold=1000, mode=0o600
   -        )
   +    app.config.setdefault(
   +        "SQLALCHEMY_DATABASE_URI", "sqlite:///" + os.path.join(app.instance_path, "sessions.db")
   +    )
   +    # Server-side sessions live in their own SQLite table. Unlike the file
   +    # cache, a database never evicts live sessions when it gets "full".
   +    app.config["SESSION_SQLALCHEMY"] = SQLAlchemy(app)
   ```
   Create the `SQLAlchemy(app)` instance inside `create_app()`, not at module
   level. A module-level instance re-registers the `sessions` table each time
   the tests build a new app, and the tests crash.
4. `tests/conftest.py`: in both app fixtures, replace the `SESSION_CACHELIB` line with
   `"SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(tmp_path / "sessions.db"),`
   and remove the now-unused `FileSystemCache` import.
5. Copy `docs/fix_F1/test_session_flood.py` into `tests/`. **Before** the fix
   it fails every time (6/6 runs). **After** the fix it passes (3/3 runs), and
   so do the other 36 tests.

After the fix, the same 1,100-request flood leaves the victim logged in (`200`).

**Residual risk (be honest about this in your video).** The fix stops the
*eviction*, but each anonymous request still adds a row, so a much larger
flood can still fill the disk. To reduce this further:

- Add a global per-IP limit (e.g. `default_limits=["300 per minute"]`).
- Only issue CSRF tokens on pages that contain forms.
- In production, use Redis or a real database with monitoring and a proper
  reverse-proxy rate limit.

---

### F2: Rate limiting is per-IP, in-memory only, and proxy-unaware. **Partly verified. Medium.**

**Verified.** The 6th login attempt within a minute from one IP gets `429`
(`test_login_rate_limit`).

**Weaknesses (from reading the code and the library's documented behavior):**

1. **No per-account limit.** An attacker with many IPs (a botnet, cloud VMs,
   IPv6 ranges) gets 5 guesses per minute *per IP* against the same account.
   *Password spraying*, trying one common password against many accounts, is
   barely slowed at all.
2. **`memory://` storage.** Counters reset whenever the server restarts. With
   several worker processes (`gunicorn -w 4`), each worker counts
   separately, so the real limit is 4× higher.
3. **Behind a reverse proxy** (nginx, a cloud load balancer), every request
   appears to come from the proxy's IP. Then all users share one bucket, and an
   attacker can lock *everyone* out of login with 5 bad attempts per minute.
   If someone "fixes" that by trusting `X-Forwarded-For` without care, the
   attacker can send a fake header on each request and bypass the limit.

**Recommendations:**

- Add a second limit keyed by the submitted username, e.g. with a custom
  `key_func`.
- Use Redis storage (`RATELIMIT_STORAGE_URI=redis://...`).
- Use `werkzeug.middleware.proxy_fix.ProxyFix(x_for=1)` only when exactly one
  trusted proxy sits in front of the app.
- Prefer progressive delays or a CAPTCHA over hard lockouts, which attackers
  can abuse to lock out victims.

---

### F3: Long but common passwords are accepted. **Verified. Medium.**

`password1234` registered successfully (`201`). The policy checks only length,
12–128 characters, which follows NIST SP 800-63B's advice not to impose
composition rules. But NIST *also* says to reject passwords known to be
common or breached, and the app doesn't do that.

**Exploit.** Password spraying with lists like "password1234",
"qwertyuiop12", "Summer2026!!", combined with F2 (no per-account limit).

**Recommendation.** Reject passwords found in a breach corpus. Options:

- Check against the Have I Been Pwned *Pwned Passwords* range API (k-anonymity:
  only the first 5 characters of the SHA-1 hash are sent).
- Check against a bundled top-100k list.
- Use `zxcvbn` strength estimation.

Apply the same check in `create-admin`.

---

### F4: Passwords can leak into logs, and the audit trail is thin. **Verified. Low–Medium.**

Failed logins are logged with the submitted username:

```
WARNING in auth: Failed login for username='MySecretPass99' from 127.0.0.1
```

Users often type their password into the username box by mistake. That
password then sits in plaintext in the server logs, which are usually far
less protected than the database. On the other side, *successful* logins,
logouts, 403 events and admin page views aren't logged at all. That makes
incident investigation hard (OWASP Top 10 A09: Security Logging and
Monitoring Failures). Using `%r` does prevent log-line injection through
newlines.

**Recommendations:**

- Log only usernames that exist in the database, or a keyed hash or
  truncation of the submitted value.
- Add structured security events: login success or failure, logout, 401 and
  403 with path, admin access, `create-admin` use.
- Alert on spikes.

---

### F5: Username enumeration through registration. **Verified by design. Low.**

Login hides whether a username exists, but registration answers
`409 That username is already taken.` An attacker can check a list of
usernames against `/register`. The 10-per-hour-per-IP limit slows this, but
multiple IPs get around it.

**Trade-off.** Some enumeration is hard to avoid on any site with public
sign-up and unique usernames. Mitigations:

- Stricter registration rate limits or a CAPTCHA.
- Register by email with a confirmation link, then always answer "check your
  inbox".
- Accept that usernames are public and make sure F2 and F3 are strong.

---

### F6: Sliding session lifetime with no absolute timeout. **Verified (config). Low.**

`SESSION_REFRESH_EACH_REQUEST=True`, the Flask default, means each request
pushes expiry 30 minutes further out. A hijacked session that the attacker
keeps busy never expires. There's also no "log out all my sessions" feature,
and no password change, which would normally revoke the other sessions.

**Recommendations:**

- Store `login_at` in the session and reject sessions older than, for
  example, 8 hours, whatever the activity.
- Ask Admins to re-enter their password before sensitive admin actions.
- If password change is added, delete all of that user's sessions when it
  happens.

---

### F7: Argon2 memory cost turns login into a resource-exhaustion vector. **Analysis. Low–Medium.**

Every login attempt, including attempts on usernames that don't exist (because
of the timing dummy hash), uses about **64 MiB of RAM** for roughly 50–100 ms.
Twenty concurrent attempts from different IPs need more than 1.2 GB. The
per-IP limit doesn't cap this across IPs.

**Recommendations:**

- Cap concurrent hashing, for example with a semaphore or worker limits.
- Add a global login rate limit.
- Size the server for peak concurrent logins.
- Tune Argon2 parameters to the hardware. RFC 9106 and OWASP list
  lower-memory profiles with higher time cost.

---

### F8: Things that must change for production (not bugs in local dev, but must be verified)

| Item | Local dev now | Production requirement |
|---|---|---|
| Transport | HTTP on 127.0.0.1 | HTTPS everywhere (TLS at the proxy) |
| `SESSION_COOKIE_SECURE` | `0` (otherwise the browser won't send the cookie over HTTP) | **`1`**, so the cookie is never sent over plain HTTP. HSTS is then sent automatically by the app. |
| Cookie name | `secureaccess_session` | Consider the `__Host-` prefix (`__Host-session`). It forces Secure, Path=/ and no Domain. |
| Server | Werkzeug dev server | Gunicorn or Waitress behind nginx |
| Debug | `FLASK_DEBUG=0` | Must stay `0`. Verify that the deployed environment doesn't set it. |
| `SECRET_KEY` | In `.env` | From a secret manager. Rotate it if leaked. Never commit it. |
| Storage | SQLite files under `instance/` | Restrict file permissions or use a managed database, with backups |
| Admin accounts | Password only | Add MFA (TOTP or WebAuthn) for Admins at least |
| Rate limiting | `memory://` | Redis, plus correct proxy configuration (see F2) |
| Dependencies | Pinned versions | Run `pip-audit` regularly and update |

---

## 3. Controls: implemented vs. verified

**Legend:**

- **Auto**: covered by `pytest` (36 tests, all passing).
- **Live**: checked against the running server with curl or a headless browser.
- **Manual**: you still need to check it yourself (see `QA_CHECKLIST.md`).

| Control | Implemented | Auto | Live | Still needs testing |
|---|---|---|---|---|
| Argon2id hashing, no plaintext stored | ✅ | ✅ | | Inspect the DB in a SQLite viewer |
| Registration always assigns `User` (role injection ignored) | ✅ | ✅ | ✅ | |
| Admin only via CLI, weak password rejected | ✅ | ✅ | ✅ | |
| Generic login error, same message for unknown users | ✅ | ✅ | ✅ | Timing measurement (manual, optional) |
| Logout invalidates the session on the server (stolen cookie rejected) | ✅ | ✅ | ✅ | Show the cookie disappearing in DevTools |
| Session ID regenerated at login | ✅ | ✅ | | Compare cookie values in DevTools |
| HttpOnly / SameSite cookie flags | ✅ | ✅ | ✅ | DevTools → Application → Cookies |
| `Secure` cookie + HSTS over HTTPS | ✅ (env flag) | | | **Untested**: needs an HTTPS deployment |
| CSRF on all POSTs | ✅ | ✅ | ✅ | Try a cross-site form (optional) |
| 401 for unauthenticated / 403 for User on admin endpoints | ✅ | ✅ | ✅ | DevTools → Network tab |
| Role re-checked against the DB each request | ✅ | ✅ | | |
| Parameterized SQL, SQL injection attempts rejected | ✅ | ✅ | | Optional: `sqlmap` against localhost |
| Input validation (empty, too long, wrong type, special characters) | ✅ | ✅ | ✅ | |
| XSS output encoding + CSP | ✅ | partial | ✅ (no CSP violations) | Try `<img src=x onerror=alert(1)>` in inputs |
| Generic error pages, no stack traces | ✅ | ✅ (404 JSON) | | Force a 500 and look at the page |
| Debug off by default | ✅ | ✅ | ✅ | |
| Login rate limiting (per IP) | ✅ | ✅ | | Multi-IP behavior (F2) untested |
| No-store caching after logout | ✅ | ✅ | ✅ | Press Back after logout |
| Session store resists flooding | ❌ (F1) | fix provided | ✅ reproduced | Apply the fix and rerun |
| Breached-password check | ❌ (F3) | | | |
| Per-account throttling | ❌ (F2) | | | |
| Security event logging | partial (F4) | | | |
| Absolute session timeout | ❌ (F6) | | | |
| MFA for Admin | ❌ (F8) | | | |

---

## 4. Suggested correction to demonstrate in the video: F1

1. Start the server and log in as a normal user in the browser. Show the dashboard.
2. In a second terminal, run `python scripts/demo_session_flood.py --username <user>`.
   It prints `VULNERABLE`. Refresh the browser: you're logged out, with a 401.
3. Explain the cause in one sentence: anonymous sessions fill a size-capped
   store that evicts real users first.
4. Apply the fix from F1 (about 10 lines) and copy in the regression test.
5. Run `pytest -v`. All 37 tests pass, including the new one.
6. Run the flood script again. It prints `Session survived.`
7. Mention the residual risk (disk growth) and what you'd do next.

Optional second improvement, if you have time: F3, adding a common-password
blocklist. It's easy to show with a visible before and after.

# SecureAccess: QA Checklist

Fill in the **Result** column as you test. Use ✅ for pass, ❌ for fail, and add
a note for anything unexpected.

**Setup before testing:**

1. Server is running: `python run.py`
2. An admin exists: `flask --app run create-admin`
3. A normal user exists: register one through the website
4. Browser DevTools are open (F12): **Network** tab with "Preserve log" ticked,
   **Application → Cookies → http://127.0.0.1:5000**, and **Console**

## A. Automated tests

| # | Test | How | Expected | Result |
|---|---|---|---|---|
| A1 | Full suite | `pytest -v` | 36 passed (37 after the F1 fix) | |

## B. Authentication

| # | Test | Steps | Expected | Result |
|---|---|---|---|---|
| B1 | Successful registration | Register `testuser1` with a 12+ character password | Green success message, redirect to Login. Network: `POST /register` → **201** | |
| B2 | Duplicate username | Register `TESTUSER1` again | "That username is already taken." → **409** | |
| B3 | Successful login | Log in as `testuser1` | Redirect to Dashboard. Network: `POST /login` → **200** | |
| B4 | Invalid password | Log in with the wrong password | "Invalid username or password." → **401** | |
| B5 | Unknown user | Log in as `nobody123` | Same message as B4 → **401** | |
| B6 | Successful logout | Click **Log out** | Redirect to Home. `POST /logout` → **200**. The session cookie is **gone** from the Cookies panel. | |
| B7 | Back button after logout | Press Back after B6 | No dashboard shown, because the page isn't cached | |
| B8 | Session fixation defense | Note the cookie value on /login, then log in | Cookie value **changes** | |
| B9 | Stolen cookie after logout | Copy the cookie value, log out, then `curl -b "secureaccess_session=<value>" -i http://127.0.0.1:5000/dashboard` | **401** | |
| B10 | Rate limiting | Submit a wrong password 6 times within a minute | 6th attempt: "Too many attempts…" → **429** | |

## C. Authorization (RBAC)

| # | Test | Steps | Expected | Result |
|---|---|---|---|---|
| C1 | Logged-out user → dashboard | Log out, visit `/dashboard` | **401** page with a Log in button | |
| C2 | Logged-out user → admin | Visit `/admin` and `/api/admin/users` | **401** | |
| C3 | User → User dashboard | Log in as `testuser1`, open `/dashboard` | **200**: username, role `User` | |
| C4 | User → Admin dashboard | As `testuser1`, type `/admin` into the address bar | **403** page. No "Admin" link appears in the nav. | |
| C5 | User → Admin API | As `testuser1`, visit `/api/admin/users` | **403** JSON | |
| C6 | Admin → both dashboards | Log in as the admin, open `/dashboard` and `/admin` | Both **200**. The user list shows no password hashes. | |
| C7 | Role injection | Run in the Console on /register: `fetch('/register',{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':document.querySelector('meta[name=csrf-token]').content},body:JSON.stringify({username:'hacker1',password:'hacker-password-1',role:'Admin'})}).then(r=>r.json()).then(console.log)` | Account created, but the admin dashboard shows `hacker1` as **User** | |
| C8 | No public admin route | Look for any admin sign-up option in the UI | None exists | |

## D. Input validation

| # | Test | Steps | Expected | Result |
|---|---|---|---|---|
| D1 | Empty username | Submit register or login with an empty username | "Username is required." (the frontend stops it; the backend also returns 400) | |
| D2 | Empty password | Submit with an empty password | "Password is required." | |
| D3 | Short password | Register with `short` | "Password must be at least 12 characters." | |
| D4 | Special characters in username | Register `<script>alert(1)</script>` | Rejected with a message. No alert pops up. | |
| D5 | Special characters in password | Register with `p@ss w0rd!<>'";--ü` | Registration and login both work | |
| D6 | SQL injection on login | Username `' OR '1'='1' --`, password `anything` | "Invalid username or password." **No login, no crash.** | |
| D7 | SQL injection on register | Username `x'; DROP TABLE users; --` | Rejected by validation. Users are still listed on /admin. | |
| D8 | Missing CSRF token | `curl -i -X POST -H "Content-Type: application/json" -d "{}" http://127.0.0.1:5000/login` | **400**, "Security token missing or invalid…" | |

## E. Browser checks

| # | Test | Steps | Expected | Result |
|---|---|---|---|---|
| E1 | Status codes | Watch the Network tab throughout | Codes match the tables above | |
| E2 | No JavaScript errors | Watch the Console during all tests | No red **JS exceptions** (see the note below) | |
| E3 | Cookie flags | Application → Cookies | `secureaccess_session`: **HttpOnly ✓**, **SameSite Lax**, Secure ✗ (expected on http://) | |
| E4 | `document.cookie` | Type `document.cookie` in the Console while logged in | The session cookie is **not** shown, because of HttpOnly | |
| E5 | Security headers | Network → click any page → Response Headers | `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Cache-Control: no-store` | |
| E6 | Generic errors | Visit `/does-not-exist` | Friendly 404 page with no stack trace | |

> **Note for E2:** Chrome prints lines like *"Failed to load resource: the server
> responded with a status of 401"* whenever a request gets a 4xx response,
> including the 401, 403 and 429 responses you're *deliberately* triggering.
> Those are network log entries, not JavaScript errors. A real JS error looks
> like `Uncaught TypeError: …` with a file and line number.

## F. Audit finding F1 (before and after the fix)

| # | Test | Steps | Expected before fix | Expected after fix | Result |
|---|---|---|---|---|---|
| F1a | Session flood | Log in in the browser, then run `python scripts/demo_session_flood.py --username <user>` | `VULNERABLE`. Browser refresh → 401 | `Session survived.` Still logged in. | |
| F1b | Regression test | Copy `docs/fix_F1/test_session_flood.py` into `tests/`, run `pytest -v` | That test **fails** | All tests pass | |

## Sign-off

| Tester | Date | Python version | Browser | Overall result |
|---|---|---|---|---|
| | | | | |

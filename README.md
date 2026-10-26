# SecureAccess

A small full-stack web app demonstrating **Authentication (AuthN)**,
**Authorization (AuthZ)** and **Role-Based Access Control (RBAC)**. It was
built for a cybersecurity course assignment.

- **Backend:** Python 3.10+, Flask
- **Frontend:** HTML, CSS, vanilla JavaScript (no frameworks)
- **Database:** SQLite (parameterized queries only)
- **Sessions:** server-side (Flask-Session). The browser holds only a random session ID.
- **Passwords:** Argon2id (`argon2-cffi`)
- **Also:** CSRF protection (Flask-WTF), login rate limiting (Flask-Limiter), `python-dotenv`

> ⚠️ This is a learning project. Read [`docs/SECURITY_AUDIT.md`](docs/SECURITY_AUDIT.md)
> before reusing any of it. It lists known weaknesses, including one
> verified denial-of-service issue (F1) with a tested fix.

---

## Features

| Page | URL | Access | If denied |
|---|---|---|---|
| Home | `/` | Everyone | - |
| Register | `/register` | Everyone (always creates role **User**) | - |
| Log in | `/login` | Everyone | - |
| User dashboard | `/dashboard` | Logged-in User or Admin | **401** |
| Admin dashboard | `/admin` | Admin only | **401** (not logged in) / **403** (User) |

JSON API: `GET /api/me` (any logged-in user) and `GET /api/admin/users` (Admin only).
State changes use `POST /register`, `POST /login` and `POST /logout`, all with JSON
bodies and a CSRF token.

Admins **can't** be created through the website. They're created only with a
CLI command (see below).

---

## Setup (Visual Studio Code)

Open the project folder in VS Code, then open a terminal with **Terminal → New Terminal**.

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
```

If PowerShell blocks the activate script, run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
```

### Then, on every platform

1. Open `.env` and paste the generated value into `SECRET_KEY=`.
2. Create the database and an admin account:
   ```bash
   flask --app run init-db
   flask --app run create-admin     # asks for a username and a hidden password (12+ chars)
   ```
3. Start the app:
   ```bash
   python run.py
   ```
4. Visit **http://127.0.0.1:5000**.

In VS Code, press `Ctrl+Shift+P` → **Python: Select Interpreter** → choose the
one inside `.venv`.

To start over, stop the server and delete the `instance/` folder. It holds the
database and session files.

---

## Running the tests

```bash
pytest -v
```

There are 36 tests covering registration, login, logout, the 401/403 rules, the
role-injection attempt, CSRF, rate limiting, session fixation, stolen-cookie
reuse after logout, empty and invalid input, special characters, and SQL
injection attempts.

The manual and browser checklist is in [`docs/QA_CHECKLIST.md`](docs/QA_CHECKLIST.md).

> On Windows PowerShell, use `curl.exe` instead of `curl` in the checklist
> commands. Plain `curl` there is an alias for a different command.

---

## Project structure

```
app/
  __init__.py      App factory: config, extensions, security headers, error handlers
  config.py        Settings read from environment variables (.env)
  extensions.py    CSRF, server-side session and rate-limiter objects
  db.py            SQLite connection + `init-db` command
  schema.sql       users table (UNIQUE NOCASE username, CHECK on role)
  auth.py          Register / login / logout, loads the current user
  routes.py        Home, dashboards, JSON API
  decorators.py    @login_required (401), @role_required (403)
  validation.py    Server-side input rules
  passwords.py     Argon2id hash / verify / rehash
  cli.py           `create-admin` command
  templates/       Jinja2 HTML pages
  static/          style.css, main.js
tests/             pytest suite
scripts/
  demo_session_flood.py   Localhost-only reproduction of audit finding F1
docs/
  SECURITY_AUDIT.md   Security decisions, findings, fixes
  QA_CHECKLIST.md     Manual test checklist
  AI_PROMPTS.md       Prompt log template
  fix_F1/             Regression test to add along with the F1 fix
pytest.ini         Limits pytest to the tests/ folder
run.py             Entry point
```

---

## Key security concepts

- **Authentication vs. authorization.** Authentication is *who are you?*
  (login). Authorization is *what may you do?* (roles).
- **401 vs. 403.** 401 means "not logged in". 403 means "logged in, but not
  allowed".
- **Hashing, not encryption.** Passwords are run through Argon2id, which is
  one-way, salted and deliberately slow and memory-hungry. Even the app can't
  recover the original password.
- **Server-side enforcement.** The Admin link is hidden for normal users, but
  that's only cosmetic. The `/admin` route checks the role itself, so typing
  the URL or using curl still gets a 403.
- **Least privilege.** New accounts are always `User`. Admins are created only
  by someone with shell access to the server. The role is re-read from the
  database on every request, so demotion takes effect immediately.
- **CSRF.** Each page has a secret token that JavaScript sends in the
  `X-CSRFToken` header. A malicious site can't read it, so it can't forge
  requests.
- **SQL injection.** Every query uses `?` placeholders, so input is always
  treated as data, never as SQL.

---

## Local development vs. HTTPS production

The cookie settings in `app/config.py` are set for `http://127.0.0.1`:

| Setting | Local | Production (HTTPS) | Why |
|---|---|---|---|
| `SESSION_COOKIE_SECURE` | `0` | **`1`** | With `Secure`, browsers send the cookie only over HTTPS. Over plain HTTP the cookie would be refused and login would break, so it has to be `0` locally. |
| `SESSION_COOKIE_HTTPONLY` | `True` | `True` | JavaScript can't read the cookie |
| `SESSION_COOKIE_SAMESITE` | `Lax` | `Lax` (or `Strict`) | Not sent on cross-site POSTs |
| HSTS header | off | on automatically when `SESSION_COOKIE_SECURE=1` | Forces HTTPS on future visits |
| `FLASK_DEBUG` | `0` (`1` only while coding) | **always `0`** | The debugger allows remote code execution |
| Server | `python run.py` (Werkzeug dev server) | Gunicorn or Waitress behind nginx with TLS | The dev server isn't built for production |
| Rate-limit storage | `memory://` | Redis | Shared across workers, survives restarts |

See section F8 of the security audit for the full list.

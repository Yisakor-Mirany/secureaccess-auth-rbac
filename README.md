# SecureAccess

A lightweight full-stack web application demonstrating **Authentication (AuthN)**,
**Authorization (AuthZ)**, and **Role-Based Access Control (RBAC)**.

SecureAccess was developed for a cybersecurity course assignment to demonstrate
secure authentication, role-based permissions, vulnerability identification,
security remediation, and software testing.

The application includes user registration, login, logout, protected dashboards,
administrator-only functionality, and security controls.

## Technology Stack

| Component             | Technology                         |
| --------------------- | ---------------------------------- |
| Backend               | Python 3.10+, Flask                |
| Frontend              | HTML, CSS, JavaScript              |
| Database              | SQLite                             |
| Session Management    | Flask-Session with SQLAlchemy      |
| Session Storage       | SQLite-backed server-side sessions |
| Password Hashing      | Argon2id                           |
| CSRF Protection       | Flask-WTF                          |
| Rate Limiting         | Flask-Limiter                      |
| Environment Variables | python-dotenv                      |
| Testing               | pytest                             |

> **Security Notice:** SecureAccess is an educational project and is not
> production-ready without additional security hardening.
>
> See [Security Audit](docs/SECURITY_AUDIT.md) for identified vulnerabilities,
> implemented corrections, and remaining security risks.

---

# Features

## Authentication

- User registration
- User login
- User logout
- Secure password hashing using Argon2id
- Server-side session management
- Session invalidation during logout
- Input validation
- Generic authentication error messages

## Authorization

SecureAccess implements two roles:

**User**

- Can register through the website.
- Can log in and log out.
- Can access the authenticated dashboard.
- Cannot access administrator-only functionality.

**Admin**

- Can log in and log out.
- Can access the authenticated dashboard.
- Can access the administrator dashboard.
- Can access administrator-only API endpoints.

Public registration always creates a standard User account.

Administrator accounts must be created separately using the CLI.

## Security Controls

- Argon2id password hashing
- Server-side session storage
- SQLite-backed sessions
- CSRF protection
- Authentication rate limiting
- Parameterized SQL queries
- Backend role enforcement
- Secure session cookie configuration
- Security response headers
- Input validation and error handling

---

# Application Routes

| Page            | URL          | Access        | Unauthorized Response |
| --------------- | ------------ | ------------- | --------------------- |
| Home            | `/`          | Everyone      | —                     |
| Register        | `/register`  | Everyone      | —                     |
| Login           | `/login`     | Everyone      | —                     |
| User Dashboard  | `/dashboard` | User or Admin | HTTP 401              |
| Admin Dashboard | `/admin`     | Admin only    | HTTP 401 or 403       |

## API Endpoints

| Endpoint               | Access              |
| ---------------------- | ------------------- |
| `GET /api/me`          | Authenticated users |
| `GET /api/admin/users` | Admin only          |

Authentication-related state changes use:

```text
POST /register
POST /login
POST /logout
```

These requests use JSON bodies and CSRF protection.

## HTTP Status Codes

SecureAccess uses standard HTTP responses.

**200 OK**

The request was successful.

**401 Unauthorized**

The visitor is not authenticated.

**403 Forbidden**

The visitor is authenticated but does not have
permission to access the requested resource.

For example, a standard User attempting to access
`/admin` receives HTTP 403.

---

# Installation and Setup

## Requirements

Before starting, install:

- Python 3.10 or newer
- Git
- Visual Studio Code or another code editor

## 1. Clone the Repository

Open a terminal and run:

```bash
git clone https://github.com/Yisakor-Mirany/secureaccess-auth-rbac.git
cd secureaccess-auth-rbac
```

## 2. Create a Virtual Environment

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, adjust the execution policy
according to your system's security requirements.

## 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

The application uses Flask-SQLAlchemy for database-backed
server-side session storage.

## 4. Configure Environment Variables

### macOS / Linux

```bash
cp .env.example .env
```

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

Generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Open `.env` and replace the placeholder `SECRET_KEY`
with the generated value.

Example local development configuration:

```env
SECRET_KEY=replace-with-your-generated-secret
FLASK_DEBUG=0
SESSION_COOKIE_SECURE=0
SESSION_LIFETIME_MINUTES=30
LOGIN_RATE_LIMIT=5 per minute;20 per hour
DATABASE_PATH=secureaccess.db
```

**Important:**

- Never commit `.env` to GitHub.
- Never share your actual `SECRET_KEY`.
- Use `SESSION_COOKIE_SECURE=1` when deploying over HTTPS.
- Keep Flask debug mode disabled in production.

## 5. Initialize the Database

Run:

```bash
flask --app run init-db
```

This creates the application's SQLite user database.

## 6. Create an Administrator

Run:

```bash
flask --app run create-admin
```

Follow the terminal prompts to create an administrator account.

Administrator passwords must meet the application's
password requirements.

Public registration cannot create Admin accounts.

## 7. Start the Application

Run:

```bash
python run.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000
```

You can now:

1. Register a standard User account.
2. Log in.
3. Access the User dashboard.
4. Log out.
5. Log in using an Admin account.
6. Access the Admin dashboard.

---

# Project Structure

```text
secureaccess-auth-rbac/
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── db.py
│   ├── schema.sql
│   ├── auth.py
│   ├── routes.py
│   ├── decorators.py
│   ├── validation.py
│   ├── passwords.py
│   ├── cli.py
│   │
│   ├── templates/
│   │
│   └── static/
│
├── tests/
│   ├── test_session_regression.py
│   └── ...
│
├── scripts/
│   └── demo_session_flood.py
│
├── docs/
│   ├── SECURITY_AUDIT.md
│   ├── QA_CHECKLIST.md
│   ├── AI_PROMPTS.md
│   └── fix_F1/
│
├── instance/
│   └── sessions.db
│
├── requirements.txt
├── pytest.ini
├── run.py
├── .env.example
├── .gitignore
└── README.md
```

**Note:** The `instance/` directory contains local database files
and should not be committed to version control.

---

# Running Automated Tests

SecureAccess uses pytest for automated testing.

Activate the virtual environment and run:

```bash
python -m pytest -v
```

Alternatively:

```bash
python -m pytest -q
```

## Test Coverage

The automated tests cover:

- User registration
- User authentication
- Logout
- Password validation
- Role-based authorization
- HTTP 401 responses
- HTTP 403 responses
- CSRF protection
- Authentication rate limiting
- Session security
- Input validation
- SQL injection-like inputs
- Session regression testing

## Latest Verified Test Results

The original application passed:

```text
36 tests
```

After correcting security finding F1 and adding a regression test:

```text
37 passed, 1408 warnings in 2.39s
```

**Passing Tests:** 37

**Failing Tests:** 0

The warnings were primarily associated with deprecated
datetime behavior in session-related dependencies.

These warnings did not cause test failures, but they
should be reviewed during dependency maintenance.

---

# Security Audit

SecureAccess includes a security audit documenting
the application's protections, vulnerabilities,
and recommended improvements.

The audit is available at:

[docs/SECURITY_AUDIT.md](docs/SECURITY_AUDIT.md)

## Finding F1: Session Eviction Vulnerability

### Original Problem

The initial application used Flask-Session with
a file-based cache.

The cache had a threshold of 1,000 entries.

Repeated anonymous requests could create enough
sessions to cause legitimate authenticated sessions
to be evicted.

This could unexpectedly log users out.

### Security Impact

The vulnerability affected application availability.

An attacker could cause legitimate users to lose
their authenticated sessions.

### Implemented Correction

The original file-based cache was replaced with
SQLite-backed server-side session storage.

The updated configuration includes:

```python
SESSION_TYPE = "sqlalchemy"
SESSION_CLEANUP_N_REQUESTS = 100
```

The session database is stored locally at:

```text
instance/sessions.db
```

This removes the original fixed-size cache eviction behavior.

### Regression Test

A new automated test was created:

```text
tests/test_session_regression.py
```

The test:

1. Creates an original session.
2. Stores a marker in that session.
3. Creates 1,100 additional sessions.
4. Reopens the original session.
5. Confirms that the marker still exists.

### Verification Result

```text
37 passed
0 failed
```

The regression test passed.

This provides evidence that the original
session eviction issue was corrected.

However, SQLite-backed sessions can still
consume server resources under heavy traffic.

Additional production protections are recommended.

---

# Manual QA Testing

Manual testing was performed using the browser
and Chrome DevTools.

## Verified Authorization Behavior

| Test                                 | Expected Result  | Observed Result  |
| ------------------------------------ | ---------------- | ---------------- |
| User accesses `/dashboard`           | 200 OK           | 200 OK           |
| User accesses `/admin`               | 403 Forbidden    | 403 Forbidden    |
| Logged-out visitor accesses `/admin` | 401 Unauthorized | 401 Unauthorized |
| Admin accesses `/dashboard`          | 200 OK           | 200 OK           |
| Admin accesses `/admin`              | 200 OK           | 200 OK           |

Additional input validation and authentication checks
are documented in the QA checklist.

For the complete checklist, see:

[docs/QA_CHECKLIST.md](docs/QA_CHECKLIST.md)

---

# Important Security Concepts

## Authentication vs. Authorization

**Authentication** determines who a user is.

Example:

```text
Logging in with a username and password.
```

**Authorization** determines what the user
is allowed to access.

Example:

```text
Only an Admin can access /admin.
```

## Password Hashing

SecureAccess uses Argon2id.

Passwords are not stored in plaintext.

Argon2id is a password hashing algorithm designed
to make password guessing computationally expensive.

## Server-Side Authorization

The application checks permissions in Flask.

Hiding the Admin navigation link is not
considered a security control.

The `/admin` route verifies the user's role
before returning protected content.

## Least Privilege

Public registration creates only User accounts.

Admin accounts are created separately.

This prevents visitors from assigning themselves
administrator privileges during registration.

## CSRF Protection

SecureAccess uses Flask-WTF to protect
state-changing requests.

JavaScript sends the CSRF token using:

```text
X-CSRFToken
```

## SQL Injection Prevention

Database queries use parameterized SQL.

User-provided values are treated as data
rather than executable SQL statements.

---

# Local Development vs. Production

The application is configured for local development.

Production deployment requires additional security controls.

| Setting                   | Local Development          | Production                   |
| ------------------------- | -------------------------- | ---------------------------- |
| `SESSION_COOKIE_SECURE`   | `0`                        | `1`                          |
| `SESSION_COOKIE_HTTPONLY` | `True`                     | `True`                       |
| `SESSION_COOKIE_SAMESITE` | `Lax`                      | `Lax` or `Strict`            |
| `FLASK_DEBUG`             | `0`                        | `0`                          |
| HTTPS                     | Not required for localhost | Required                     |
| Web Server                | Flask development server   | Production WSGI server       |
| Rate Limit Storage        | In-memory                  | Shared storage such as Redis |
| Security Monitoring       | Limited                    | Recommended                  |

## Additional Production Recommendations

Before deploying publicly:

1. Enable HTTPS.
2. Enable secure cookies.
3. Use a production WSGI server.
4. Configure reverse-proxy request limits.
5. Use shared rate-limit storage.
6. Add security event logging.
7. Monitor database storage and server resources.
8. Configure backups.
9. Implement administrator multifactor authentication.
10. Perform additional penetration and load testing.

---

# AI-Assisted Development

SecureAccess was developed with assistance from
Claude Code and ChatGPT.

AI tools were used for:

- Architecture planning
- Application implementation
- Authentication design
- Authorization implementation
- Security analysis
- Vulnerability remediation
- Regression testing
- Documentation

The original AI-generated implementation
contained a session availability vulnerability.

The vulnerability was identified through
security auditing and corrected.

The project demonstrates the importance
of critically evaluating AI-generated code.

The AI prompt history and evaluation are available at:

[docs/AI_PROMPTS.md](docs/AI_PROMPTS.md)

---

# Documentation

| Document                                 | Description                                    |
| ---------------------------------------- | ---------------------------------------------- |
| [Security Audit](docs/SECURITY_AUDIT.md) | Security controls, findings, and corrections   |
| [QA Checklist](docs/QA_CHECKLIST.md)     | Automated and manual testing                   |
| [AI Prompt Log](docs/AI_PROMPTS.md)      | AI prompts, responses, and critical evaluation |

---

# Project Status

| Requirement                 | Status    |
| --------------------------- | --------- |
| User registration           | Complete  |
| User login                  | Complete  |
| User logout                 | Complete  |
| Secure password hashing     | Complete  |
| User dashboard              | Complete  |
| Admin dashboard             | Complete  |
| Role-based access control   | Complete  |
| SQLite database             | Complete  |
| Server-side sessions        | Complete  |
| CSRF protection             | Complete  |
| Login rate limiting         | Complete  |
| Security audit              | Complete  |
| F1 vulnerability correction | Complete  |
| F1 regression test          | Passed    |
| Automated tests             | 37 passed |
| QA documentation            | Updated   |
| AI prompt log               | Updated   |
| README documentation        | Updated   |
| Final GitHub push           | Pending   |
| Video demonstration         | Pending   |

---

# Conclusion

SecureAccess demonstrates authentication,
authorization, and role-based access control
using Python Flask and SQLite.

The project includes secure password hashing,
server-side sessions, CSRF protection,
input validation, and automated testing.

During the security audit, a session eviction
vulnerability was identified.

The vulnerability was corrected by replacing
file-based session storage with SQLite-backed sessions.

A regression test verified that the original
session remained available after creating
1,100 additional sessions.

The updated application passed all 37 automated tests.

SecureAccess demonstrates both the benefits
and limitations of AI-assisted software development.

AI can accelerate implementation, but developers
remain responsible for reviewing, testing,
and securing the resulting application.

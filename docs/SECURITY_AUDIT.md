# SecureAccess: AI Security Audit

## Overview

SecureAccess is a Flask-based authentication and role-based access control
(RBAC) application developed with assistance from AI tools.

The purpose of this security audit is to evaluate the security of the
AI-generated application, identify vulnerabilities, implement corrections,
and verify the effectiveness of security controls through automated and
manual testing.

The application demonstrates:

- Secure user registration and login
- Argon2id password hashing
- Server-side session authentication
- Role-based authorization
- CSRF protection
- Input validation
- SQL injection prevention
- Secure session cookies
- Rate limiting
- Security-focused error handling

The audit identified eight security findings, labeled F1 through F8.

The most significant confirmed vulnerability, F1, involved a
denial-of-service weakness in the original file-based session storage.

F1 has been corrected by migrating to SQLite-backed server-side sessions.

The updated application successfully passed 37 automated tests.

**Important:** Passing automated tests does not prove that an application
is completely secure. Testing confirms only the scenarios covered by
the test suite.

---

# 1. Application Architecture

## Technology Stack

| Component                 | Technology                    |
| ------------------------- | ----------------------------- |
| Backend                   | Python 3.13 / Flask 3.1.3     |
| Frontend                  | HTML, CSS, JavaScript         |
| Database                  | SQLite                        |
| Password hashing          | Argon2id                      |
| Session management        | Flask-Session                 |
| Session storage           | SQLite using Flask-SQLAlchemy |
| CSRF protection           | Flask-WTF                     |
| Rate limiting             | Flask-Limiter                 |
| Environment configuration | python-dotenv                 |
| Automated testing         | pytest                        |
| Version control           | Git and GitHub                |

## Application Access Levels

SecureAccess provides three access levels.

### Public Access

Accessible without authentication.

Examples:

- Home page
- Registration page
- Login page

### Authenticated User Access

Accessible to authenticated users with either the User or Admin role.

Example:

- `/dashboard`

Unauthenticated requests receive:

HTTP 401 Unauthorized

### Administrator Access

Accessible only to authenticated users with the Admin role.

Example:

- `/admin`

Expected responses:

- Admin user: HTTP 200 OK
- Standard User: HTTP 403 Forbidden
- Unauthenticated visitor: HTTP 401 Unauthorized

Authorization decisions are enforced by the Flask backend.

Hiding administrator navigation links in the frontend is not considered
a sufficient security control.

---

# 2. Security Controls and Design Decisions

| Security Area            | Implementation                                | Security Benefit                                    |
| ------------------------ | --------------------------------------------- | --------------------------------------------------- |
| Password storage         | Argon2id with random salts                    | Protects stored passwords against offline guessing  |
| Password rehashing       | Rehash check after successful login           | Allows password hashes to be upgraded               |
| Login errors             | Generic authentication error                  | Reduces username enumeration                        |
| Login timing             | Dummy Argon2 verification                     | Reduces timing differences for nonexistent accounts |
| Session authentication   | Flask-Session                                 | Keeps session data on the server                    |
| Session storage          | SQLite-backed sessions                        | Prevents size-based eviction of active sessions     |
| Session fixation         | Regenerate session identifier during login    | Reduces session fixation risk                       |
| Cookie security          | HttpOnly, SameSite=Lax                        | Reduces cookie exposure                             |
| HTTPS cookies            | Secure flag controlled by environment         | Restricts cookies to HTTPS in production            |
| CSRF protection          | Flask-WTF                                     | Protects state-changing requests                    |
| Authorization            | Server-side role guards                       | Prevents unauthorized resource access               |
| Role freshness           | Read current role from database               | Enforces role changes on subsequent requests        |
| Registration roles       | New users receive User role                   | Prevents self-registration as Admin                 |
| Administrator creation   | CLI-only admin creation                       | Restricts privileged account creation               |
| SQL injection prevention | Parameterized SQL queries                     | Separates user input from SQL statements            |
| Input validation         | Username and password validation              | Rejects malformed requests                          |
| XSS prevention           | Template escaping and Content Security Policy | Reduces script injection risk                       |
| Error handling           | Generic error responses                       | Avoids exposing internal application details        |
| Debug configuration      | Disabled by default                           | Prevents debugger exposure                          |
| Secrets                  | Environment variables                         | Keeps secrets out of source code                    |
| Rate limiting            | Flask-Limiter                                 | Reduces automated password guessing                 |
| Cache protection         | Cache-Control: no-store                       | Prevents sensitive page caching                     |

---

# 3. Security Findings

## F1 — Session Flood Denial-of-Service Vulnerability

**Severity:** High

**Category:** Availability / Session Management

**Status:** FIXED AND REGRESSION-TESTED

**Date:** October 27, 2026

### Original Vulnerability

The original application used Flask-Session with a file-based
session cache.

The cache was configured using:

```python
FileSystemCache(
    cache_dir,
    threshold=1000,
    mode=0o600
)
```

The maximum threshold was 1,000 cached entries.

The application also generated CSRF tokens for visitors.

Because CSRF tokens were stored in server-side sessions,
anonymous visitors could create session records without
authenticating.

An attacker could repeatedly request pages without preserving
session cookies.

This caused the file-based cache to accumulate sessions.

When the cache reached its configured threshold, valid sessions
could be evicted.

Consequently, authenticated users could unexpectedly lose
their active sessions.

### Original Attack Demonstration

A test against the original implementation produced:

```text
Victim /dashboard before flood: 200

Sending 1100 anonymous requests...

Victim /dashboard after flood: 401

VULNERABLE: victim was logged out.
```

This demonstrated a session availability weakness.

The login rate limiter did not prevent the attack because
the requests targeted GET endpoints rather than login attempts.

### Root Cause

The underlying problem was the use of a size-limited
file cache for authentication sessions.

Authentication sessions should not be removed simply because
unrelated anonymous visitors create additional sessions.

The original design allowed an attacker to affect the
availability of legitimate users' sessions.

### Security Correction

The application was updated to use SQLite-backed
server-side session storage.

Flask-SQLAlchemy was installed:

```bash
python -m pip install Flask-SQLAlchemy==3.1.1
```

The dependency was added to `requirements.txt`:

```text
Flask-SQLAlchemy==3.1.1
```

The session configuration was changed from:

```python
SESSION_TYPE = "cachelib"
```

To:

```python
SESSION_TYPE = "sqlalchemy"
SESSION_CLEANUP_N_REQUESTS = 100
```

The application factory was updated to configure a dedicated
SQLite database for session storage.

The resulting configuration uses:

```text
SESSION_TYPE=sqlalchemy
```

With session data stored in:

```text
instance/sessions.db
```

The session database is separate from the application's
primary user database.

### Why This Fix Works

The SQLite-backed session store does not use the original
1,000-entry file-cache eviction threshold.

Creating additional anonymous sessions no longer causes
legitimate sessions to be evicted because that threshold
has been reached.

Expired session records can be cleaned up periodically.

This improves session availability under the specific
attack scenario identified during the audit.

### Regression Test

A dedicated regression test was added:

```text
tests/test_session_regression.py
```

The test performs the following actions:

1. Creates a Flask application with SQLite-backed sessions.
2. Creates an original client session.
3. Stores a test marker in the original session.
4. Creates 1,100 additional sessions.
5. Checks whether the original session still exists.
6. Confirms that the original session marker remains available.

### Regression Test Result

```text
PASSED
```

The original session remained available after the additional
sessions were created.

### Complete Automated Test Results

Command:

```bash
python -m pytest -q
```

Result:

```text
37 passed, 1408 warnings in 2.39s
```

**Total tests:** 37

**Passed:** 37

**Failed:** 0

The test suite includes the new session regression test.

### Remaining Risk

The correction eliminates the specific cache-eviction
vulnerability demonstrated in F1.

However, it does not eliminate all denial-of-service risks.

An attacker generating large numbers of sessions could still
consume database storage or other server resources.

Additional production protections should include:

- Global request rate limiting
- Reverse-proxy request limits
- Database storage monitoring
- Automated cleanup of expired sessions
- Infrastructure resource limits
- Production-grade session storage where appropriate

### Security Lesson

AI-generated authentication code should never be trusted
without independent security review.

The original application passed its functional tests even
though a denial-of-service weakness remained.

Dedicated adversarial testing identified the problem.

The vulnerability was corrected and verified using an
automated regression test.

---

## F2 — Rate Limiting Weaknesses

**Severity:** Medium

**Status:** PARTIALLY VERIFIED — IMPROVEMENTS RECOMMENDED

### Description

SecureAccess uses Flask-Limiter to restrict login attempts.

The application limits login attempts to approximately:

- 5 attempts per minute per IP address
- 20 attempts per hour per IP address

Registration is also rate-limited.

These controls reduce repeated authentication attempts
from a single IP address.

However, IP-based rate limiting alone does not provide
complete protection against distributed attacks.

### Identified Weaknesses

#### 1. No Per-Account Rate Limiting

An attacker using multiple IP addresses could attempt
authentication against the same account.

Each IP address would receive its own rate limit.

#### 2. In-Memory Rate Limit Storage

The current development configuration uses memory-based
rate limit counters.

Counters can reset when the application restarts.

Multiple application workers may maintain separate counters.

#### 3. Reverse Proxy Configuration

When deployed behind a reverse proxy, the application
must correctly determine the trusted client IP address.

Incorrect configuration could cause all visitors to share
the same rate limit.

Blindly trusting client-supplied forwarding headers could
allow attackers to bypass IP-based limits.

### Verification

Automated testing confirmed that excessive login attempts
from the same client can produce:

```text
HTTP 429 Too Many Requests
```

### Recommendations

- Add per-account login throttling.
- Use Redis for shared rate-limit storage.
- Configure trusted reverse proxies correctly.
- Monitor suspicious login activity.
- Consider progressive delays for repeated failures.

### Current Assessment

The existing rate limiter provides useful protection
against basic repeated login attempts.

Additional controls are recommended before production deployment.

---

## F3 — Common Passwords Are Accepted

**Severity:** Medium

**Status:** VERIFIED — NOT FIXED

### Description

SecureAccess validates password length.

Passwords must contain between 12 and 128 characters.

The application does not require arbitrary combinations
of uppercase letters, numbers, and symbols.

This is consistent with modern password guidance that
discourages unnecessary composition rules.

However, password length alone does not guarantee strength.

### Identified Weakness

A commonly used password such as:

```text
password1234
```

can satisfy the application's minimum length requirement.

The application does not currently check passwords against
a database of compromised or frequently used passwords.

### Security Impact

Attackers could attempt common passwords during
credential-stuffing or password-spraying attacks.

This weakness becomes more significant when combined
with F2's lack of per-account throttling.

### Recommendations

Implement breached-password detection.

Possible approaches include:

- Have I Been Pwned Pwned Passwords API
- A locally maintained list of compromised passwords
- Password strength estimation using zxcvbn

The same validation should apply when creating
administrator accounts.

### Current Assessment

Password hashing is secure, but password selection
could be strengthened.

---

## F4 — Authentication Logging and Sensitive Data Exposure

**Severity:** Low–Medium

**Status:** VERIFIED — IMPROVEMENTS RECOMMENDED

### Description

The application logs failed authentication attempts.

The submitted username may appear in application logs.

Example:

```text
WARNING: Failed login for username='MySecretPass99'
```

### Security Concern

Users sometimes accidentally enter passwords into
username fields.

If the application logs the submitted username,
a mistakenly entered password could appear in plaintext
in server logs.

Application logs may be accessible to developers,
administrators, or monitoring systems.

### Additional Weakness

The security audit trail does not comprehensively record
all important security events.

Examples include:

- Successful login
- Logout
- Authorization failures
- Administrator access
- Privileged account creation

### Recommendations

- Avoid logging raw untrusted authentication input.
- Redact potentially sensitive values.
- Add structured authentication events.
- Record authorization failures.
- Monitor repeated suspicious activity.
- Restrict access to application logs.

### Current Assessment

The application avoids exposing internal errors to users.

However, security logging should be improved for
production monitoring and incident investigation.

---

## F5 — Username Enumeration Through Registration

**Severity:** Low

**Status:** VERIFIED — ACCEPTED DESIGN TRADE-OFF

### Description

The login endpoint returns a generic error message:

```text
Invalid username or password.
```

This reduces the ability to determine whether
a username exists through login responses.

However, registration returns a specific error
when a username is already registered.

Example:

```text
That username is already taken.
```

### Security Impact

An attacker could attempt registration using
different usernames to identify existing accounts.

The registration rate limiter reduces the number
of attempts from a single IP address.

However, distributed requests could still be used.

### Recommendations

- Apply stricter registration throttling.
- Consider CAPTCHA after suspicious activity.
- Use email verification for production accounts.
- Ensure login errors remain generic.
- Strengthen protections against password spraying.

### Current Assessment

The behavior is an accepted usability trade-off
for this demonstration application.

It should be reconsidered for applications with
higher privacy requirements.

---

## F6 — Sliding Session Lifetime Without Absolute Expiration

**Severity:** Low

**Status:** VERIFIED BY CONFIGURATION — NOT FIXED

### Description

The application uses a session inactivity timeout.

The configured session lifetime is approximately:

```text
30 minutes
```

With sliding session expiration enabled,
activity can extend the session lifetime.

### Security Concern

A stolen session that remains continuously active
could avoid expiration based solely on inactivity.

The application does not currently enforce
an independent absolute session lifetime.

### Recommendations

- Record the original authentication time.
- Enforce an absolute session lifetime.
- Require reauthentication for sensitive actions.
- Support revocation of all active user sessions.
- Invalidate sessions after password changes.

An example production policy could use:

```text
Inactivity timeout: 30 minutes
Absolute session lifetime: 8 hours
```

The appropriate values depend on application risk.

### Current Assessment

The inactivity timeout provides a basic session
security control.

An absolute expiration policy is recommended
for production use.

---

## F7 — Argon2 Resource Consumption

**Severity:** Low–Medium

**Status:** ANALYSIS — IMPROVEMENTS RECOMMENDED

### Description

SecureAccess uses Argon2id for password hashing.

The configured hashing parameters include:

```text
Time cost: 3
Memory cost: 64 MiB
Parallelism: 4
```

Argon2id intentionally requires computational resources.

This makes offline password cracking more expensive.

However, password verification also consumes server resources.

### Security Concern

Many concurrent login requests could consume
significant memory and CPU resources.

The application also performs dummy password verification
for nonexistent usernames to reduce timing-based enumeration.

This means even invalid usernames can trigger
expensive hashing operations.

### Potential Impact

An attacker distributing authentication requests
across multiple IP addresses could attempt to
exhaust available server resources.

### Recommendations

- Limit concurrent password hashing operations.
- Add global authentication request limits.
- Monitor memory and CPU usage.
- Configure appropriate worker limits.
- Tune Argon2 parameters for deployment hardware.

### Current Assessment

Argon2id is an appropriate password hashing algorithm.

Production deployment should account for its
intentional computational cost.

---

## F8 — Production Deployment Security Requirements

**Category:** Production Hardening

**Status:** NOT FULLY VERIFIED

The application currently runs as a local demonstration.

Additional security controls are required before
a public production deployment.

| Security Area                | Current Development Setup           | Production Recommendation          |
| ---------------------------- | ----------------------------------- | ---------------------------------- |
| Transport                    | Local HTTP                          | HTTPS with TLS                     |
| Session cookies              | Secure flag disabled for local HTTP | Enable Secure flag                 |
| Cookie name                  | secureaccess_session                | Consider \_\_Host- prefix          |
| Web server                   | Flask development server            | Production WSGI server             |
| Debug mode                   | Disabled                            | Keep disabled                      |
| Secret key                   | Local .env                          | Managed secret storage             |
| Database                     | Local SQLite                        | Managed database where appropriate |
| Administrator authentication | Password authentication             | Add MFA                            |
| Rate limiting                | In-memory storage                   | Shared Redis storage               |
| Reverse proxy                | Local development                   | Configure trusted proxy headers    |
| Dependencies                 | Pinned versions                     | Regular security updates           |
| Monitoring                   | Basic application logs              | Centralized security monitoring    |
| Backups                      | Local development                   | Secure database backups            |

### HTTPS Configuration

For HTTPS deployments, configure:

```env
SESSION_COOKIE_SECURE=1
FLASK_DEBUG=0
```

The session cookie should only be transmitted
over encrypted connections.

### Secret Management

The application's secret key must never be committed
to GitHub.

The `.env` file must remain excluded through `.gitignore`.

Example:

```gitignore
.env
.venv/
instance/
```

Secrets should be generated using a cryptographically
secure random generator.

Example:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Current Assessment

SecureAccess is appropriate for local demonstration
and educational security testing.

Production deployment requires additional configuration,
monitoring, and infrastructure hardening.

---

# 4. Security Testing and Verification

## Automated Testing

The application uses pytest.

Tests cover authentication, authorization,
input validation, and session management.

The complete test suite was executed using:

```bash
python -m pytest -q
```

### Results

```text
37 passed, 1408 warnings in 2.39s
```

| Test Metric           | Result |
| --------------------- | ------ |
| Total automated tests | 37     |
| Passed                | 37     |
| Failed                | 0      |
| Warnings              | 1408   |
| Overall result        | PASS   |

The warnings originated from deprecated
datetime usage in the installed Flask-Session
SQLAlchemy implementation.

These warnings did not cause test failures.

However, dependency warnings should be reviewed
and addressed during maintenance.

---

## Authentication Tests

| Test                                   | Expected Result                | Status |
| -------------------------------------- | ------------------------------ | ------ |
| Register valid user                    | Account created                | PASS   |
| Login with valid credentials           | Authentication succeeds        | PASS   |
| Login with invalid credentials         | Generic error                  | PASS   |
| Login with unknown username            | Generic error                  | PASS   |
| Logout                                 | Session invalidated            | PASS   |
| Access protected page while logged out | 401 Unauthorized               | PASS   |
| Session fixation protection            | Session identifier regenerated | PASS   |
| CSRF validation                        | Invalid request rejected       | PASS   |

---

## Authorization Tests

| Test                                       | Expected Result       | Status |
| ------------------------------------------ | --------------------- | ------ |
| Standard User opens dashboard              | 200 OK                | PASS   |
| Standard User opens Admin dashboard        | 403 Forbidden         | PASS   |
| Admin opens User dashboard                 | 200 OK                | PASS   |
| Admin opens Admin dashboard                | 200 OK                | PASS   |
| Logged-out visitor opens Admin dashboard   | 401 Unauthorized      | PASS   |
| User attempts unauthorized role assignment | Rejected or ignored   | PASS   |
| Administrator role changes                 | Current role enforced | PASS   |

---

## Input Validation Tests

| Test                        | Expected Result                | Status |
| --------------------------- | ------------------------------ | ------ |
| Empty username              | Rejected                       | PASS   |
| Empty password              | Rejected                       | PASS   |
| Short password              | Rejected                       | PASS   |
| Excessively long username   | Rejected                       | PASS   |
| Invalid username characters | Rejected                       | PASS   |
| SQL injection attempt       | Does not bypass authentication | PASS   |
| Malformed JSON              | Rejected                       | PASS   |
| Unknown API route           | 404 response                   | PASS   |

---

## Session Regression Testing

### Test File

```text
tests/test_session_regression.py
```

### Purpose

Verify that creating more than 1,000 additional
sessions does not invalidate an existing session.

### Procedure

1. Create the original session.
2. Store a session marker.
3. Generate 1,100 additional sessions.
4. Reopen the original session.
5. Verify the original marker remains.

### Result

```text
PASS
```

### Conclusion

The corrected SQLite-backed session implementation
successfully preserved the original session.

The original file-cache eviction vulnerability
was addressed.

---

# 5. Browser-Based QA Verification

Manual browser testing was performed using
Google Chrome and Chrome DevTools.

## Standard User Access

A standard account was created and authenticated.

The User dashboard displayed:

```text
Username: testuser
Role: User
```

The user successfully accessed:

```text
/dashboard
```

Expected result:

```text
HTTP 200 OK
```

### Result

PASS

---

## Unauthorized Administrator Access

While authenticated as a standard User,
the following endpoint was requested:

```text
/admin
```

The application displayed:

```text
403

You do not have permission to access this page.
```

Chrome DevTools confirmed:

```text
Request Method: GET
Status Code: 403 FORBIDDEN
```

### Result

PASS

This confirms that administrator authorization
is enforced by the backend rather than only
by hiding frontend navigation elements.

---

## Unauthenticated Access

After logging out, the administrator endpoint
was requested again.

The application displayed:

```text
401

You must log in to access this page.
```

Chrome DevTools confirmed:

```text
Request Method: GET
Status Code: 401 UNAUTHORIZED
```

### Result

PASS

---

## Administrator Access

The administrator account was authenticated.

The application displayed:

```text
Username: admin
Role: Admin
```

The administrator successfully accessed:

```text
/dashboard
```

And:

```text
/admin
```

Chrome DevTools confirmed:

```text
Request Method: GET
Status Code: 200 OK
```

### Result

PASS

---

## Responsive Interface Testing

The application was tested using
Chrome DevTools responsive device mode.

A viewport width of approximately 400 pixels
was used.

The following pages were inspected:

- User dashboard
- Administrator dashboard
- 401 error page
- 403 error page

The interface remained usable at the tested
mobile viewport size.

The administrator table required horizontal
scrolling because of its multiple columns.

### Result

PASS WITH MINOR USABILITY LIMITATION

---

# 6. Security Controls Verification Matrix

| Security Control               | Implemented  | Verified              | Notes                                        |
| ------------------------------ | ------------ | --------------------- | -------------------------------------------- |
| Argon2id password hashing      | Yes          | Automated             | Hashing tests passed                         |
| No plaintext password storage  | Yes          | Automated             | Manual database inspection still recommended |
| Generic login errors           | Yes          | Automated             | Prevents direct login enumeration            |
| Server-side sessions           | Yes          | Automated             | SQLite-backed                                |
| Session regeneration           | Yes          | Automated             | Session fixation protection                  |
| Session logout invalidation    | Yes          | Automated             | Server-side session removal                  |
| HttpOnly cookies               | Yes          | Automated             | Cookie protection                            |
| SameSite cookies               | Yes          | Automated             | Cross-site request protection                |
| Secure cookies over HTTPS      | Configurable | Not deployed          | Requires HTTPS                               |
| CSRF protection                | Yes          | Automated             | POST requests protected                      |
| User dashboard protection      | Yes          | Automated and browser | 401 when logged out                          |
| Admin authorization            | Yes          | Automated and browser | 403 for User                                 |
| Role revalidation              | Yes          | Automated             | Database role checked                        |
| Parameterized SQL              | Yes          | Automated             | Injection tests passed                       |
| Input validation               | Yes          | Automated             | Invalid requests rejected                    |
| Security headers               | Yes          | Automated             | CSP and related headers                      |
| Debug disabled                 | Yes          | Automated             | Default configuration                        |
| Login rate limiting            | Yes          | Automated             | 429 verified                                 |
| Cache-Control no-store         | Yes          | Automated             | Prevents sensitive caching                   |
| Session flood protection       | Yes          | Regression test       | F1 fixed                                     |
| Breached password detection    | No           | No                    | F3 remains                                   |
| Per-account throttling         | No           | No                    | F2 remains                                   |
| Comprehensive security logging | Partial      | Partial               | F4 remains                                   |
| Absolute session expiration    | No           | No                    | F6 remains                                   |
| Administrator MFA              | No           | No                    | Production improvement                       |

---

# 7. AI-Generated Code Review

## AI Tools Used

The project was developed with AI assistance.

AI tools assisted with:

- Application architecture
- Flask authentication implementation
- Password hashing
- Session management
- Role-based authorization
- Input validation
- Automated test generation
- Security review
- Documentation

The exact AI prompts are documented separately in:

```text
docs/AI_PROMPTS.md
```

## What AI Generated Correctly

The generated application included several
appropriate security controls.

Examples:

1. Argon2id password hashing
2. Generic login errors
3. Server-side authorization
4. CSRF protection
5. Parameterized SQL queries
6. Secure session cookie settings
7. Input validation
8. Rate limiting
9. Security response headers

These controls were reviewed and tested.

## What AI Generated Incorrectly

The original session storage configuration
used a file-based cache with a threshold
of 1,000 entries.

The configuration created an availability
weakness under repeated anonymous requests.

The weakness was not detected by the
original functional test suite.

## Manual Security Correction

The application was modified to use
SQLite-backed session storage.

A dedicated regression test was added
to verify that legitimate sessions remain
available after 1,100 additional sessions
are created.

The corrected implementation passed
the complete automated test suite.

## Key Lesson

AI-generated code can contain vulnerabilities
even when it appears functional.

Developers must independently verify:

- Authentication behavior
- Authorization boundaries
- Session security
- Password storage
- Input validation
- Error handling
- Resource exhaustion risks

AI should assist the development process,
not replace security engineering judgment.

---

# 8. Video Demonstration Plan

The assignment requires a 5–7 minute
video demonstrating the application
and its security testing.

The recording will be completed separately.

## 0:00–1:30 — Architecture and Security Audit

Demonstrate:

- Project architecture
- Flask backend
- SQLite database
- Argon2id password hashing
- Session-based authentication
- Role-based authorization
- Original F1 vulnerability
- SQLite session storage correction

Explain that the original AI-generated
session configuration could evict valid sessions.

## 1:30–3:30 — Functional Demonstration

Demonstrate:

1. Register a standard User.
2. Log in.
3. Access the User dashboard.
4. Log out.
5. Log in as Admin.
6. Access the Admin dashboard.

## 3:30–5:30 — Security Testing

Open Chrome DevTools.

Demonstrate:

- HTTP 200 for authorized access
- HTTP 401 for unauthenticated access
- HTTP 403 for unauthorized Admin access
- Generic invalid-login error
- Password hashes stored in SQLite
- Passing automated tests

Run:

```bash
python -m pytest -q
```

Show:

```text
37 passed
```

Explain the F1 regression test.

## 5:30–6:30 — Conclusion

Summarize:

- AI-generated code requires auditing.
- Authentication and authorization are different.
- Authorization must be enforced on the server.
- Secure password storage is essential.
- Functional tests alone cannot guarantee security.
- Security regression tests help prevent vulnerabilities
  from returning.

---

# 9. Final Security Assessment

## Completed Improvements

The SecureAccess project successfully implemented:

- User registration
- User login
- User logout
- Administrator authentication
- Server-side RBAC
- Argon2id password hashing
- SQLite-backed server-side sessions
- CSRF protection
- Input validation
- Parameterized SQL queries
- Rate limiting
- Generic error handling
- Security headers
- Automated regression testing

## Confirmed Results

```text
Automated tests: 37 PASSED

Failed tests: 0

F1 session vulnerability: FIXED

User dashboard: ACCESSIBLE TO AUTHENTICATED USERS

Admin dashboard: ACCESSIBLE TO ADMIN ONLY

Unauthorized User access: 403 FORBIDDEN

Unauthenticated access: 401 UNAUTHORIZED

Admin access: 200 OK
```

## Remaining Improvements

The following improvements are recommended
before production deployment:

1. Per-account authentication throttling
2. Breached-password detection
3. Improved security event logging
4. Absolute session expiration
5. Global request rate limiting
6. Administrator multifactor authentication
7. Production HTTPS configuration
8. Centralized monitoring and database backups

## Final Conclusion

SecureAccess demonstrates authentication
and role-based authorization using
modern security practices.

The project also demonstrates why
AI-generated security code must be
reviewed and tested independently.

A real session availability vulnerability
was identified in the original implementation.

The issue was corrected by replacing
the file-based session cache with
SQLite-backed session storage.

The correction was verified using
a dedicated regression test.

All 37 automated tests passed.

The project is suitable for demonstrating
authentication, authorization, and
security quality assurance in an
educational environment.

It should not be considered
production-ready without additional
security hardening and deployment testing.

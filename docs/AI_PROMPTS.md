# SecureAccess: AI Prompt Log and Critical Evaluation

**Project:** SecureAccess — Authentication and Role-Based Access Control  
**Technologies:** Python, Flask, SQLite, HTML, CSS, JavaScript  
**AI Tools:** Claude Code and ChatGPT  
**Testing Framework:** pytest  
**Documentation Updated:** October 27, 2026

---

## 1. Purpose

This document records how AI tools were used to design, implement, test,
audit, and document the SecureAccess application.

The assignment requires:

1. Recording the AI prompts used during development.
2. Summarizing the AI-generated responses.
3. Critically evaluating the generated code.
4. Identifying security weaknesses.
5. Implementing and testing a security correction.
6. Reflecting on the reliability and limitations of AI-generated software.

AI tools assisted with application architecture, authentication,
authorization, security testing, and documentation.

However, all AI-generated security code required independent review.

The original application passed 36 automated tests.

After correcting security finding F1 and adding a regression test,
the application passed 37 automated tests.

---

# 2. AI Prompt History

## Prompt 1 — Initial Application Architecture and Development

**AI Tool:** Claude Code  
**Date:** Initial project development  
**Prompt Type:** Initial application generation

### Original Prompt (Verbatim)

```text
Act as a senior software engineer. Build a lightweight full-stack authentication and role-based authorization application named SecureAccess using Python Flask, SQLite, HTML, CSS, and JavaScript.

Requirements:
1. Registration and login for users with User and Admin roles.
2. Secure password hashing.
3. Session-based authentication and logout.
4. Public home page, authenticated user dashboard, and Admin-only dashboard.
5. Server-side route guards and role checks.
6. SQLite database to store users.
7. Basic input validation and error handling.
8. Minimal interface for testing all functionality.

Provide all project files, required dependencies, and local setup instructions. Explain your security choices. Public registration must create only standard User accounts; Admin accounts must be provisioned separately.
```

### Summary of AI Response

Claude Code proposed a Flask application architecture that included:

- Flask application factory
- Authentication blueprint
- Main application blueprint
- SQLite database
- Argon2id password hashing
- Flask-Session for server-side sessions
- Flask-WTF for CSRF protection
- Flask-Limiter for login rate limiting
- Server-side role-based authorization
- User and Admin dashboards
- Administrator account creation through a CLI command
- Automated tests using pytest

The AI also explained its security decisions.

One important design choice was using server-side sessions instead
of Flask's default client-side signed sessions.

This allowed the application to invalidate authentication sessions
during logout.

The AI provided a proposed project structure, dependencies,
and setup instructions.

### My Evaluation

The proposed architecture addressed the main assignment requirements.

I specifically requested that public registration create only
standard User accounts.

The generated application followed this requirement by assigning
the User role during registration and restricting administrator
creation to a separate CLI command.

I also requested server-side route guards and role checks.

These were implemented in the Flask backend.

The architecture included appropriate security controls such as:

1. Secure password hashing.
2. Server-side session management.
3. CSRF protection.
4. Parameterized database queries.
5. Input validation.
6. Login rate limiting.
7. Backend authorization.

However, the initial architecture was not sufficient evidence
that the application was secure.

The session storage configuration required additional review.

---

## Prompt 2 — Generate the Application

**AI Tool:** Claude Code  
**Prompt Type:** Continue implementation

### Original Prompt (Verbatim)

```text
Continue
```

### Summary of AI Response

Claude Code generated the initial SecureAccess application.

The generated project included:

- User registration
- User login
- User logout
- Public home page
- User dashboard
- Administrator dashboard
- Role-based authorization
- Argon2id password hashing
- SQLite database integration
- Server-side sessions
- CSRF protection
- Authentication rate limiting
- HTML templates
- CSS styling
- JavaScript functionality
- Administrator CLI command
- Automated pytest tests

The original test suite contained 36 passing tests.

The AI also reviewed the application for security weaknesses.

During the audit, it identified a denial-of-service vulnerability
in the original session storage implementation.

The AI documented the vulnerability and proposed a correction.

The correction was left unapplied so that I could implement
and demonstrate the security improvement myself.

### My Evaluation

The generated application successfully implemented the main
authentication and authorization features.

However, passing the original 36 tests did not prove
that the application was secure.

The original file-based session storage used a cache
with a maximum threshold of 1,000 entries.

Repeated anonymous requests could cause legitimate
authenticated sessions to be evicted.

This was a significant availability vulnerability.

I learned that functional testing and security testing
serve different purposes.

Functional tests verify expected application behavior.

Security testing also investigates how the application
behaves under malicious or unexpected conditions.

---

## Prompt 3 — Security Vulnerability Remediation

**AI Tool:** ChatGPT  
**Date:** October 27, 2026  
**Task:** Fix security finding F1

### Prompt Record

The F1 correction was completed through a series of
step-by-step requests in ChatGPT.

The exact original wording of those requests has not
been reconstructed in this document.

For a complete verbatim prompt log, the original
conversation should be consulted.

### Summary of AI Response

ChatGPT provided guidance for replacing the
file-based session cache with SQLite-backed
server-side session storage.

The correction involved installing:

```bash
python -m pip install Flask-SQLAlchemy==3.1.1
```

The dependency was added to:

```text
requirements.txt
```

The session configuration was changed to:

```python
SESSION_TYPE = "sqlalchemy"
SESSION_CLEANUP_N_REQUESTS = 100
```

A dedicated SQLite database was configured for sessions:

```text
instance/sessions.db
```

The original file-cache configuration was removed.

The application continued to use:

- CSRF protection
- Authentication rate limiting
- Secure password hashing
- Server-side authorization
- Generic error handling

### My Evaluation

I followed the implementation instructions and
updated the application files.

I verified the active session configuration.

The application reported:

```text
Session type: sqlalchemy
```

I also confirmed that the dedicated SQLite
session database existed.

This correction removed the original
1,000-entry file-cache eviction threshold.

However, SQLite-backed sessions still require
storage monitoring and expired-session cleanup.

The correction addressed the identified
session eviction problem but did not eliminate
every possible denial-of-service risk.

---

## Prompt 4 — Create and Run a Regression Test

**AI Tool:** ChatGPT  
**Date:** October 27, 2026  
**Task:** Verify the F1 security correction

### Prompt Record

I used ChatGPT for step-by-step assistance
creating and executing a session regression test.

The exact wording of the individual requests
should be copied from the original conversation
if a complete verbatim transcript is required.

### Summary of AI Response

ChatGPT provided a regression test to verify
that the original session remained available
after creating more than 1,000 additional sessions.

The test was saved in:

```text
tests/test_session_regression.py
```

The regression test:

1. Created a Flask application.
2. Created an original session.
3. Stored a marker in the original session.
4. Created 1,100 additional sessions.
5. Reopened the original session.
6. Verified that the original marker remained.

### My Evaluation

I added the regression test to the project.

I executed the complete automated test suite using:

```bash
python -m pytest -q
```

The results were:

```text
37 passed, 1408 warnings in 2.39s
```

**Passed:** 37  
**Failed:** 0

The regression test passed.

This provided evidence that the original
session was not evicted after the creation
of 1,100 additional sessions.

However, the test does not prove that the
application can withstand every possible
resource exhaustion attack.

A live post-fix session flood test would
provide additional verification.

---

## Prompt 5 — Security Audit Documentation

**AI Tool:** ChatGPT  
**Task:** Update the security audit

### Original Request

I requested a complete corrected version of
the existing security audit document that I
could copy and paste into VS Code.

### Summary of AI Response

ChatGPT assisted with updating:

```text
docs/SECURITY_AUDIT.md
```

The updated document included:

- Application architecture
- Security controls
- Security findings F1–F8
- Original F1 vulnerability
- F1 remediation
- Regression test results
- Remaining security risks
- Production hardening recommendations
- Final security assessment

### My Evaluation

I reviewed the updated documentation to ensure
that it reflected the changes made to the application.

The document distinguishes between the corrected
F1 vulnerability and the remaining findings
that require additional security improvements.

The security audit also explains why passing
automated tests does not guarantee complete security.

---

## Prompt 6 — QA Checklist Documentation

**AI Tool:** ChatGPT  
**Task:** Update QA testing documentation

### Original Request

I provided the existing QA checklist and
requested a complete updated version that
could be copied directly into VS Code.

### Summary of AI Response

ChatGPT assisted with updating:

```text
docs/QA_CHECKLIST.md
```

The updated checklist documented:

- Automated test results
- Authentication testing
- Authorization testing
- Input validation
- SQL injection-like input testing
- Browser status code verification
- Session security testing
- F1 regression testing
- Remaining manual verification items

### My Evaluation

I reviewed the checklist to ensure that
test results were accurately documented.

The checklist distinguishes between:

- Confirmed manual tests
- Automated test results
- Reported test results
- Pending verification

This is important because AI-generated
documentation can overstate testing results.

A security test should only be marked
as verified when there is supporting evidence.

---

# 3. Security Finding F1

## Vulnerability

The original application used Flask-Session
with a file-based cache.

The cache was configured with:

```python
FileSystemCache(
    cache_dir,
    threshold=1000,
    mode=0o600
)
```

Anonymous requests could create server-side
sessions without authentication.

When enough sessions accumulated,
legitimate sessions could be evicted.

This caused an availability weakness.

## Original Vulnerability Evidence

The security audit documented:

```text
Victim /dashboard before flood: 200
Sending 1100 anonymous requests...
Victim /dashboard after flood: 401
VULNERABLE: victim was logged out.
```

The original 36 automated tests passed
despite the vulnerability.

## Correction

The application was updated to use
SQLite-backed server-side sessions.

The updated configuration uses:

```python
SESSION_TYPE = "sqlalchemy"
SESSION_CLEANUP_N_REQUESTS = 100
```

The session database is stored at:

```text
instance/sessions.db
```

## Regression Test

A regression test was added:

```text
tests/test_session_regression.py
```

The test created an original session,
then generated 1,100 additional sessions.

It confirmed that the original session
remained available.

## Test Results

```text
37 passed, 1408 warnings in 2.39s
```

**Result: PASS**

## Remaining Risks

The fix addresses the original session
eviction vulnerability.

However, additional protections are
recommended for production:

- Global rate limiting
- Database storage monitoring
- Reverse-proxy request limits
- Expired-session cleanup
- Infrastructure resource limits

---

# 4. Critical Evaluation of AI-Generated Code

## 4.1 What Did AI Generate Correctly?

AI successfully assisted with implementing:

- Secure user registration
- User authentication
- Administrator authentication
- Argon2id password hashing
- Server-side sessions
- Role-based authorization
- CSRF protection
- Input validation
- Parameterized SQL queries
- Authentication rate limiting
- Security response headers
- Automated testing

The application successfully enforced
different access levels.

A standard User could access:

```text
/dashboard
```

But could not access:

```text
/admin
```

Chrome DevTools confirmed:

```text
403 FORBIDDEN
```

An unauthenticated visitor received:

```text
401 UNAUTHORIZED
```

An authenticated Admin could access:

```text
/admin
```

Chrome DevTools confirmed:

```text
200 OK
```

These results demonstrate that authorization
checks were implemented on the server.

---

## 4.2 What Was Wrong or Incomplete?

The original session storage implementation
contained a denial-of-service vulnerability.

The file-based cache could evict legitimate
sessions after enough anonymous sessions
were created.

The original automated test suite did
not detect this vulnerability.

Additional security limitations remain:

- No per-account authentication throttling
- No breached-password blocklist
- Limited security event logging
- No absolute session timeout
- No administrator multifactor authentication
- No production HTTPS deployment verification

These limitations demonstrate that
AI-generated code requires additional review.

---

## 4.3 What Did I Change?

I implemented the F1 security correction.

The changes included:

1. Installing Flask-SQLAlchemy.
2. Updating the session configuration.
3. Replacing file-based session storage.
4. Creating a dedicated SQLite session database.
5. Adding a regression test.
6. Running the complete test suite.
7. Updating the security audit.
8. Updating the QA checklist.

The correction was completed successfully.

---

## 4.4 How Did I Verify the Correction?

I used several verification methods.

### Configuration Verification

The application reported:

```text
Session type: sqlalchemy
```

### Database Verification

The session database was created:

```text
instance/sessions.db
```

### Regression Testing

The regression test created 1,100 additional
sessions and confirmed that the original
session remained available.

### Automated Testing

The complete test suite returned:

```text
37 passed
```

### Browser Testing

Authentication and authorization
continued to work correctly.

The application returned:

- HTTP 200 for authorized access
- HTTP 401 for unauthenticated access
- HTTP 403 for unauthorized Admin access

---

# 5. What I Would Test Further

Although the application passed its
automated tests, additional verification
would be required before production deployment.

Recommended testing includes:

1. HTTPS deployment testing.
2. Secure cookie verification.
3. Distributed rate-limit testing.
4. Resource exhaustion testing.
5. Session expiration testing.
6. Security logging review.
7. Dependency vulnerability scanning.
8. Administrator MFA testing.
9. Live post-fix session flood testing.
10. Database backup and recovery testing.

I would also investigate dependency
deprecation warnings.

These warnings did not cause the
current tests to fail, but they
should be addressed during maintenance.

---

# 6. Final Reflection

AI tools significantly accelerated
the development of SecureAccess.

Claude Code helped design and generate
the initial application.

ChatGPT assisted with security remediation,
regression testing, and documentation.

The AI-generated application included
several appropriate security controls.

However, the original implementation
also contained a session availability
vulnerability.

This weakness was identified during
security auditing.

I implemented a correction using
SQLite-backed session storage.

A dedicated regression test verified
that the original session remained
available after creating 1,100
additional sessions.

The updated application passed
all 37 automated tests.

The most important lesson from this
assignment is that AI-generated code
must be reviewed and tested independently.

AI can assist developers with architecture,
implementation, testing, and documentation,
but developers remain responsible for
security, correctness, and verification.

---

# 7. Final Project Status

| Requirement                 | Status    |
| --------------------------- | --------- |
| User registration           | Completed |
| User login                  | Completed |
| User logout                 | Completed |
| Secure password hashing     | Completed |
| User dashboard              | Completed |
| Admin dashboard             | Completed |
| Server-side RBAC            | Completed |
| SQLite database             | Completed |
| CSRF protection             | Completed |
| Input validation            | Completed |
| Login rate limiting         | Completed |
| Security audit              | Completed |
| F1 vulnerability correction | Completed |
| F1 regression test          | Passed    |
| Automated testing           | 37 passed |
| QA checklist                | Updated   |
| AI prompt log               | Updated   |
| GitHub submission           | Pending   |
| Video demonstration         | Pending   |

**Overall Result:** SecureAccess meets the core educational
authentication and authorization requirements, with
additional production hardening recommended.

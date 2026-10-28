# SecureAccess: QA Checklist

**Project:** SecureAccess — Authentication and Role-Based Access Control  
**Testing Date:** October 27, 2026  
**Testing Tools:** pytest, Google Chrome, Chrome DevTools  
**Environment:** Local Flask development server  
**Automated Tests:** 37 passed, 0 failed

## Test Result Legend

- **PASS:** Test completed successfully.
- **PASS (Automated):** Verified by automated testing.
- **REPORTED PASS:** Manually tested and reported successful.
- **PENDING:** Additional manual verification needed.
- **N/A:** Not applicable to local development.

---

## A. Automated Tests

| ID  | Test                  | Expected Result                                     | Actual Result | Status |
| --- | --------------------- | --------------------------------------------------- | ------------- | ------ |
| A1  | Full pytest suite     | All tests pass                                      | 37 passed     | PASS   |
| A2  | Authentication tests  | Valid and invalid login handled                     | Tests passed  | PASS   |
| A3  | Authorization tests   | Role permissions enforced                           | Tests passed  | PASS   |
| A4  | CSRF protection       | Invalid requests rejected                           | Tests passed  | PASS   |
| A5  | Rate limiting         | Excessive login attempts rejected                   | Tests passed  | PASS   |
| A6  | Input validation      | Invalid input rejected                              | Tests passed  | PASS   |
| A7  | F1 session regression | Original session survives 1,100 additional sessions | Test passed   | PASS   |

### Test Command

```bash
python -m pytest -q
```

### Test Results

```text
37 passed, 1408 warnings in 2.39s
```

**Total Tests:** 37  
**Passed:** 37  
**Failed:** 0

The warnings were primarily caused by deprecated datetime functionality in Flask-Session. They did not cause test failures.

---

## B. Authentication

| ID  | Test                       | Expected Result                   | Status           |
| --- | -------------------------- | --------------------------------- | ---------------- |
| B1  | Successful registration    | New User account created          | PASS             |
| B2  | Duplicate username         | HTTP 409                          | PENDING          |
| B3  | Successful login           | Dashboard accessible              | PASS             |
| B4  | Invalid password           | Generic authentication error      | REPORTED PASS    |
| B5  | Unknown username           | Generic authentication error      | PASS (Automated) |
| B6  | Successful logout          | Session invalidated               | REPORTED PASS    |
| B7  | Back button after logout   | Protected dashboard not displayed | PENDING          |
| B8  | Session fixation defense   | Session ID changes after login    | PASS (Automated) |
| B9  | Stolen cookie after logout | Old session rejected              | PASS (Automated) |
| B10 | Login rate limiting        | HTTP 429 after excessive attempts | PASS (Automated) |

### Registration Test

A standard user account was registered successfully.

```text
Username: testuser
Role: User
Result: PASS
```

### Login Test

The registered user logged in successfully.

```text
Username: testuser
Role: User
Dashboard: Accessible
Result: PASS
```

### Invalid Password Test

An incorrect password was submitted.

The application rejected the login attempt.

```text
Result: REPORTED PASS
```

The exact HTTP response should be confirmed in Chrome DevTools during the final demonstration.

---

## C. Authorization (RBAC)

| ID  | Test                               | Expected Result           | Status             |
| --- | ---------------------------------- | ------------------------- | ------------------ |
| C1  | Logged-out visitor → `/dashboard`  | HTTP 401                  | PENDING            |
| C2  | Logged-out visitor → `/admin`      | HTTP 401                  | PASS               |
| C3  | User → `/dashboard`                | HTTP 200                  | PASS               |
| C4  | User → `/admin`                    | HTTP 403                  | PASS               |
| C5  | User → `/api/admin/users`          | HTTP 403                  | PASS (Automated)   |
| C6  | Admin → `/dashboard`               | HTTP 200                  | PASS               |
| C7  | Admin → `/admin`                   | HTTP 200                  | PASS               |
| C8  | Role injection during registration | Account remains User      | PASS (Automated)   |
| C9  | No public Admin registration       | Admin creation restricted | PASS (Code Review) |
| C10 | Admin API excludes password hashes | Sensitive data omitted    | PASS (Automated)   |

### Standard User Authorization

Logged in as:

```text
Username: testuser
Role: User
```

Requested:

```text
GET /admin
```

Chrome DevTools confirmed:

```text
Status Code: 403 FORBIDDEN
```

**Result: PASS**

### Unauthenticated Access

After logging out, the Admin endpoint was requested.

```text
GET /admin
Status Code: 401 UNAUTHORIZED
```

**Result: PASS**

### Administrator Access

Logged in as:

```text
Username: admin
Role: Admin
```

The administrator accessed:

```text
GET /dashboard
GET /admin
```

Both endpoints returned:

```text
Status Code: 200 OK
```

**Result: PASS**

### Authorization Summary

| Account State | Endpoint     | Expected | Result  |
| ------------- | ------------ | -------- | ------- |
| User          | `/dashboard` | 200      | PASS    |
| User          | `/admin`     | 403      | PASS    |
| Admin         | `/dashboard` | 200      | PASS    |
| Admin         | `/admin`     | 200      | PASS    |
| Logged out    | `/admin`     | 401      | PASS    |
| Logged out    | `/dashboard` | 401      | PENDING |

---

## D. Input Validation

| ID  | Test                                  | Expected Result         | Status           |
| --- | ------------------------------------- | ----------------------- | ---------------- |
| D1  | Empty username                        | Validation error        | REPORTED PASS    |
| D2  | Empty password                        | Validation error        | REPORTED PASS    |
| D3  | Short password                        | Rejected                | PASS (Automated) |
| D4  | Invalid username characters           | Rejected                | PASS (Automated) |
| D5  | Special characters in password        | Handled correctly       | PASS (Automated) |
| D6  | SQL injection-like login input        | Authentication rejected | REPORTED PASS    |
| D7  | SQL injection-like registration input | Rejected                | PASS (Automated) |
| D8  | Missing CSRF token                    | HTTP 400                | PASS (Automated) |
| D9  | Malformed JSON                        | HTTP 400                | PASS (Automated) |
| D10 | Oversized request                     | Rejected                | PASS (Automated) |

### Empty Input Test

Empty username and password submissions were tested.

The application rejected the invalid input.

**Result: REPORTED PASS**

### SQL Injection Test

The following username was submitted:

```text
' OR '1'='1
```

The application did not authenticate the request or crash.

**Result: REPORTED PASS**

The application uses parameterized SQL queries to prevent user input from being interpreted as SQL commands.

---

## E. Browser and Security Checks

| ID  | Test                      | Expected Result               | Status                       |
| --- | ------------------------- | ----------------------------- | ---------------------------- |
| E1  | Authorized Admin request  | HTTP 200                      | PASS                         |
| E2  | Unauthorized User request | HTTP 403                      | PASS                         |
| E3  | Unauthenticated request   | HTTP 401                      | PASS                         |
| E4  | Invalid password response | HTTP 401                      | PENDING NETWORK CONFIRMATION |
| E5  | No JavaScript exceptions  | No unhandled errors           | PENDING                      |
| E6  | HttpOnly session cookie   | JavaScript cannot read cookie | PASS (Automated)             |
| E7  | SameSite cookie           | SameSite=Lax                  | PASS (Automated)             |
| E8  | Secure cookie over HTTPS  | Secure enabled                | N/A — Local HTTP             |
| E9  | Security response headers | Required headers present      | PASS (Automated)             |
| E10 | Friendly 404 error        | No stack trace                | PASS (Automated)             |
| E11 | Responsive layout         | Usable on mobile viewport     | REPORTED PASS                |

### Browser Network Results

Chrome DevTools confirmed:

```text
200 OK
401 UNAUTHORIZED
403 FORBIDDEN
```

**Result: PASS**

### Browser Console

Expected HTTP errors may appear in Chrome DevTools when testing authorization failures.

For example:

```text
Failed to load resource: the server responded with a status of 403
```

These messages do not necessarily indicate JavaScript exceptions.

The final console review remains pending.

---

## F. Security Audit Finding F1

### F1 — Session Flood Denial-of-Service

**Severity:** High  
**Original Status:** Vulnerable  
**Current Status:** Fixed and regression-tested

### Original Vulnerability

The original application used Flask-Session with a file-based cache.

The cache had a threshold of 1,000 entries.

Anonymous requests could create additional sessions and cause legitimate sessions to be evicted.

The original security audit documented:

```text
Victim /dashboard before flood: 200
Sending 1100 anonymous requests...
Victim /dashboard after flood: 401
VULNERABLE: victim was logged out.
```

### Security Fix

The application was updated to use SQLite-backed sessions.

Changes implemented:

1. Installed Flask-SQLAlchemy 3.1.1.
2. Changed `SESSION_TYPE` to `sqlalchemy`.
3. Configured a dedicated SQLite session database.
4. Removed the file-cache threshold of 1,000.
5. Enabled periodic expired-session cleanup.
6. Added an automated regression test.

### Session Configuration

```python
SESSION_TYPE = "sqlalchemy"
SESSION_CLEANUP_N_REQUESTS = 100
```

Session database:

```text
instance/sessions.db
```

### Regression Test

Test file:

```text
tests/test_session_regression.py
```

The test:

1. Creates an original session.
2. Stores a session marker.
3. Creates 1,100 additional sessions.
4. Reopens the original session.
5. Confirms that the original session marker remains.

**Result: PASS**

### F1 Test Summary

| ID  | Test                         | Result                        | Status                     |
| --- | ---------------------------- | ----------------------------- | -------------------------- |
| F1a | Original file-cache flood    | Original session evicted      | VERIFIED IN ORIGINAL AUDIT |
| F1b | SQLite session configuration | SQLAlchemy active             | PASS                       |
| F1c | Session database creation    | `sessions.db` exists          | PASS                       |
| F1d | Session regression test      | Original session preserved    | PASS                       |
| F1e | Complete pytest suite        | 37 passed                     | PASS                       |
| F1f | Live flood after fix         | Session remains authenticated | PENDING                    |

### Remaining Risk

The correction prevents the original size-based session eviction.

However, large numbers of requests could still consume database storage.

Recommended production protections include:

- Global rate limiting
- Reverse-proxy request limits
- Database monitoring
- Expired-session cleanup
- Infrastructure resource limits

---

## G. Final QA Summary

| Category                         | Result                            |
| -------------------------------- | --------------------------------- |
| Authentication                   | PASS — some manual checks pending |
| Authorization                    | PASS                              |
| Input validation                 | PASS                              |
| SQL injection resistance         | PASS — tested scenarios           |
| CSRF protection                  | PASS (Automated)                  |
| Session security                 | PASS (Automated)                  |
| F1 regression test               | PASS                              |
| Browser HTTP status verification | PASS                              |
| Browser Console                  | PENDING                           |
| HTTPS deployment                 | NOT TESTED                        |
| Automated test suite             | 37 PASSED                         |

### Overall Result

**PASS WITH REMAINING MANUAL VERIFICATION ITEMS**

SecureAccess successfully demonstrates:

- Secure registration and login
- Argon2id password hashing
- Server-side session management
- Role-based access control
- Input validation
- CSRF protection
- SQL injection resistance
- Authentication rate limiting
- Security regression testing

The original F1 session vulnerability was corrected using SQLite-backed sessions.

All 37 automated tests passed.

The application is suitable for educational demonstration but requires additional hardening before production deployment.

---

## Sign-Off

| Field                  | Value                           |
| ---------------------- | ------------------------------- |
| Project                | SecureAccess                    |
| Testing date           | October 27, 2026                |
| Testing environment    | Local Flask development server  |
| Browser                | Google Chrome                   |
| Automated tests passed | 37                              |
| Automated tests failed | 0                               |
| F1 remediation         | Completed                       |
| Overall QA status      | PASS WITH PENDING MANUAL CHECKS |

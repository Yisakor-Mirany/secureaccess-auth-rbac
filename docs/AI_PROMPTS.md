# AI Prompt Log

Assignment requirement: document how AI was used, and critically evaluate
what it produced.

Paste each prompt **verbatim**, then summarize the response and your own
evaluation. Your evaluation should cover what you checked, what was wrong or
missing, and what you changed.

---

## Prompt 1: Architecture and plan

**Tool / model:** Claude Code
**Date:**

**Prompt (verbatim):**

```
<paste your full first prompt here>
```

**Summary of AI response:**

- Proposed a Flask app factory with auth and main blueprints, Flask-Session
  server-side sessions, Flask-WTF CSRF, Flask-Limiter, Argon2id, and SQLite with
  parameterized queries.
- Explained a key distinction: Flask's default session is a signed *client-side*
  cookie that logout can't revoke, so a server-side store was chosen.
- Gave the folder structure, dependency list and setup commands, then stopped
  for confirmation as instructed.

**My evaluation:**

---

## Prompt 2: "Continue" (generate the application)

**Prompt (verbatim):**

```
Continue
```

**Summary of AI response:**

- Generated the application, templates, CSS/JS, CLI admin command and 36 pytest tests.
- Ran the tests and drove the real UI with a headless browser.
- While auditing its own code, the AI found and reproduced a real
  denial-of-service weakness (F1: an anonymous request flood evicts logged-in
  sessions). It wrote a reproduction script, a validated fix, and a regression
  test, but **left the fix unapplied** so that I could demonstrate the
  correction myself.

**My evaluation:**

---

## Prompt 3:

**Prompt (verbatim):**

```

```

**Summary of AI response:**

**My evaluation:**

---

## Reflection

- Where was the AI's output correct, and how did you verify it?
- Where was it wrong, incomplete or overconfident?
- Which finding did you fix, and what evidence shows the fix works?
- What would you still not trust without further testing?

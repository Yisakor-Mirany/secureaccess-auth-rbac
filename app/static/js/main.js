// SecureAccess frontend. Plain JavaScript, no frameworks.
// Frontend validation is only for convenience - the server re-checks everything.
"use strict";

const USERNAME_RE = /^[A-Za-z0-9_.-]{3,30}$/;

function csrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute("content") : "";
}

// POST JSON with the CSRF token. Returns { ok, status, data }.
async function postJSON(url, body) {
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
      credentials: "same-origin",
      body: JSON.stringify(body || {}),
    });
    let data = {};
    try { data = await res.json(); } catch (_) { /* non-JSON response */ }
    return { ok: res.ok, status: res.status, data };
  } catch (_) {
    return { ok: false, status: 0, data: { error: "Network error. Is the server running?" } };
  }
}

// textContent (never innerHTML) so messages can never be interpreted as HTML.
function showMessage(el, text, kind) {
  el.textContent = text;
  el.className = "message " + (kind === "success" ? "message-success" : "message-error");
  el.hidden = false;
}

function setupRegister() {
  const form = document.getElementById("register-form");
  if (!form) return;
  const msg = document.getElementById("form-message");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const username = form.username.value.trim();
    const password = form.password.value;
    const confirm = form.confirm.value;

    if (!username) return showMessage(msg, "Username is required.");
    if (!USERNAME_RE.test(username))
      return showMessage(msg, "Username must be 3-30 characters: letters, numbers, '.', '_' or '-'.");
    if (!password) return showMessage(msg, "Password is required.");
    if (password.length < 12) return showMessage(msg, "Password must be at least 12 characters.");
    if (password.length > 128) return showMessage(msg, "Password must be at most 128 characters.");
    if (password !== confirm) return showMessage(msg, "Passwords do not match.");

    const button = form.querySelector("button[type=submit]");
    button.disabled = true;
    const { ok, data } = await postJSON("/register", { username, password });
    button.disabled = false;

    if (ok) {
      showMessage(msg, (data.message || "Account created.") + " Redirecting to login...", "success");
      form.reset();
      setTimeout(() => { window.location.href = "/login"; }, 1200);
    } else {
      showMessage(msg, data.error || "Registration failed.");
    }
  });
}

function setupLogin() {
  const form = document.getElementById("login-form");
  if (!form) return;
  const msg = document.getElementById("form-message");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const username = form.username.value.trim();
    const password = form.password.value;

    if (!username) return showMessage(msg, "Username is required.");
    if (!password) return showMessage(msg, "Password is required.");

    const button = form.querySelector("button[type=submit]");
    button.disabled = true;
    const { ok, data } = await postJSON("/login", { username, password });
    button.disabled = false;

    if (ok) {
      window.location.href = data.redirect || "/dashboard";
    } else {
      form.password.value = "";
      showMessage(msg, data.error || "Invalid username or password.");
    }
  });
}

function setupLogout() {
  const button = document.getElementById("logout-btn");
  if (!button) return;
  button.addEventListener("click", async () => {
    button.disabled = true;
    const { data } = await postJSON("/logout");
    // Use replace() so "Back" does not return to the protected page.
    window.location.replace(data.redirect || "/");
  });
}

document.addEventListener("DOMContentLoaded", () => {
  setupRegister();
  setupLogin();
  setupLogout();
});

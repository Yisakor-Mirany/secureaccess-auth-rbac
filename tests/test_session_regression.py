"""Regression tests for F1 session eviction vulnerability."""

import os
import tempfile

from app import create_app


def test_sessions_not_evicted_after_1000_new_sessions():
    """
    F1 regression test.

    Verify that an existing session remains valid
    after more than 1,000 additional sessions are created.
    """

    with tempfile.TemporaryDirectory() as temp_dir:

        session_database = os.path.join(
            temp_dir,
            "test_sessions.db"
        )

        app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret-key-for-regression",
            "SESSION_TYPE": "sqlalchemy",
            "SQLALCHEMY_DATABASE_URI": (
                "sqlite:///" + session_database
            ),
            "SESSION_CLEANUP_N_REQUESTS": 100,
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": False,
        })

        # Create the original client and session.
        original_client = app.test_client()

        with original_client.session_transaction() as session:
            session["test_marker"] = "original_session"

        # Generate more than the original 1,000-session limit.
        for i in range(1100):

            client = app.test_client()

            with client.session_transaction() as session:
                session["test_marker"] = f"session_{i}"

        # Verify that the original session still exists.
        with original_client.session_transaction() as session:

            assert session.get("test_marker") == "original_session", (
                "F1 regression: original session was evicted!"
            )
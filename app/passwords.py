"""Password hashing with Argon2id.

argon2-cffi generates a random salt for every hash and stores the salt and
cost parameters inside the hash string itself, e.g.
    $argon2id$v=19$m=65536,t=3,p=4$<salt>$<hash>
"""
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()  # Library defaults follow RFC 9106 recommendations

# Used when a username does not exist, so that a failed login takes about the
# same time either way and response timing does not reveal valid usernames.
_DUMMY_HASH = _hasher.hash("dummy-password-for-timing-equalization")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    """Check a password. Pass password_hash=None when the user does not exist."""
    if password_hash is None:
        # Burn the same CPU time as a real check, then fail.
        try:
            _hasher.verify(_DUMMY_HASH, password)
        except VerificationError:
            pass
        return False
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):  # includes VerifyMismatchError
        return False


def needs_rehash(password_hash: str) -> bool:
    """True if the hash was made with weaker parameters than today's settings."""
    return _hasher.check_needs_rehash(password_hash)

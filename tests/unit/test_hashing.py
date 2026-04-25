"""Unit tests for password hashing utilities."""
import pytest
from app.auth.hashing import hash_password, verify_password


def test_hash_is_not_plaintext():
    pw = "SuperSecret123!"
    hashed = hash_password(pw)
    assert hashed != pw
    assert hashed.startswith("$2")  # bcrypt prefix


def test_verify_correct_password():
    pw = "CorrectHorseBatteryStaple"
    assert verify_password(pw, hash_password(pw)) is True


def test_verify_wrong_password():
    hashed = hash_password("right-password")
    assert verify_password("wrong-password", hashed) is False


def test_hashes_are_unique_per_call():
    """bcrypt salts each hash, so two hashes of the same password differ."""
    pw = "samePassword123"
    assert hash_password(pw) != hash_password(pw)


def test_empty_password_raises():
    with pytest.raises(ValueError):
        hash_password("")


def test_verify_handles_empty_inputs():
    assert verify_password("", "anything") is False
    assert verify_password("anything", "") is False


def test_verify_handles_malformed_hash():
    assert verify_password("password", "not-a-real-hash") is False

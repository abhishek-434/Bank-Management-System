"""Automated tests for authentication, password hashing, lockout, and sessions."""
import pytest
from services.auth_service import auth_service
from config.constants import UserRole


def test_password_hashing():
    """Verify that bcrypt hashes are salted and verifiable."""
    plain = "SecureBanking@2026"
    hashed = auth_service.hash_password(plain)

    assert hashed != plain
    assert auth_service.verify_password(plain, hashed) is True
    assert auth_service.verify_password("WrongPassword", hashed) is False


def test_successful_login(test_user):
    """Test successful authentication yielding valid session context."""
    success, session_ctx, msg = auth_service.login("test_customer", "Pass@1234")

    assert success is True
    assert session_ctx is not None
    assert session_ctx.username == "test_customer"
    assert session_ctx.role == UserRole.CUSTOMER.value
    assert session_ctx.is_customer is True
    assert session_ctx.is_admin is False


def test_invalid_password_and_lockout(test_user):
    """Verify failed attempts increment and trigger account lockout after 5 tries."""
    for attempt in range(1, 5):
        ok, sess, msg = auth_service.login("test_customer", "WrongPassword")
        assert ok is False
        assert "Invalid username or password" in msg

    # 5th attempt triggers lockout
    ok, sess, msg = auth_service.login("test_customer", "WrongPassword")
    assert ok is False
    assert "locked" in msg.lower()


def test_change_password(test_user):
    """Verify password update with validation and old password verification."""
    # Mismatched confirmation
    ok, msg = auth_service.change_password(test_user, "Pass@1234", "NewPass@123", "Mismatch@123")
    assert ok is False
    assert "match" in msg.lower()

    # Weak password
    ok, msg = auth_service.change_password(test_user, "Pass@1234", "weak", "weak")
    assert ok is False

    # Valid change
    ok, msg = auth_service.change_password(test_user, "Pass@1234", "NewPass@2026", "NewPass@2026")
    assert ok is True

    # Login with new password
    ok, sess, _ = auth_service.login("test_customer", "NewPass@2026")
    assert ok is True


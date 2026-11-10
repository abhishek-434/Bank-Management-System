"""Authentication and session management service with bcrypt password hashing."""
import bcrypt
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy import select
from config.settings import settings
from config.constants import UserRole
from database.connection import db_manager
from models.user import User
from models.customer import Customer
from models.employee import Employee
from services.audit_service import audit_service
from utils.validators import validate_password_strength

logger = logging.getLogger("bms.auth_service")


class SessionContext:
    """Active user session representation."""

    def __init__(
        self,
        user_id: str,
        username: str,
        role: str,
        customer_id: Optional[str] = None,
        employee_id: Optional[str] = None,
        display_name: str = "",
    ):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.customer_id = customer_id
        self.employee_id = employee_id
        self.display_name = display_name or username
        self.login_time = datetime.now(timezone.utc)

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN.value

    @property
    def is_employee(self) -> bool:
        return self.role == UserRole.EMPLOYEE.value

    @property
    def is_customer(self) -> bool:
        return self.role == UserRole.CUSTOMER.value


class AuthService:
    """Manages credentials, secure hashing, lockout policies, and user sessions."""

    def __init__(self):
        self._current_session: Optional[SessionContext] = None

    @property
    def current_session(self) -> Optional[SessionContext]:
        return self._current_session

    @staticmethod
    def hash_password(plain_password: str) -> str:
        """Hash a plain text password using bcrypt with configured salt rounds."""
        salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
        hashed_bytes = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
        return hashed_bytes.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against bcrypt hash."""
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False

    def login(self, username: str, plain_password: str, ip_address: str = "127.0.0.1") -> Tuple[bool, Optional[SessionContext], str]:
        """
        Authenticate a user by username and password.
        Returns: (success, session_context, message)
        """
        if not username or not plain_password:
            return False, None, "Username and password are required."

        with db_manager.session_scope() as session:
            stmt = select(User).where(User.username == username.strip())
            user = session.execute(stmt).scalars().first()

            if not user:
                logger.warning(f"Login failed: User '{username}' does not exist.")
                return False, None, "Invalid username or password."

            if not user.is_active:
                logger.warning(f"Login rejected: User '{username}' is disabled.")
                return False, None, "This account is disabled. Please contact an administrator."

            # Check lockout
            if user.is_locked():
                remaining = int((user.locked_until - datetime.now(timezone.utc)).total_seconds() // 60) + 1
                logger.warning(f"Login rejected: User '{username}' is locked.")
                return False, None, f"Account is temporarily locked. Please try again in {remaining} minute(s)."

            # Verify password
            if not self.verify_password(plain_password, user.password_hash):
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                    user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCOUNT_LOCK_MINUTES)
                    audit_service.log(
                        action="ACCOUNT_LOCKED",
                        target_entity="User",
                        target_id=user.id,
                        user_id=user.id,
                        details={"reason": "Excessive failed login attempts", "attempts": user.failed_login_attempts},
                        ip_address=ip_address,
                        session=session,
                    )
                    return False, None, f"Account locked for {settings.ACCOUNT_LOCK_MINUTES} minutes due to excessive failed attempts."

                audit_service.log(
                    action="LOGIN_FAILED",
                    target_entity="User",
                    target_id=user.id,
                    user_id=user.id,
                    details={"attempt": user.failed_login_attempts},
                    ip_address=ip_address,
                    session=session,
                )
                return False, None, "Invalid username or password."

            # Successful login: reset failed attempts
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login = datetime.now(timezone.utc)

            # Determine associated IDs and display name
            customer_id = None
            employee_id = None
            display_name = user.username

            if user.role == UserRole.CUSTOMER.value:
                cust = session.execute(select(Customer).where(Customer.user_id == user.id)).scalars().first()
                if cust:
                    customer_id = cust.id
                    display_name = cust.full_name
            elif user.role in (UserRole.EMPLOYEE.value, UserRole.ADMIN.value):
                emp = session.execute(select(Employee).where(Employee.user_id == user.id)).scalars().first()
                if emp:
                    employee_id = emp.id
                    display_name = emp.full_name

            audit_service.log(
                action="LOGIN_SUCCESS",
                target_entity="User",
                target_id=user.id,
                user_id=user.id,
                details={"role": user.role},
                ip_address=ip_address,
                session=session,
            )

            sess_ctx = SessionContext(
                user_id=user.id,
                username=user.username,
                role=user.role,
                customer_id=customer_id,
                employee_id=employee_id,
                display_name=display_name,
            )
            self._current_session = sess_ctx
            return True, sess_ctx, "Login successful."

    def logout(self, ip_address: str = "127.0.0.1") -> None:
        """Terminate the active session."""
        if self._current_session:
            audit_service.log(
                action="LOGOUT",
                target_entity="User",
                target_id=self._current_session.user_id,
                user_id=self._current_session.user_id,
                ip_address=ip_address,
            )
            self._current_session = None

    def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
        confirm_password: str,
    ) -> Tuple[bool, str]:
        """Change user password with strict validation and old password verification."""
        if new_password != confirm_password:
            return False, "New password and confirmation do not match."

        is_valid, msg = validate_password_strength(new_password)
        if not is_valid:
            return False, msg

        with db_manager.session_scope() as session:
            user = session.get(User, user_id)
            if not user:
                return False, "User not found."

            if not self.verify_password(current_password, user.password_hash):
                return False, "Current password is incorrect."

            user.password_hash = self.hash_password(new_password)
            audit_service.log(
                action="PASSWORD_CHANGED",
                target_entity="User",
                target_id=user.id,
                user_id=user.id,
                session=session,
            )
            return True, "Password updated successfully."

    def create_user(
        self,
        username: str,
        plain_password: str,
        role: str = UserRole.CUSTOMER.value,
        session=None,
    ) -> User:
        """Create a new user with hashed password."""
        is_valid, msg = validate_password_strength(plain_password)
        if not is_valid:
            raise ValueError(f"Password does not meet complexity requirements: {msg}")

        user = User(
            username=username.strip(),
            password_hash=self.hash_password(plain_password),
            role=role,
            is_active=True,
        )
        if session:
            session.add(user)
        else:
            with db_manager.session_scope() as sess:
                sess.add(user)
        return user


auth_service = AuthService()


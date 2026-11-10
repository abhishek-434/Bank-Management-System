"""Customer lifecycle and management service."""
import logging
from datetime import date
from typing import Optional, List, Tuple
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from database.connection import db_manager
from models.customer import Customer
from models.user import User
from models.account import Account
from models.loan import Loan
from config.constants import CustomerStatus, UserRole
from utils.generators import generate_customer_code
from utils.validators import validate_email, validate_phone
from services.auth_service import auth_service
from services.audit_service import audit_service

logger = logging.getLogger("bms.customer_service")


class CustomerService:
    """Handles customer registration, updates, search, and status controls."""

    def register_customer(
        self,
        first_name: str,
        last_name: str,
        date_of_birth: date,
        email: str,
        phone: str,
        address: str,
        govt_id: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        created_by_user_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[Customer], str]:
        """Register a new customer and optionally create a login user account."""
        if not first_name.strip() or not last_name.strip():
            return False, None, "First name and last name are required."

        if not validate_email(email):
            return False, None, "Invalid email address."

        if not validate_phone(phone):
            return False, None, "Invalid phone number."

        with db_manager.session_scope() as session:
            # Check unique email
            existing_email = session.execute(
                select(Customer).where(Customer.email == email.strip().lower())
            ).scalars().first()
            if existing_email:
                return False, None, f"A customer with email '{email}' already exists."

            # Optional user account
            user_id = None
            if username and password:
                # Check username
                existing_user = session.execute(
                    select(User).where(User.username == username.strip())
                ).scalars().first()
                if existing_user:
                    return False, None, f"Username '{username}' is already taken."

                try:
                    new_user = auth_service.create_user(
                        username=username,
                        plain_password=password,
                        role=UserRole.CUSTOMER.value,
                        session=session,
                    )
                    session.flush()
                    user_id = new_user.id
                except ValueError as ve:
                    return False, None, str(ve)

            # Generate unique code
            customer_code = generate_customer_code()
            masked_id = f"ID-***-{govt_id.strip()[-4:]}" if len(govt_id.strip()) >= 4 else "ID-***-DEMO"

            customer = Customer(
                user_id=user_id,
                customer_code=customer_code,
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                date_of_birth=date_of_birth,
                email=email.strip().lower(),
                phone=phone.strip(),
                address=address.strip(),
                govt_id_masked=masked_id,
                status=CustomerStatus.ACTIVE.value,
            )
            session.add(customer)
            session.flush()

            audit_service.log(
                action="CUSTOMER_REGISTERED",
                target_entity="Customer",
                target_id=customer.id,
                user_id=created_by_user_id,
                details={"code": customer.customer_code, "name": customer.full_name},
                session=session,
            )

            logger.info(f"Customer {customer.customer_code} ({customer.full_name}) registered successfully.")
            return True, customer, "Customer registered successfully."

    def update_customer(
        self,
        customer_id: str,
        first_name: str,
        last_name: str,
        phone: str,
        address: str,
        updated_by_user_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Update customer personal contact details."""
        if not first_name.strip() or not last_name.strip():
            return False, "First name and last name are required."

        if not validate_phone(phone):
            return False, "Invalid phone number."

        with db_manager.session_scope() as session:
            customer = session.get(Customer, customer_id)
            if not customer:
                return False, "Customer not found."

            customer.first_name = first_name.strip()
            customer.last_name = last_name.strip()
            customer.phone = phone.strip()
            customer.address = address.strip()

            audit_service.log(
                action="CUSTOMER_UPDATED",
                target_entity="Customer",
                target_id=customer.id,
                user_id=updated_by_user_id,
                details={"name": customer.full_name},
                session=session,
            )
            return True, "Customer details updated successfully."

    def set_status(
        self,
        customer_id: str,
        new_status: str,
        admin_user_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Activate, deactivate, or suspend a customer."""
        valid_statuses = [s.value for s in CustomerStatus]
        if new_status not in valid_statuses:
            return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"

        with db_manager.session_scope() as session:
            customer = session.get(Customer, customer_id)
            if not customer:
                return False, "Customer not found."

            old_status = customer.status
            customer.status = new_status

            # If customer has a linked user account, keep is_active synced
            if customer.user_id:
                user = session.get(User, customer.user_id)
                if user:
                    user.is_active = (new_status == CustomerStatus.ACTIVE.value)

            audit_service.log(
                action="CUSTOMER_STATUS_CHANGED",
                target_entity="Customer",
                target_id=customer.id,
                user_id=admin_user_id,
                details={"old": old_status, "new": new_status},
                session=session,
            )
            return True, f"Customer status updated to {new_status}."

    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        """Retrieve customer by unique ID with linked accounts and loans."""
        with db_manager.session_scope() as session:
            stmt = (
                select(Customer)
                .options(selectinload(Customer.accounts), selectinload(Customer.loans))
                .where(Customer.id == customer_id)
            )
            return session.execute(stmt).scalars().first()

    def get_by_user_id(self, user_id: str) -> Optional[Customer]:
        """Retrieve customer associated with a user ID."""
        with db_manager.session_scope() as session:
            stmt = (
                select(Customer)
                .options(selectinload(Customer.accounts))
                .where(Customer.user_id == user_id)
            )
            return session.execute(stmt).scalars().first()

    def search_customers(
        self,
        search_query: str = "",
        status_filter: str = "ALL",
        limit: int = 100,
    ) -> List[Customer]:
        """Search customers by name, code, or email, with optional status filter."""
        with db_manager.session_scope() as session:
            stmt = select(Customer).options(selectinload(Customer.accounts))

            if status_filter and status_filter != "ALL":
                stmt = stmt.where(Customer.status == status_filter)

            if search_query:
                q = f"%{search_query.strip()}%"
                stmt = stmt.where(
                    or_(
                        Customer.first_name.ilike(q),
                        Customer.last_name.ilike(q),
                        Customer.customer_code.ilike(q),
                        Customer.email.ilike(q),
                        Customer.phone.ilike(q),
                    )
                )

            stmt = stmt.order_by(Customer.created_at.desc()).limit(limit)
            return session.execute(stmt).scalars().all()


customer_service = CustomerService()


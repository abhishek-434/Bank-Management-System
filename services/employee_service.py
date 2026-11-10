"""Employee management service."""
import logging
from typing import Optional, List, Tuple
from sqlalchemy import select, or_
from database.connection import db_manager
from models.employee import Employee
from models.user import User
from config.constants import EmployeeStatus, UserRole
from utils.generators import generate_employee_code
from utils.validators import validate_email, validate_phone
from services.auth_service import auth_service
from services.audit_service import audit_service

logger = logging.getLogger("bms.employee_service")


class EmployeeService:
    """Handles employee registration, updates, and role assignments."""

    def register_employee(
        self,
        first_name: str,
        last_name: str,
        department: str,
        designation: str,
        email: str,
        phone: str,
        username: str,
        password: str,
        role: str = UserRole.EMPLOYEE.value,
        created_by_user_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[Employee], str]:
        """Register bank employee along with credentials."""
        if not first_name.strip() or not last_name.strip():
            return False, None, "First and last name are required."

        if not validate_email(email):
            return False, None, "Invalid email address."

        if not validate_phone(phone):
            return False, None, "Invalid phone number."

        with db_manager.session_scope() as session:
            existing_user = session.execute(
                select(User).where(User.username == username.strip())
            ).scalars().first()
            if existing_user:
                return False, None, f"Username '{username}' is already in use."

            existing_email = session.execute(
                select(Employee).where(Employee.email == email.strip().lower())
            ).scalars().first()
            if existing_email:
                return False, None, f"Email '{email}' is already registered to an employee."

            try:
                user = auth_service.create_user(
                    username=username,
                    plain_password=password,
                    role=role,
                    session=session,
                )
                session.flush()
            except ValueError as ve:
                return False, None, str(ve)

            employee = Employee(
                user_id=user.id,
                employee_code=generate_employee_code(),
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                department=department.strip(),
                designation=designation.strip(),
                email=email.strip().lower(),
                phone=phone.strip(),
                status=EmployeeStatus.ACTIVE.value,
            )
            session.add(employee)
            session.flush()

            audit_service.log(
                action="EMPLOYEE_REGISTERED",
                target_entity="Employee",
                target_id=employee.id,
                user_id=created_by_user_id,
                details={"code": employee.employee_code, "role": role},
                session=session,
            )
            return True, employee, "Employee registered successfully."

    def list_employees(
        self,
        search_query: str = "",
        status_filter: str = "ALL",
    ) -> List[Employee]:
        """Fetch employees matching optional search terms."""
        with db_manager.session_scope() as session:
            stmt = select(Employee)
            if status_filter and status_filter != "ALL":
                stmt = stmt.where(Employee.status == status_filter)

            if search_query:
                q = f"%{search_query.strip()}%"
                stmt = stmt.where(
                    or_(
                        Employee.first_name.ilike(q),
                        Employee.last_name.ilike(q),
                        Employee.employee_code.ilike(q),
                        Employee.email.ilike(q),
                        Employee.department.ilike(q),
                    )
                )

            stmt = stmt.order_by(Employee.created_at.desc())
            return session.execute(stmt).scalars().all()

    def set_status(
        self,
        employee_id: str,
        new_status: str,
        admin_user_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Update employee status."""
        valid_statuses = [s.value for s in EmployeeStatus]
        if new_status not in valid_statuses:
            return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"

        with db_manager.session_scope() as session:
            emp = session.get(Employee, employee_id)
            if not emp:
                return False, "Employee not found."

            emp.status = new_status
            if emp.user_id:
                user = session.get(User, emp.user_id)
                if user:
                    user.is_active = (new_status == EmployeeStatus.ACTIVE.value)

            audit_service.log(
                action="EMPLOYEE_STATUS_CHANGED",
                target_entity="Employee",
                target_id=emp.id,
                user_id=admin_user_id,
                details={"new_status": new_status},
                session=session,
            )
            return True, f"Employee status updated to {new_status}."


employee_service = EmployeeService()


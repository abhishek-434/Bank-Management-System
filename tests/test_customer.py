"""Automated tests for customer lifecycle, CRUD, and status."""
from datetime import date
from services.customer_service import customer_service
from config.constants import CustomerStatus


def test_customer_registration():
    """Verify customer registration with validation."""
    ok, cust, msg = customer_service.register_customer(
        first_name="Alice",
        last_name="Smith",
        date_of_birth=date(1995, 4, 12),
        email="alice.smith@example.com",
        phone="+1-555-4321",
        address="456 Oak Avenue",
        govt_id="ID-772910",
        username="alicesmith",
        password="Password@123",
    )

    assert ok is True
    assert cust is not None
    assert cust.full_name == "Alice Smith"
    assert cust.customer_code.startswith("CUST-")
    assert cust.status == CustomerStatus.ACTIVE.value


def test_duplicate_email_rejection(test_customer):
    """Verify that registering with duplicate email is blocked."""
    ok, cust, msg = customer_service.register_customer(
        first_name="Jane",
        last_name="Duplicate",
        date_of_birth=date(1990, 1, 1),
        email="jane.doe@test.com",  # Matches test_customer fixture
        phone="+1-555-9999",
        address="999 Street",
        govt_id="ID-000",
    )

    assert ok is False
    assert "already exists" in msg


def test_customer_status_transition(test_customer):
    """Verify customer activation, deactivation, and search."""
    ok, msg = customer_service.set_status(test_customer, CustomerStatus.INACTIVE.value)
    assert ok is True

    cust = customer_service.get_by_id(test_customer)
    assert cust.status == CustomerStatus.INACTIVE.value

    # Search returns customer
    results = customer_service.search_customers(search_query="Jane")
    assert len(results) == 1
    assert results[0].first_name == "Jane"


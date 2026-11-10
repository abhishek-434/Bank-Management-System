"""Application entry launcher for the Professional Banking Management System (BMS)."""
import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from database.migrations.init_db import init_database
from database.seed_data import seed_demo_data
from ui.app import start_app


def main():
    """Verify database initialization, seed demo data, and start GUI application."""
    print("=" * 65)
    print("APEX HORIZON BANK - CORE BANKING MANAGEMENT SYSTEM")
    print("=" * 65)
    print("Initializing persistent storage and database schema...")
    try:
        init_database()
        seed_demo_data()
        print("Database ready.")
    except Exception as exc:
        print(f"Warning during database bootstrap: {exc}")

    print("Launching Desktop UI interface...")
    start_app()


if __name__ == "__main__":
    main()


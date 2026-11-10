# Apex Horizon Bank — Core Banking Management System (BMS)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter%206.0-teal.svg)](https://customtkinter.tomschimansky.com/)
[![Database](https://img.shields.io/badge/DB-PostgreSQL%20%2F%20SQLAlchemy%202.0-blueviolet.svg)](https://www.postgresql.org/)
[![Precision](https://img.shields.io/badge/Math-Python%20Decimal%20(No%20Floats)-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/tests-23%20passed%20(100%25)-success.svg)]()

A complete, native Python desktop banking management application simulating core commercial banking operations in a controlled educational demonstration environment. Built with an immutable double-entry ledger architecture, strict decimal precision, role-based access control (RBAC), modern high-DPI CustomTkinter UI, interactive Matplotlib analytics, and automated PDF receipt & statement generation.

---

## Table of Contents

1. [Key Features](#key-features)
2. [Technology Stack](#technology-stack)
3. [Architecture & Database Design](#architecture--database-design)
4. [Demonstration Credentials](#demonstration-credentials)
5. [Prerequisites & System Requirements](#prerequisites--system-requirements)
6. [Installation & Setup](#installation--setup)
7. [PostgreSQL Configuration](#postgresql-configuration)
8. [Database Initialization & Seeding](#database-initialization--seeding)
9. [Running the Application](#running-the-application)
10. [Automated Testing](#automated-testing)
11. [Backup & Restoration](#backup--restoration)
12. [Troubleshooting Guide](#troubleshooting-guide)
13. [Educational Disclaimer](#educational-disclaimer)

---

## 1. Key Features

### 🔐 Security & Access Control
- **Role-Based Access Control (RBAC)**: Distinct permissions for **Administrators**, **Employees / Tellers**, and **Customer Self-Service**.
- **Bcrypt Password Hashing**: Adaptive work factor with automatic salt generation; plain-text passwords are never stored.
- **Account Lockout Policy**: Monitored failed login attempts; locks accounts for 15 minutes after 5 consecutive failed attempts.
- **Audit Logging**: Immutable, tamper-evident audit logs capturing every administrative, financial, and security action with IP addresses and metadata.

### 💳 Core Banking Operations
- **Double-Entry Ledger Immutability**: All financial mutations create permanent, unalterable ledger records (`DEPOSIT`, `WITHDRAWAL`, `TRANSFER_DEBIT`, `TRANSFER_CREDIT`, `LOAN_DISBURSEMENT`, `LOAN_REPAYMENT`).
- **Atomic Fund Transfers**: Internal transfers use database transactions with row-level locks (`with_for_update()`) ensuring sender debit and beneficiary credit succeed together or roll back atomically.
- **Zero Floating-Point Inaccuracies**: Strict `decimal.Decimal` computation down to cent accuracy across all balances, fees, and transfers.
- **Financial Guardrails**:
  - Enforces minimum balance requirements per account type.
  - Prevents overdrafts and negative balances.
  - Configurable daily withdrawal ceilings.
  - Prohibits financial activity on `FROZEN`, `DORMANT`, or `CLOSED` accounts.
  - Rejects account closures if funds remain or active loans exist.

### 💼 Educational Loan Management
- **Loan Applications**: Customer loan applications with automated simple-interest calculations:
  $$\text{Total Interest} = \frac{P \times R \times M}{100 \times 12}$$
  $$\text{Total Payable} = P + \text{Total Interest}$$
- **Staff Approval & Disbursement**: Direct disbursement into active customer accounts.
- **Repayment Tracking**: Partial or full repayments reducing principal and closing the loan upon payoff.

### 📊 Analytics & Reporting
- **Live Dashboards**: Interactive KPI cards (Total Customers, Active Accounts, Vault Reserves, Deposits Volume).
- **Embedded Visualizations**: Matplotlib charts matching the dark navy palette embedded directly into CustomTkinter:
  - Monthly inflow vs. outflow volume trends.
  - Portfolio distribution across Savings, Current, and Fixed Deposit products.
- **Export Capabilities**:
  - Official transaction receipts generated as high-resolution PDFs via ReportLab.
  - Full periodic bank account statements exported to PDF.
  - Master ledger exports to CSV.

---

## 2. Technology Stack

| Layer | Technology | Details |
| :--- | :--- | :--- |
| **GUI Framework** | CustomTkinter 6.0+ | Modern native desktop framework with dark mode support. |
| **Language** | Python 3.11+ | Type-annotated, modern modular codebase. |
| **ORM / Persistence** | SQLAlchemy 2.0+ | Enterprise ORM with row-level locking and connection pooling. |
| **DB Connector** | Psycopg2-binary | High-performance C-binary PostgreSQL driver. |
| **Storage Engines** | PostgreSQL (Primary) + SQLite (Fallback) | Automatic fallback to local SQLite for zero-config demonstration. |
| **Security** | Bcrypt 5.0+ | Secure salted password hashing. |
| **Analytics** | Pandas 3.0+ & Matplotlib 3.11+ | Data aggregation, pivot metrics, and embedded TkAgg charts. |
| **PDF Generation** | ReportLab 4.4+ | Pixel-precise statements and customer receipts. |
| **Testing** | Pytest 9.2+ | Automated unit, concurrency, and rollback test suite. |

---

## 3. Architecture & Database Design

The system implements 10 normalized tables adhering to 3NF standards:

```
├── users             (Authentication, roles, failed attempts, lockouts)
├── customers         (KYC, masked identity, personal and contact profiles)
├── employees         (Staff details, department, designations)
├── account_types     (Product rules: Savings, Current, Fixed Deposit)
├── accounts          (Bank account master, balances, lifecycle status)
├── transactions      (Append-only financial ledger entries)
├── transfers         (Internal dual-account transfer records)
├── loans             (Loan contracts, principal, interest, remaining balance)
├── loan_repayments   (Historical installment payment ledger)
└── audit_logs        (System-wide immutable security audit trail)
```

---

## 4. Demonstration Credentials

The database includes realistic synthetic accounts pre-seeded for immediate evaluation:

| Role | Username | Password | Purpose / Associated Profile |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `Admin@123` | Alexander Vance (Chief Systems Architect) — Full admin control, staff management, audit trail inspection. |
| **Employee (Teller)** | `employee1` | `Employee@123` | Sarah Jenkins (Senior Banking Officer) — Customer onboarding, deposits, withdrawals, transfers. |
| **Employee (Lending)** | `employee2` | `Employee@123` | David Ross (Credit Specialist) — Loan reviews, approvals, and repayments. |
| **Customer** | `customer1` | `Customer@123` | Eleanor Sterling — Savings Account (`1008472910`) & FD Account (`1009182341`). |
| **Customer** | `customer2` | `Customer@123` | Marcus Thorne — Commercial Current Account (`1003928172`). |
| **Customer** | `customer3` | `Customer@123` | Chloe Bennett — Savings Account (`1005829143`). |

> **Note:** The login screen provides **Quick Demo Login buttons** at the bottom to prefill credentials with a single click.

---

## 5. Prerequisites & System Requirements

- **Operating System**: Windows 10/11, macOS, or Linux.
- **Python**: Version **3.11** or later.
- **PostgreSQL**: Version 14, 15, or 16 (Optional for local testing; the app automatically falls back to an embedded SQLite database if PostgreSQL is not installed).

---

## 6. Installation & Setup

### Step 1: Clone or Navigate to the Workspace
```powershell
cd d:\My-Projects\BMS
```

### Step 2: Create and Activate a Python Virtual Environment
```powershell
# Create virtual environment
python -m venv venv

# Activate on Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Activate on Linux / macOS
source venv/bin/activate
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

---

## 7. PostgreSQL Configuration

1. Create a dedicated database in PostgreSQL:
```sql
CREATE DATABASE bms_db;
CREATE USER postgres WITH ENCRYPTED PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE bms_db TO postgres;
```

2. Copy `.env.example` to `.env` and verify credentials:
```powershell
Copy-Item .env.example .env
```

3. Update `.env` with your PostgreSQL credentials:
```ini
DB_ENGINE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bms_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password
```

> **Smart Storage Engine Adaptability:**
> If you do not have a PostgreSQL server running locally, the application automatically detects connection timeouts and falls back seamlessly to the embedded SQLite database `bms.db`. You can also force local offline mode by setting `DB_ENGINE=sqlite` in `.env`.

---

## 8. Database Initialization & Seeding

To initialize the schema and populate the demo dataset manually:
```powershell
python -m database.seed_data
```

This will:
1. Create all 10 normalized tables.
2. Seed default account types (`SAVINGS`, `CURRENT`, `FIXED_DEPOSIT`).
3. Seed admin, employee, and customer accounts with active balances.
4. Populate 30 days of realistic financial transactions, transfers, active loans, and audit logs.

---

## 9. Running the Application

Launch the native desktop interface:
```powershell
python run.py
```

The application window will open with the navy blue and subtle cyan desktop interface.

---

## 10. Automated Testing

The automated test suite runs against an isolated in-memory test database, ensuring zero contamination of your demonstration or production data.

Run the full Pytest test suite:
```powershell
pytest
```

Run with verbose test execution:
```powershell
pytest -v
```

### Test Suite Coverage:
- `tests/test_auth.py`: Password hashing, session creation, failed attempts, and account lockout.
- `tests/test_customer.py`: Customer CRUD, unique email verification, status toggling.
- `tests/test_account.py`: Account opening, minimum balance constraints, freeze rules, zero-balance closure checks.
- `tests/test_transactions.py`: Cash deposits, withdrawals, minimum balance protection, daily limit enforcement.
- `tests/test_transfers.py`: Internal transfers, atomic debit/credit, same-account rejection, insufficient balance rollback.
- `tests/test_loans.py`: Interest calculation, loan application, disbursement crediting, repayments, loan payoff closure.
- `tests/test_reports.py`: KPI aggregation, CSV report export, ReportLab PDF receipt generation.

---

## 11. Backup & Restoration

### PostgreSQL Backup
```powershell
# Create a timestamped SQL dump
pg_dump -U postgres -h localhost -d bms_db > backup_bms_$(Get-Date -Format "yyyyMMdd_HHmmss").sql
```

### PostgreSQL Restore
```powershell
# Restore from SQL dump
psql -U postgres -h localhost -d bms_db < backup_bms_YYYYMMDD_HHMMSS.sql
```

### SQLite Backup (Fallback mode)
Simply copy `bms.db`:
```powershell
Copy-Item bms.db "bms_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"
```

---

## 12. Troubleshooting Guide

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `psycopg2.OperationalError: connection to server failed` | PostgreSQL service is stopped or port 5432 is blocked. | The app will automatically fall back to `bms.db`. To fix Postgres, start the PostgreSQL Windows Service or check credentials in `.env`. |
| `sqlite3.OperationalError: attempt to write a readonly database` | Running in a restricted sandbox without write permissions to `bms.db`. | Ensure proper filesystem write permissions on `d:\My-Projects\BMS` or run outside sandbox. |
| High DPI / Scaling blurry fonts | Windows display scaling mismatch. | CustomTkinter handles DPI automatically. Set `ctk.deactivate_automatic_dpi_awareness()` if custom scaling is desired. |
| Missing fonts warning in console | Segoe UI or Roboto not loaded. | Harmless warning; CustomTkinter uses standard fallback system fonts on Windows. |

---

## 13. Educational Disclaimer

> **IMPORTANT**: This software is designed and implemented exclusively for **educational, demonstration, and architectural study purposes**. It is not intended for production banking environments, does not process real money, does not link to real payment networks, and does not collect authentic government identity documents.


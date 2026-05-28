# Breathe ESG — Carbon Accounting Server (`breathe-esg-server`)

This is the backend server for the Breathe ESG platform. It is built using **Django** and **Django REST Framework (DRF)**. The server ingests raw activity and procurement data from various enterprise platforms (SAP, utility portals, and travel systems), parses and normalizes the data into a common schema, performs greenhouse gas (GHG) calculations, tracks audit logs, and exposes a secure REST API for review and lock operations.

---

## 🛠️ Tech Stack & Key Choices

- **Framework**: Django 4.2 & Django REST Framework (DRF) 3.14.
- **Database**: SQLite (configured for seamless upgrade to PostgreSQL in production via Django ORM).
- **Core Architecture**: Registry Pattern for data parsers, allowing new data source types to be added with minimal code modifications (Open-Closed Principle).
- **Authentication**: Native session-based cookie authentication with JSON endpoints, fully CSRF protected.
- **Audit System**: Custom `AuditLog` model recording every field-level change, old/new status, action author, and timestamp.

---

## 📂 Project Structure

```
breathe-esg-server/
├── apps/
│   ├── ingestion/       # Ingestion engines, parsers, serializers, views
│   │   ├── parsers/     # Modular parsers (SAP, Utility, Concur)
│   │   ├── migrations/  # Database schema migrations
│   │   ├── models.py    # DataSource, ActivityRecord, AuditLog models
│   │   └── views.py     # API Viewsets (Auth, Sources, Records, Review)
│   ├── emissions/       # Calculation engine and emission factor database
│   │   └── calculator.py# Conversion and CO₂e math engine
│   └── review/          # Dashboard stats aggregation
├── config/              # Core settings, URL routing, WSGI/ASGI configuration
├── manage.py            # Django management command CLI
└── requirements.txt     # Python package dependencies
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10 or 3.11 installed.

### 2. Setting Up Virtual Environment & Dependencies
From the `breathe-esg-server` folder, run:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Database Migrations & Initial Setup
Initialize the SQLite database and create an admin user:
```bash
# Run migrations
python manage.py migrate

# Create an admin user (for reviewer login)
python manage.py createsuperuser
```

### 4. Running the Development Server
Start the backend server locally:
```bash
python manage.py runserver
```
The server will run at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

---

## 🔌 API Documentation

All requests must include standard CSRF cookies in secure environments. The login endpoint accepts JSON payloads and establishes a session.

### 🔐 Authentication Endpoints

| Method | Endpoint | Description | Payload |
|--------|----------|-------------|---------|
| `GET` | `/api/auth/csrf/` | Set CSRF Cookie on client | None |
| `POST` | `/api/auth/login/` | JSON-based Session Login | `{"username": "...", "password": "..."}` |
| `POST` | `/api/auth/logout/` | End Session | None |
| `GET` | `/api/auth/status/` | Returns current login status | None |

### 📂 Data Ingestion & Review Endpoints

| Method | Endpoint | Description | Query / Form Params |
|--------|----------|-------------|---------------------|
| `POST` | `/api/sources/` | Upload CSV data source | `file` (multipart), `source_type` (string) |
| `GET` | `/api/sources/` | List uploaded data sources | None |
| `GET` | `/api/records/` | List paginated & filterable normalized records | `source_type`, `status`, `scope`, `search`, `page` |
| `PATCH` | `/api/records/{id}/review/` | Single record status review | `{"status": "APPROVED" \| "FLAGGED" \| "REJECTED", "reviewer_comment": "..."}` |
| `POST` | `/api/records/bulk-review/` | Bulk status review update | `{"ids": [1, 2, ...], "status": "APPROVED", "reviewer_comment": "..."}` |
| `POST` | `/api/records/lock/` | Seal all APPROVED records | None (Irreversible!) |
| `GET` | `/api/review/stats/` | Aggregated dashboard KPI stats | None |

---

## 🧪 Testing

The server comes with a robust unit test suite covering parsing rules, Haversine flight distance calculations, hotel night extraction, and unit conversions.

To run the test suite:
```bash
python manage.py test apps.ingestion -v2
```

The tests verify:
- **SAP Procurement Parser**: German header parsing, semi-colon delimiter, German decimal format, and GAL ➔ L conversion.
- **Utility Electricity Parser**: MWh ➔ kWh normalization and billing period parsing.
- **Corporate Travel Parser**: Free-text IATA code extraction, Haversine distance math, hotel night extraction, and Scope 3 calculation logic.

---

## 📐 Data Normalization & Engineering

To support compliance and auditing, the server converts disparate raw formats into a single table utilizing standard conversions:
- **Scope 1 (SAP Fuel)**: Normalizes liters and gallons. Calculates $CO_2e$ using US EPA / UK DEFRA fuel emission factors.
- **Scope 2 (Electricity)**: Converts MWh to kWh. Applies regional grid factors ($CO_2e$ per kWh).
- **Scope 3 (Travel)**: Computes direct distance using coordinate lookups and calculates emissions based on flight haul classification (short, medium, long-haul).

Review `MODEL.md` in the root folder for full database structure and math formulas.

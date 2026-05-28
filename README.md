# Breathe ESG — Carbon Accounting Server

This is the Django backend for the Breathe ESG platform. It handles file parsing, data normalization, greenhouse gas (GHG) calculations, audit trails, and the API that powers the frontend dashboard.

---

## 🛠️ The Tech & Design Choices

- **Core**: Django 4.2 & Django REST Framework (DRF) 3.14.
- **Database**: PostgreSQL (configured for production on Railway, with local PostgreSQL support).
- **Parser Registry**: Uses the Registry pattern so you can add new customer file layouts easily without rewriting the ingestion pipeline (Open-Closed Principle).
- **Session Auth**: Native cookie-based logins with JSON endpoints, fully CSRF protected.
- **Audit Trails**: A dedicated `AuditLog` table tracks every single field update, old/new values, who changed it, and when.

---

## 📂 Folder Tour

```
breathe-esg-server/
├── apps/
│   ├── ingestion/       # Parsing engines (SAP, Utility, Concur), views, and serializers
│   ├── emissions/       # Math engine & emission factor database (DEFRA / EPA lookup)
│   └── review/          # Dashboard stats aggregation
├── config/              # Django settings, CORS configurations, and root URLs
```

---

## 🚀 Get Started Locally

### 1. Set up your environment & packages
Ensure your local PostgreSQL server is running and you have created a database named `breath_esg_db`.
```bash
# Set up a virtual environment
python -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Run migrations & create an admin user
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 3. Spin up the server
```bash
python manage.py runserver
```
The API will run at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

---

## 🔌 API Quick Reference

- **`POST /api/auth/login/`**: Native session login.
- **`POST /api/sources/`**: Upload a new file (`file` and `source_type`).
- **`GET /api/records/`**: Fetch normalized and paginated activity records (supports status/scope/search filters).
- **`PATCH /api/records/{id}/review/`**: Single record review status update.
- **`POST /api/records/bulk-review/`**: Bulk approve, reject, or flag multiple IDs.
- **`POST /api/records/lock/`**: Seal all approved records (irreversible lock for auditors).
- **`GET /api/review/stats/`**: Key aggregated stats for the dashboard.

---

## 🧪 Testing

We have a comprehensive unit test suite covering parsing rules, Haversine flight distance calculations, hotel night extraction, and unit conversions.

To run the tests:
```bash
python manage.py test apps.ingestion -v2
```

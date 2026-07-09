# Rent Django Project

A personal rental management app for a house owner who collects rent payments directly.

The app helps the owner keep notes on renters, apartments, yearly rent amounts, monthly payments, who has paid, who has not paid, and how much money is still left for each renter. It is built for a simple owner-managed rental workflow rather than for tenants paying online.

## What It Does

- Manage floors and apartments.
- Add renters to available apartments.
- Automatically connect a renter to the apartment's floor.
- Keep renter email optional.
- Prevent two active renters from being assigned to the same apartment.
- Mark a renter as having left an apartment while keeping their payment history.
- Add yearly rent per apartment.
- Calculate monthly rent from the yearly rent.
- Track month-by-month payment status.
- Show how much was paid, how much was due, and how much is still left.
- Treat months before a renter's start month as not due.
- Provide a Django REST Framework API for the rental data.
- Use PostgreSQL with the pgvector extension.

## Tech Stack

- Python
- Django
- Django REST Framework
- SimpleJWT
- PostgreSQL
- pgvector
- Docker Compose

## Local Setup

Start the PostgreSQL/pgvector database:

```powershell
docker compose up -d db
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Apply migrations:

```powershell
python manage.py migrate
```

Create an admin user:

```powershell
python manage.py createsuperuser
```

Run the app:

```powershell
python manage.py runserver 127.0.0.1:8001
```

Open:

```text
http://127.0.0.1:8001/
```

## API

The REST API is available under:

```text
/api/
```

JWT token endpoints:

```text
/api/token/
/api/token/refresh/
```

## Database

This project uses PostgreSQL with pgvector instead of SQLite.

Default local database settings:

```text
database: rent_api
user: rent_api
password: rent_api
host: localhost
port: 5432
```

Inside Docker, Django connects to the database host named `db`.

## Notes

This app is intended for personal rental tracking by the property owner. Payments are entered manually by the owner after collecting money from renters.

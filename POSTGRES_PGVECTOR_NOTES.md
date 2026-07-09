# PostgreSQL + pgvector Setup

This project now uses PostgreSQL with the pgvector extension instead of SQLite.

## Start The Database

```bash
docker compose up -d db
```

The database settings are:

```text
database: rent_api
user: rent_api
password: rent_api
host: localhost
port: 5432
```

Inside Docker, the Django `web` service connects to the database host named `db`.

## Apply Migrations

```bash
python manage.py migrate
```

Migration `process.0007_enable_pgvector` enables the extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## Run Django

Local Python:

```bash
python manage.py runserver 127.0.0.1:8001
```

Docker:

```bash
docker compose up --build
```

## Important

The old `db.sqlite3` file is no longer used by Django. The new PostgreSQL database starts empty unless you manually export data from SQLite and import it into PostgreSQL.

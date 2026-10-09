# MyCore

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Update `.env` with the real database credentials and a private `SECRET_KEY`.

## Run

```bash
python -m uvicorn src:app --reload
```

The API is available at `http://127.0.0.1:8000`, and Swagger UI is available at
`http://127.0.0.1:8000/docs`.

## Database Migrations

This project uses the native Tortoise ORM migration CLI.

Create a migration after changing models:

```bash
python -m tortoise makemigrations -n describe_your_change
```

Apply pending migrations:

```bash
python -m tortoise migrate
```

Show migration history:

```bash
python -m tortoise history
```

If an existing database was created previously by `generate_schemas`, mark the
initial migration as applied without running its SQL again:

```bash
python -m tortoise migrate models 0001_initial --fake
```

Do not run `--fake` on a fresh database. Use `python -m tortoise migrate` there.

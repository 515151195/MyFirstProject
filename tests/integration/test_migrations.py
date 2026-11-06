from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from tortoise import connections


pytestmark = pytest.mark.integration
ROOT = Path(__file__).resolve().parents[2]


def test_tortoise_cli_reads_migrations():
    result = subprocess.run(
        [sys.executable, "-m", "tortoise", "heads"],
        cwd=ROOT,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "models.0005_add_organizations" in result.stdout


async def test_test_database_contains_all_business_tables(database: None):
    connection = connections.get("default")
    rows = await connection.execute_query_dict("SHOW TABLES")
    table_names = {next(iter(row.values())) for row in rows}

    assert {
        "user",
        "role",
        "user_role",
        "Organization",
        "Membership",
        "invitations",
        "approval_request",
        "approval_record",
        "idempotency_record",
        "outbox_message",
        "notification",
    }.issubset(table_names)


async def test_openapi_contains_core_api_groups(app):
    paths = app.openapi()["paths"]
    joined_paths = "\n".join(paths)

    for prefix in (
        "/api/v1/base",
        "/api/v1/users",
        "/api/v1/organizations",
        "/api/v1/invitations",
        "/api/v1/approvals",
        "/api/v1/notifications",
    ):
        assert prefix in joined_paths

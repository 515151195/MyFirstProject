from __future__ import annotations

from dataclasses import dataclass
from typing import Any


TEST_DB_SUFFIX = "_test"

# Keep child tables before their parents. This is useful for debugging even
# though reset_database temporarily disables MySQL foreign key checks.
BUSINESS_TABLES = (
    "notification",
    "outbox_message",
    "approval_record",
    "approval_request",
    "idempotency_record",
    "invitations",
    "Membership",
    "user_role",
    "Organization",
    "role",
    "user",
)


class UnsafeTestDatabaseError(RuntimeError):
    """Raised when a destructive test helper would touch a non-test database."""


@dataclass(frozen=True)
class SeededRoles:
    admin: Any
    user: Any


def ensure_test_database() -> str:
    from settings import settings

    database_name = settings.DB_NAME
    if not database_name.endswith(TEST_DB_SUFFIX):
        raise UnsafeTestDatabaseError(
            f"Refusing to modify non-test database {database_name!r}; "
            f"the name must end with {TEST_DB_SUFFIX!r}"
        )
    return database_name


async def reset_database() -> None:
    ensure_test_database()

    from tortoise import connections

    connection = connections.get("default")
    await connection.execute_script("SET FOREIGN_KEY_CHECKS=0")
    try:
        for table_name in BUSINESS_TABLES:
            await connection.execute_script(f"TRUNCATE TABLE `{table_name}`")
    finally:
        await connection.execute_script("SET FOREIGN_KEY_CHECKS=1")


async def seed_roles() -> SeededRoles:
    from models import Role

    admin, _ = await Role.get_or_create(
        name="admin",
        defaults={"desc": "Administrator"},
    )
    user, _ = await Role.get_or_create(
        name="user",
        defaults={"desc": "Normal user"},
    )
    return SeededRoles(admin=admin, user=user)


async def count_model(model: type[Any]) -> int:
    return await model.all().count()

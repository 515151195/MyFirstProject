import pytest

from utils.password import hash_password, verify_password


pytestmark = pytest.mark.unit


def test_hash_password_does_not_store_plaintext():
    password = "StrongPass123"

    hashed = hash_password(password)

    assert hashed != password
    assert password not in hashed
    assert hashed.startswith("$argon2")


def test_hash_password_uses_a_fresh_salt():
    password = "StrongPass123"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash
    assert verify_password(password, first_hash)
    assert verify_password(password, second_hash)


def test_verify_password_accepts_the_original_password():
    password = "StrongPass123"

    assert verify_password(password, hash_password(password))


@pytest.mark.parametrize(
    "wrong_password",
    [
        "StrongPass124",
        "strongpass123",
        "StrongPass123 ",
        "",
    ],
)
def test_verify_password_rejects_incorrect_password(wrong_password: str):
    password = "StrongPass123"

    assert not verify_password(wrong_password, hash_password(password))

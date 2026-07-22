import os

import pytest

from app.identity import AuthError, load_users, resolve_token

FIXTURE_USERS = os.path.join(os.path.dirname(__file__), "..", "data", "users.json")

pytestmark = pytest.mark.unit


@pytest.fixture
def users_by_token():
    return load_users(FIXTURE_USERS)


def test_valid_token_resolves_expected_user_and_roles(users_by_token):
    user = resolve_token("tok_marketing_demo", users_by_token)
    assert user.id == "u_maria"
    assert user.roles == ("marketing",)


def test_different_tokens_resolve_to_different_users(users_by_token):
    maria = resolve_token("tok_marketing_demo", users_by_token)
    sam = resolve_token("tok_sales_demo", users_by_token)
    assert maria.id != sam.id
    assert sam.roles == ("sales", "marketing")


def test_unknown_token_raises_auth_error(users_by_token):
    with pytest.raises(AuthError):
        resolve_token("tok_not_a_real_token", users_by_token)


def test_empty_token_raises_auth_error(users_by_token):
    with pytest.raises(AuthError):
        resolve_token("", users_by_token)


def test_none_token_raises_auth_error(users_by_token):
    with pytest.raises(AuthError):
        resolve_token(None, users_by_token)
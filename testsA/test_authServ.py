from services.auth_service import AuthService
from repositories.user_repository import UserRepository
import pytest

@pytest.fixture
def auth_service():
    repo = UserRepository()
    return AuthService(repo)


def test_register_success(auth_service):
    user = auth_service.register("test@mail.com", "123456", "Test")
    assert user["email"] == "test@mail.com"
    assert "password" not in user


def test_register_existing_email(auth_service):
    auth_service.register("test@mail.com", "123456", "Test")

    with pytest.raises(Exception):
        auth_service.register("test@mail.com", "123456", "Test")


def test_login_success(auth_service):
    auth_service.register("test@mail.com", "123456", "Test")
    result = auth_service.login("test@mail.com", "123456")

    assert "access_token" in result
    assert result["user_id"] == 1


def test_login_wrong_password(auth_service):
    auth_service.register("test@mail.com", "123456", "Test")

    with pytest.raises(Exception):
        auth_service.login("test@mail.com", "wrongpass")
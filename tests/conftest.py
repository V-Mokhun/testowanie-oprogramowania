import pytest

from app import create_app, db
from app.models import User
from config import Config


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    TESTING = True


@pytest.fixture(scope="session")
def app():
    app = create_app(TestConfig)
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def user(client):
    user = User(username="testuser", email="testuser@example.com")
    user.set_password("testpass")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def auth_headers(user: User):
    token = user.get_token()
    db.session.commit()
    return {"Authorization": f"Bearer {token}"}


def login_user_via_client(client, username, password):
    return client.post(
        "/auth/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


def is_logged_in(client):
    return ("Sign In" and "Redirecting...") not in client.get("/index").get_data(
        as_text=True
    )

import os
import sys
from datetime import datetime, timezone

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, Post


def seed_test_data(app=None):
    """Create test data for E2E tests."""
    from config import Config

    if app is None:

        class TestConfig(Config):
            SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
            WTF_CSRF_ENABLED = False
            TESTING = True

        app = create_app(TestConfig)

    with app.app_context():
        db.drop_all()
        db.create_all()

        testuser = User(username="testuser", email="testuser@example.com")
        testuser.set_password("password")
        testuser.about_me = "Test user bio"
        testuser.last_seen = datetime.now(timezone.utc)

        otheruser = User(username="otheruser", email="otheruser@example.com")
        otheruser.set_password("password")
        otheruser.about_me = "Other user bio"
        otheruser.last_seen = datetime.now(timezone.utc)

        thirduser = User(username="thirduser", email="thirduser@example.com")
        thirduser.set_password("password")
        thirduser.about_me = "Third user bio"
        thirduser.last_seen = datetime.now(timezone.utc)

        post1 = Post(body="Test post 1", author=testuser)
        post2 = Post(body="Test post 2", author=testuser)
        post3 = Post(body="Other user post", author=otheruser)
        post4 = Post(body="Third user post", author=thirduser)

        db.session.add(testuser)
        db.session.add(otheruser)
        db.session.add(thirduser)
        db.session.add(post1)
        db.session.add(post2)
        db.session.add(post3)
        db.session.add(post4)

        db.session.commit()


if __name__ == "__main__":
    seed_test_data()

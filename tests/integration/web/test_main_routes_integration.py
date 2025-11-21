import sqlalchemy as sa

from app import db
from app.models import Message, Post, User
from tests.conftest import login_user_via_client


def test_index_post(client, user):
    login_user_via_client(client, "testuser", "testpass")
    client.post("/index", data={"post": "hello"}, follow_redirects=False)

    post = db.session.scalar(sa.select(Post).where(Post.author == user))
    assert post.body == "hello"


def test_edit_profile_get_and_post(client, user):
    login_user_via_client(client, "testuser", "testpass")

    client.post(
        "/edit_profile",
        data={"username": "new", "about_me": "x"},
        follow_redirects=False,
    )

    user_updated = db.session.get(User, user.id)
    assert user_updated.username == "new"
    assert user_updated.about_me == "x"


def test_follow_and_unfollow(client, user):
    user2 = User(username="other", email="other@example.com")
    user2.set_password("testpass")
    db.session.add(user2)
    db.session.commit()

    login_user_via_client(client, "testuser", "testpass")
    client.post("/follow/other", follow_redirects=False)

    user_updated = db.session.get(User, user.id)
    assert user_updated.is_following(user2)

    client.post("/unfollow/other", follow_redirects=False)

    user_updated = db.session.get(User, user.id)
    assert not user_updated.is_following(user2)


def test_send_message(client, user):
    user2 = User(username="other", email="other@example.com")
    user2.set_password("testpass")
    db.session.add(user2)
    db.session.commit()

    login_user_via_client(client, "testuser", "testpass")
    client.post("/send_message/other", data={"message": "hi"}, follow_redirects=False)

    message = db.session.scalar(
        sa.select(Message).where(
            Message.sender_id == user.id, Message.recipient_id == user2.id
        )
    )
    assert message.body == "hi"

from app import db
from app.models import User
from app.main.forms import EditProfileForm, PostForm, MessageForm


def test_edit_profile_form_unique_username(app, client):
    user = User(username="taken", email="taken@example.com")
    user.set_password("password")
    db.session.add(user)
    db.session.commit()

    with client.application.test_request_context():
        f = EditProfileForm(original_username="orig")
        f.username.data = "taken"
        assert not f.validate()
        assert len(f.username.errors) > 0

        f2 = EditProfileForm(original_username="orig")
        f2.username.data = "orig"
        assert f2.validate()


def test_post_form_validator(app, client):
    with client.application.test_request_context():
        p = PostForm()
        p.post.data = "hello"
        assert p.validate()


def test_message_form_validator(app, client):
    with client.application.test_request_context():
        m = MessageForm()
        m.message.data = "hi"
        assert m.validate()

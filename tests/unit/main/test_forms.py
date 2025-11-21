import pytest


def test_edit_profile_form_unique_username(app, monkeypatch):
    from app.main.forms import EditProfileForm
    from app import db

    db.session.scalar.return_value = object()
    f = EditProfileForm(original_username="orig")
    f.username.data = "taken"
    with pytest.raises(Exception):
        f.validate_username(f.username)

    f2 = EditProfileForm(original_username="orig")
    f2.username.data = "orig"
    f2.validate_username(f2.username)


def test_post_and_message_form_validators(app):
    from app.main.forms import PostForm, MessageForm

    p = PostForm()
    p.post.data = "hello"
    assert p.validate()
    m = MessageForm()
    m.message.data = "hi"
    assert m.validate()

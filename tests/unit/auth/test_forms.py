from app import db
from app.models import User
from app.auth.forms import RegistrationForm, ResetPasswordForm, LoginForm, ResetPasswordRequestForm


def test_registration_form_unique_validators(app, client):
    user = User(username="u", email="u@example.com")
    user.set_password("password")
    db.session.add(user)
    db.session.commit()

    with client.application.test_request_context():
        form = RegistrationForm()
        form.username.data = "u"
        form.email.data = "u@example.com"
        form.password.data = "password"
        form.password2.data = "password"

        assert not form.validate()
        assert len(form.username.errors) > 0

        form2 = RegistrationForm()
        form2.username.data = "u2"
        form2.email.data = "u2@example.com"
        form2.password.data = "password"  
        form2.password2.data = "password"
        assert form2.validate()


def test_reset_password_form_validators(app, client):
    with client.application.test_request_context():
        f = ResetPasswordForm()
        f.password.data = "a"
        f.password2.data = "a"
        assert f.validate()

        f2 = ResetPasswordForm()
        f2.password.data = "a"
        f2.password2.data = "b"
        assert not f2.validate()


def test_login_form_requires_fields(app, client):
    with client.application.test_request_context():
        f = LoginForm()
        assert not f.validate()


def test_reset_password_request_form_email_validation(app, client):
    with client.application.test_request_context():
        f_ok = ResetPasswordRequestForm()
        f_ok.email.data = "user@example.com"
        assert f_ok.validate()

        f_bad = ResetPasswordRequestForm()
        f_bad.email.data = "not-an-email"
        assert not f_bad.validate()

import pytest


def test_registration_form_unique_validators(app, monkeypatch):
    from app.auth.forms import RegistrationForm
    from app import db

    db.session.scalar.return_value = object()
    form = RegistrationForm()
    form.username.data = "u"
    form.email.data = "u@example.com"
    with pytest.raises(Exception):
        form.validate_username(form.username)

    db.session.scalar.return_value = None
    form2 = RegistrationForm()
    form2.username.data = "u2"
    form2.email.data = "u2@example.com"
    form2.validate_username(form2.username)
    db.session.scalar.return_value = None
    form2.validate_email(form2.email)


def test_reset_password_form_validators(app):
    from app.auth.forms import ResetPasswordForm

    f = ResetPasswordForm()
    f.password.data = "a"
    f.password2.data = "a"
    assert f.validate()

    f2 = ResetPasswordForm()
    f2.password.data = "a"
    f2.password2.data = "b"
    assert not f2.validate()


def test_login_form_requires_fields(app):
    from app.auth.forms import LoginForm

    f = LoginForm()
    assert not f.validate()


def test_reset_password_request_form_email_validation(app):
    from app.auth.forms import ResetPasswordRequestForm

    f_ok = ResetPasswordRequestForm()
    f_ok.email.data = "user@example.com"
    assert f_ok.validate()

    f_bad = ResetPasswordRequestForm()
    f_bad.email.data = "not-an-email"
    assert not f_bad.validate()

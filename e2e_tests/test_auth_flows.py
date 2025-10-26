from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from conftest import login_user
import pytest


def test_login_page_renders_with_form_fields(browser, live_server, monkeypatch):
    """Test that login page renders with username, password, and remember_me fields."""
    browser.get(f"{live_server}/auth/login")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    assert browser.find_element(By.NAME, "username")
    assert browser.find_element(By.NAME, "password")
    assert browser.find_element(By.NAME, "remember_me")
    assert browser.find_element(
        By.CSS_SELECTOR, "input[type=submit], button[type=submit]"
    )

    assert "Sign In" in browser.page_source


def test_login_with_invalid_credentials_shows_error(browser, live_server):
    """Test that login with invalid credentials shows error flash message."""
    browser.get(f"{live_server}/auth/login")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    username_field = browser.find_element(By.NAME, "username")
    username_field.clear()
    username_field.send_keys("nonexistent")

    password_field = browser.find_element(By.NAME, "password")
    password_field.clear()
    password_field.send_keys("wrongpassword")

    submit_button = browser.find_element(
        By.CSS_SELECTOR, "input[type=submit], button[type=submit]"
    )
    submit_button.click()

    WebDriverWait(browser, 5).until(EC.url_contains("/auth/login"))

    assert "Invalid username or password" in browser.page_source


def test_logout_redirects_and_shows_login_link(browser, live_server, monkeypatch):
    """Test that logout redirects to index and navbar shows Login link."""
    login_user(browser, live_server)
    browser.get(f"{live_server}/auth/logout")

    WebDriverWait(browser, 5).until(EC.url_matches(r".*/?(index)?$"))

    browser.get(f"{live_server}/")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "nav"))
    )

    assert "Login" in browser.page_source


def test_registration_page_renders_with_form(browser, live_server, monkeypatch):
    """Test that registration page renders with username, email, password, password2 fields."""
    browser.get(f"{live_server}/auth/register")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    assert browser.find_element(By.NAME, "username")
    assert browser.find_element(By.NAME, "email")
    assert browser.find_element(By.NAME, "password")
    assert browser.find_element(By.NAME, "password2")
    assert browser.find_element(
        By.CSS_SELECTOR, "input[type=submit], button[type=submit]"
    )

    assert "Register" in browser.page_source


def test_register_with_valid_data_redirects_to_login(browser, live_server):
    """Test that registration with valid data redirects to login with success message."""

    browser.get(f"{live_server}/auth/register")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    browser.find_element(By.NAME, "username").send_keys("newuser")
    browser.find_element(By.NAME, "email").send_keys("newuser@example.com")
    browser.find_element(By.NAME, "password").send_keys("password123")
    browser.find_element(By.NAME, "password2").send_keys("password123")
    browser.find_element(
        By.CSS_SELECTOR, "input[type=submit], button[type=submit]"
    ).click()

    WebDriverWait(browser, 5).until(EC.url_contains("/auth/login"))

    assert "Congratulations, you are now a registered user!" in browser.page_source


def test_register_with_duplicate_username_shows_validation_error(browser, live_server):
    """Test that registration with duplicate username shows validation error."""

    browser.get(f"{live_server}/auth/register")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    browser.find_element(By.NAME, "username").send_keys(
        "testuser"
    )  # Use seeded username
    browser.find_element(By.NAME, "email").send_keys("newuser@example.com")
    browser.find_element(By.NAME, "password").send_keys("password123")
    browser.find_element(By.NAME, "password2").send_keys("password123")
    browser.find_element(
        By.CSS_SELECTOR, "input[type=submit], button[type=submit]"
    ).click()

    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    assert "Please use a different username." in browser.page_source


def test_password_reset_request_page_renders_and_accepts_email(
    browser, live_server, monkeypatch
):
    """Test that password reset request page renders and accepts email."""
    monkeypatch.setattr("app.auth.routes.send_password_reset_email", lambda user: None)

    browser.get(f"{live_server}/auth/reset_password_request")
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.NAME, "email")))

    assert browser.find_element(By.NAME, "email")
    assert browser.find_element(
        By.CSS_SELECTOR, "input[type=submit], button[type=submit]"
    )

    browser.find_element(By.NAME, "email").send_keys(
        "testuser@example.com"
    )  # Use seeded email
    browser.find_element(
        By.CSS_SELECTOR, "input[type=submit], button[type=submit]"
    ).click()

    WebDriverWait(browser, 5).until(EC.url_contains("/auth/login"))

    assert (
        "Check your email for the instructions to reset your password"
        in browser.page_source
    )


def test_password_reset_flow(browser, live_server):
    """Test password reset flow using the seeded testuser."""
    # Step 1: Request password reset for existing user
    browser.get(f"{live_server}/auth/reset_password_request")
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.NAME, "email")))

    browser.find_element(By.NAME, "email").send_keys("testuser@example.com")
    browser.find_element(
        By.CSS_SELECTOR, "input[type=submit], button[type=submit]"
    ).click()

    WebDriverWait(browser, 5).until(EC.url_contains("/auth/login"))
    assert (
        "Check your email for the instructions to reset your password"
        in browser.page_source
    )

    # Step 2: Generate a valid reset token for the existing user
    from app.models import User
    from app import create_app

    # Create app context to access the database
    app = create_app()
    with app.app_context():
        # Get the existing testuser
        user = User.query.filter_by(username="testuser").first()
        if not user:
            pytest.fail("Test user not found")
        # Generate a valid reset token
        reset_token = user.get_reset_password_token()

        # Step 3: Use the generated token to reset password
        browser.get(f"{live_server}/auth/reset_password/{reset_token}")
        WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )

        # Verify the reset password form is displayed
        assert browser.find_element(By.NAME, "password")
        assert browser.find_element(By.NAME, "password2")
        assert browser.find_element(
            By.CSS_SELECTOR, "input[type=submit], button[type=submit]"
        )

        # Submit new password
        browser.find_element(By.NAME, "password").send_keys("newtestpassword123")
        browser.find_element(By.NAME, "password2").send_keys("newtestpassword123")
        browser.find_element(
            By.CSS_SELECTOR, "input[type=submit], button[type=submit]"
        ).click()

        WebDriverWait(browser, 5).until(EC.url_contains("/auth/login"))
        assert "Your password has been reset." in browser.page_source

        # Step 4: Login with the new password
        WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )

        browser.find_element(By.NAME, "username").send_keys("testuser")
        browser.find_element(By.NAME, "password").send_keys("newtestpassword123")

        submit_button = browser.find_element(
            By.CSS_SELECTOR, "input[type=submit], button[type=submit]"
        )
        submit_button.click()

        WebDriverWait(browser, 5).until(EC.url_contains("/index"))
        assert "Hi, testuser!" in browser.page_source

        # Step 5: Verify old password no longer works
        browser.get(f"{live_server}/auth/logout")
        WebDriverWait(browser, 5).until(
            lambda driver: "/index" in driver.current_url
            or "/auth/login" in driver.current_url
        )

        browser.get(f"{live_server}/auth/login")
        WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )

        browser.find_element(By.NAME, "username").send_keys("testuser")
        browser.find_element(By.NAME, "password").send_keys("password")  # Old password
        browser.find_element(
            By.CSS_SELECTOR, "input[type=submit], button[type=submit]"
        ).click()

        # Should stay on login page with error
        WebDriverWait(browser, 5).until(EC.url_contains("/auth/login"))
        assert "Invalid username or password" in browser.page_source

        # Step 6: Verify new password works
        browser.find_element(By.NAME, "username").clear()
        browser.find_element(By.NAME, "password").clear()
        browser.find_element(By.NAME, "username").send_keys("testuser")
        browser.find_element(By.NAME, "password").send_keys(
            "newtestpassword123"
        )  # New password
        browser.find_element(
            By.CSS_SELECTOR, "input[type=submit], button[type=submit]"
        ).click()

        WebDriverWait(browser, 5).until(EC.url_contains("/index"))
        assert "Hi, testuser!" in browser.page_source

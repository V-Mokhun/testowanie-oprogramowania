from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from conftest import login_user
import pytest
from seed_data import SEEDED_USERS


def test_login(browser, live_server):
    login_user(browser, live_server)
    assert "Hi, testuser!" in browser.page_source


def test_login_invalid_credentials(browser, live_server):
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

    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    assert "Invalid username or password" in browser.page_source


def test_logout(browser, live_server):
    login_user(browser, live_server)
    browser.get(f"{live_server}/auth/logout")

    WebDriverWait(browser, 5).until(EC.url_contains("/auth/login"))

    browser.get(f"{live_server}/")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "nav"))
    )

    assert "Login" in browser.page_source


def test_register(browser, live_server):
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


def test_register_duplicate_username(browser, live_server):
    browser.get(f"{live_server}/auth/register")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    browser.find_element(By.NAME, "username").send_keys("testuser")
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


def test_password_reset_flow(browser, live_server, app_instance):
    browser.get(f"{live_server}/auth/reset_password_request")
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.NAME, "email")))

    browser.find_element(By.NAME, "email").send_keys(SEEDED_USERS["testuser"]["email"])
    browser.find_element(
        By.CSS_SELECTOR, "input[type=submit], button[type=submit]"
    ).click()

    WebDriverWait(browser, 5).until(EC.url_contains("/auth/login"))
    assert (
        "Check your email for the instructions to reset your password"
        in browser.page_source
    )

    from app.models import User
    from app import db

    with app_instance.app_context():
        user = db.session.scalar(
            db.select(User).where(User.username == SEEDED_USERS["testuser"]["username"])
        )
        if not user:
            pytest.fail("Test user not found")
        reset_token = user.get_reset_password_token()

        browser.get(f"{live_server}/auth/reset_password/{reset_token}")
        WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )

        assert browser.find_element(By.NAME, "password")
        assert browser.find_element(By.NAME, "password2")
        assert browser.find_element(
            By.CSS_SELECTOR, "input[type=submit], button[type=submit]"
        )

        browser.find_element(By.NAME, "password").send_keys("newtestpassword123")
        browser.find_element(By.NAME, "password2").send_keys("newtestpassword123")
        browser.find_element(
            By.CSS_SELECTOR, "input[type=submit], button[type=submit]"
        ).click()

        WebDriverWait(browser, 5).until(EC.url_contains("/auth/login"))
        assert "Your password has been reset." in browser.page_source

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

        browser.get(f"{live_server}/auth/logout")
        WebDriverWait(browser, 5).until(
            lambda driver: "/index" in driver.current_url
            or "/auth/login" in driver.current_url
        )

        browser.get(f"{live_server}/auth/login")
        WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )

        browser.find_element(By.NAME, "username").send_keys(
            SEEDED_USERS["testuser"]["username"]
        )
        browser.find_element(By.NAME, "password").send_keys(
            SEEDED_USERS["testuser"]["password"]
        )
        browser.find_element(
            By.CSS_SELECTOR, "input[type=submit], button[type=submit]"
        ).click()

        WebDriverWait(browser, 5).until(EC.url_contains("/auth/login"))
        WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".alert.alert-info"))
        )
        assert (
            "Invalid username or password"
            in browser.find_element(By.CSS_SELECTOR, ".alert.alert-info").text
        )

        browser.find_element(By.NAME, "username").clear()
        browser.find_element(By.NAME, "password").clear()
        browser.find_element(By.NAME, "username").send_keys(
            SEEDED_USERS["testuser"]["username"]
        )
        browser.find_element(By.NAME, "password").send_keys("newtestpassword123")
        browser.find_element(
            By.CSS_SELECTOR, "input[type=submit], button[type=submit]"
        ).click()

        WebDriverWait(browser, 5).until(EC.url_contains("/index"))
        assert "Hi, testuser!" in browser.page_source

"""
E2E-specific conftest that doesn't inherit global mocking.
This ensures E2E tests use real database with seeded data.
"""

import contextlib
import socket
import threading
import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@pytest.fixture(scope="session")
def app_instance():
    """Create a real Flask app instance for E2E tests."""
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from app import create_app
    from config import Config

    class E2EConfig(Config):
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        WTF_CSRF_ENABLED = False
        TESTING = True
        POSTS_PER_PAGE = 5

    app = create_app(E2EConfig)
    return app


@pytest.fixture(scope="session", autouse=True)
def seed_database(app_instance):
    """Seed the database with test data before running E2E tests."""
    from seed_data import seed_test_data

    seed_test_data(app_instance)
    yield


@pytest.fixture(scope="session")
def free_port():
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def live_server(app_instance, free_port):
    def run():
        app_instance.run(host="127.0.0.1", port=free_port, use_reloader=False)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    time.sleep(0.5)
    yield f"http://127.0.0.1:{free_port}"


@pytest.fixture(scope="function")
def browser():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")

    try:
        driver = webdriver.Chrome(options=options)
    except Exception:
        from webdriver_manager.chrome import ChromeDriverManager

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

    driver.set_window_size(1366, 900)
    yield driver
    driver.quit()


@pytest.fixture(autouse=True)
def setup_database_isolation(app_instance):
    """Set up database isolation for each test (like Jest beforeEach/afterEach)."""
    from app import db

    with app_instance.app_context():
        # Clear any existing transactions
        db.session.rollback()

        # Drop and recreate all tables to ensure clean state
        db.drop_all()
        db.create_all()

        # Seed fresh test data
        from seed_data import seed_test_data

        seed_test_data(app_instance)

    yield

    with app_instance.app_context():
        # Clean up after test
        db.session.rollback()
        db.drop_all()


def login_user(browser, live_server, username="testuser", password="password"):
    """Helper function to login a user with proper isolation."""
    try:
        browser.delete_all_cookies()
        browser.refresh()

        browser.get(f"{live_server}/auth/login")

        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )

        username_field = browser.find_element(By.NAME, "username")
        username_field.clear()
        username_field.send_keys(username)

        password_field = browser.find_element(By.NAME, "password")
        password_field.clear()
        password_field.send_keys(password)

        submit_button = browser.find_element(
            By.CSS_SELECTOR, "input[type=submit], button[type=submit]"
        )
        submit_button.click()

        WebDriverWait(browser, 10).until(
            lambda driver: (
                "/index" in driver.current_url or "Sign In" not in driver.page_source
            )
        )

    except Exception as e:
        print(f"❌ Login failed for {username}: {e}")
        browser.save_screenshot(f"login_failure_{username}.png")
        print(f"Current URL: {browser.current_url}")
        print(f"Page title: {browser.title}")
        raise


def create_post(browser, live_server, post_body="My first post"):
    """Helper function to create a post with proper isolation."""
    import time

    try:
        browser.get(f"{live_server}/index")

        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "form"))
        )

        post_field = browser.find_element(By.NAME, "post")

        post_field.clear()
        post_field.send_keys(post_body)

        submit_button = browser.find_element(
            By.CSS_SELECTOR, "input[type=submit], button[type=submit]"
        )

        submit_button.click()

        WebDriverWait(browser, 10).until(lambda driver: "/index" in driver.current_url)

        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(0.5)

        print(f"✅ Post '{post_body}' submitted successfully")

    except Exception as e:
        print(f"❌ Create post failed for {post_body}: {e}")
        browser.save_screenshot(f"create_post_failure_{post_body}.png")
        print(f"Current URL: {browser.current_url}")
        print(f"Page source snippet: {browser.page_source[:500]}...")
        raise

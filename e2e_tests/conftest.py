import contextlib
import socket
import threading
import time

import pytest
from seed_data import SEEDED_USERS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from werkzeug.serving import make_server

from app import create_app, db
from config import Config


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    POSTS_PER_PAGE = 5


@pytest.fixture(scope="session")
def app_instance():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="session")
def free_port():
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def live_server(app_instance, free_port):
    server = make_server("127.0.0.1", free_port, app_instance)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{free_port}"
    finally:
        server.shutdown()
        thread.join(timeout=2)


@pytest.fixture(scope="function")
def browser():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")

    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1366, 900)
    yield driver
    driver.quit()


@pytest.fixture(autouse=True)
def setup_database_isolation(app_instance):
    with app_instance.app_context():
        db.session.rollback()

        db.drop_all()
        db.create_all()

        from seed_data import seed_test_data

        seed_test_data(app_instance)

    yield

    with app_instance.app_context():
        db.session.rollback()
        db.drop_all()


def login_user(
    browser,
    live_server,
    username=SEEDED_USERS["testuser"]["username"],
    password=SEEDED_USERS["testuser"]["password"],
):
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


def create_post(browser, live_server, post_body="My first post"):
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

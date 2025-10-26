"""
Private messaging E2E tests.
Tests message sending, receiving, pagination, and UI updates.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from conftest import login_user
from seed_data import SEEDED_USERS


def test_send_message_page_renders_with_form(browser, live_server):
    """Test that send message page renders with form."""

    login_user(browser, live_server)

    browser.get(f"{live_server}/send_message/{SEEDED_USERS['otheruser']['username']}")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    message_field = browser.find_element(By.NAME, "message")
    assert message_field.is_displayed()

    submit_button = browser.find_element(By.CSS_SELECTOR, "#submit")
    assert submit_button.is_displayed()

    page_source = browser.page_source
    assert SEEDED_USERS["otheruser"]["username"] in page_source


def test_message_submission_shows_success_and_redirects(browser, live_server):
    login_user(browser, live_server)

    browser.get(f"{live_server}/send_message/{SEEDED_USERS['otheruser']['username']}")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "message"))
    )

    message_field = browser.find_element(By.NAME, "message")
    message_field.clear()
    message_field.send_keys("Hello, this is a test message!")

    submit_button = browser.find_element(By.CSS_SELECTOR, "#submit")
    submit_button.click()

    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    assert "Your message has been sent" in browser.page_source


def test_messages_page_lists_received_messages(browser, live_server):
    """Test that messages page loads correctly."""
    login_user(browser, live_server)

    browser.get(f"{live_server}/send_message/{SEEDED_USERS['otheruser']['username']}")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "message"))
    )

    message_field = browser.find_element(By.NAME, "message")
    message_field.clear()
    message_field.send_keys("Hello, this is a test message!")

    submit_button = browser.find_element(By.CSS_SELECTOR, "#submit")
    submit_button.click()

    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    assert f"/user/{SEEDED_USERS['otheruser']['username']}" in browser.current_url

    browser.get(f"{live_server}/auth/logout")
    WebDriverWait(browser, 5).until(EC.url_contains("/auth/login"))

    login_user(
        browser,
        live_server,
        username=SEEDED_USERS["otheruser"]["username"],
        password=SEEDED_USERS["otheruser"]["password"],
    )

    message_count_el = browser.find_element(By.CSS_SELECTOR, "#message_count")
    assert message_count_el.is_displayed()
    assert message_count_el.text == "1"

    browser.get(f"{live_server}/messages")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    assert "Hello, this is a test message!" in browser.page_source

    message_count_el = browser.find_element(By.CSS_SELECTOR, "#message_count")
    assert not message_count_el.is_displayed()


def test_send_message_to_nonexistent_user_shows_error(browser, live_server):
    """Test that sending message to nonexistent user shows error."""
    login_user(browser, live_server)

    browser.get(f"{live_server}/send_message/nonexistentuser")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    assert "Not Found" in browser.page_source


def test_message_form_validation_works(browser, live_server):
    login_user(browser, live_server)

    browser.get(f"{live_server}/send_message/{SEEDED_USERS['otheruser']['username']}")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "message"))
    )

    submit_button = browser.find_element(By.CSS_SELECTOR, "#submit")
    submit_button.click()

    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "message"))
    )

    assert "/send_message" in browser.current_url


def test_messages_page_requires_authentication(browser, live_server):
    """Test that messages page requires authentication."""
    browser.get(f"{live_server}/messages")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    assert "/auth/login" in browser.current_url


def test_send_message_page_requires_authentication(browser, live_server):
    """Test that send message page requires authentication."""
    browser.get(f"{live_server}/send_message/{SEEDED_USERS['otheruser']['username']}")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    assert "/auth/login" in browser.current_url

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from conftest import login_user
from seed_data import SEEDED_USERS


def test_send_message(browser, live_server):
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


def test_messages_page(browser, live_server):
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

    browser.get(f"{live_server}/auth/logout")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

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


def test_send_message_to_nonexistent_user(browser, live_server):
    login_user(browser, live_server)

    browser.get(f"{live_server}/send_message/nonexistentuser")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    assert "Not Found" in browser.page_source


def test_message_form(browser, live_server):
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

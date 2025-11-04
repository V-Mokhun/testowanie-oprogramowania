from conftest import login_user, create_post
from seed_data import SEEDED_USERS
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def test_index_renders_with_greeting_and_post_form(browser, live_server):
    login_user(browser, live_server)

    browser.get(f"{live_server}/index")
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
    page = browser.page_source
    assert "Hi, testuser!" in page

    assert browser.find_element(By.CSS_SELECTOR, "textarea")
    assert browser.find_element(
        By.CSS_SELECTOR, "input[type=submit], button[type=submit]"
    )


def test_create_post_via_form_shows_flash_and_post_appears(browser, live_server):
    login_user(browser, live_server)

    create_post(browser, live_server, post_body="My first post")

    assert "My first post" in browser.page_source


def test_post_form_validation_shows_error_for_empty_post(browser, live_server):
    login_user(browser, live_server)

    browser.get(f"{live_server}/index")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
    )
    browser.find_element(
        By.CSS_SELECTOR, "input[type=submit], button[type=submit]"
    ).click()
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
    )

    assert "Your post is now live!" not in browser.page_source


def test_explore_page_renders_with_posts(browser, live_server):
    login_user(browser, live_server)

    create_post(browser, live_server, post_body="explore_test_post")

    browser.get(f"{live_server}/explore")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    src = browser.page_source
    assert "explore_test_post" in src


def test_posts_display_avatar_username_timestamp_and_body(browser, live_server):
    login_user(
        browser,
        live_server,
        username=SEEDED_USERS["otheruser"]["username"],
        password=SEEDED_USERS["otheruser"]["password"],
    )

    create_post(browser, live_server, post_body="content body")

    browser.get(f"{live_server}/explore")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    assert browser.find_element(By.CSS_SELECTOR, "a[href*='/user/'] img")
    timestamp = browser.find_element(By.CSS_SELECTOR, "[data-timestamp]")
    assert timestamp.text == "a few seconds ago"
    assert browser.find_element(
        By.CSS_SELECTOR, f"a[href='/user/{SEEDED_USERS['otheruser']['username']}']"
    )
    assert "content body" in browser.page_source


def test_pagination_links_render_when_multiple_pages(browser, live_server):
    login_user(browser, live_server)

    create_post(browser, live_server, post_body="pagination_test_post")

    browser.get(f"{live_server}/explore")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    assert "pagination_test_post" in browser.page_source

    next_link = browser.find_element(By.PARTIAL_LINK_TEXT, "Older posts")
    assert "page=2" in next_link.get_attribute("href")
    prev_link = browser.find_element(By.PARTIAL_LINK_TEXT, "Newer posts")
    assert "None" in prev_link.get_attribute("href")

    browser.execute_script(
        "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });",
        next_link,
    )
    next_link.click()

    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    next_link = browser.find_element(By.PARTIAL_LINK_TEXT, "Older posts")
    prev_link = browser.find_element(By.PARTIAL_LINK_TEXT, "Newer posts")
    assert "None" in next_link.get_attribute("href")
    assert "/explore?page=1" in prev_link.get_attribute("href")

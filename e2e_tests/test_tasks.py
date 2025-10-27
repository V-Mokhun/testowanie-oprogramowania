"""
Background tasks E2E tests.
Tests task launching, progress tracking, and user feedback.
"""

import time

from conftest import login_user
from seed_data import SEEDED_USERS
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def test_export_posts_link_triggers_task_launch(browser, live_server):
    """Test that export posts link triggers task launch."""
    login_user(browser, live_server)

    browser.get(f"{live_server}/user/{SEEDED_USERS['testuser']['username']}")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    export_link = browser.find_element(By.LINK_TEXT, "Export your posts")
    assert export_link.is_displayed()
    assert export_link.is_enabled()

    export_link.click()

    WebDriverWait(browser, 10).until(
        lambda driver: f"/user/{SEEDED_USERS['testuser']['username']}"
        in driver.current_url
    )

    export_links = browser.find_elements(By.LINK_TEXT, "Export your posts")
    assert len(export_links) == 0, "Export link should disappear when task is running"

    assert "Exporting posts..." in browser.page_source


def test_task_progress_visibility_on_different_pages(browser, live_server):
    """Test that task progress is visible on different pages."""
    login_user(browser, live_server)

    browser.get(f"{live_server}/user/{SEEDED_USERS['testuser']['username']}")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    export_link = browser.find_element(By.LINK_TEXT, "Export your posts")
    export_link.click()

    time.sleep(2)

    browser.get(f"{live_server}/index")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    page_source = browser.page_source
    assert "Exporting posts" in page_source

    browser.get(f"{live_server}/explore")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    page_source = browser.page_source
    assert "Exporting posts" in page_source

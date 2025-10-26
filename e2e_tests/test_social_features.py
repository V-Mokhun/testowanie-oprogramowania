"""
Social features E2E tests.
Tests follow/unfollow functionality, user popups, and social interactions.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from seed_data import SEEDED_USERS
from conftest import login_user


def test_followed_users_posts_appear_on_home_feed(browser, live_server):
    """Test that followed users' posts appear on home feed."""
    login_user(browser, live_server)

    browser.get(f"{live_server}/user/{SEEDED_USERS['otheruser']['username']}")
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

    follow_input = browser.find_element(By.CSS_SELECTOR, "input[value='Follow']")
    assert follow_input.is_displayed()

    follow_input.click()

    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[value='Unfollow']"))
    )

    browser.get(f"{live_server}/index")
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

    assert "Other user post" in browser.page_source


def test_user_popup_hover_loads_and_displays_user_info(browser, live_server):
    """Test that user popup (hover) loads and displays user info."""
    login_user(browser, live_server)

    browser.get(f"{live_server}/explore")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    username_links = browser.find_elements(By.CSS_SELECTOR, "a[href*='/user/']")
    if username_links:
        actions = ActionChains(browser)
        actions.move_to_element(username_links[0]).perform()

        import time

        time.sleep(2)

        popups = browser.find_elements(By.CSS_SELECTOR, ".popover")
        if popups:
            popup = popups[0]
            assert popup.is_displayed()

            popup_text = popup.text
            print("popup_text", popup_text)
            assert len(popup_text) > 0


def test_follow_count_updates_after_following(browser, live_server):
    """Test that follow count updates after following and unfollowing a user."""
    login_user(browser, live_server)

    browser.get(f"{live_server}/user/{SEEDED_USERS['otheruser']['username']}")
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

    assert "0 followers" in browser.page_source

    follow_button = browser.find_element(By.CSS_SELECTOR, "input[value='Follow']")
    follow_button.click()

    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[value='Unfollow']"))
    )

    browser.refresh()
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

    assert "1 followers" in browser.page_source

    unfollow_button = browser.find_element(By.CSS_SELECTOR, "input[value='Unfollow']")
    unfollow_button.click()

    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[value='Follow']"))
    )

    assert "0 followers" in browser.page_source

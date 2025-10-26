"""
User profile E2E tests that work with seeded data.
These tests focus on the core functionality without complex mocking.
"""

from conftest import login_user
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seed_data import SEEDED_USERS


def test_edit_profile_page_prefills_current_data(browser, live_server):
    login_user(browser, live_server)

    browser.get(f"{live_server}/edit_profile")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    username_field = browser.find_element(By.NAME, "username")
    about_me_field = browser.find_element(By.NAME, "about_me")

    assert username_field.get_attribute("value") == SEEDED_USERS["testuser"]["username"]
    assert about_me_field.get_attribute("value") == SEEDED_USERS["testuser"]["about_me"]


def test_edit_profile_duplicate_username_shows_validation_error(
    browser, live_server, monkeypatch
):
    login_user(browser, live_server)

    browser.get(f"{live_server}/edit_profile")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    username_field = browser.find_element(By.NAME, "username")
    username_field.clear()
    username_field.send_keys(SEEDED_USERS["otheruser"]["username"])

    browser.find_element(By.CSS_SELECTOR, "#submit").click()

    # Wait for the form to reload with validation errors
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    # Look for the validation error in the invalid-feedback div
    error_div = browser.find_element(By.CSS_SELECTOR, ".invalid-feedback")
    assert "Please use a different username." in error_div.text


def test_user_profile_shows_appropriate_links_for_own_profile(browser, live_server):
    login_user(browser, live_server)

    browser.get(f"{live_server}/user/{SEEDED_USERS['testuser']['username']}")
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

    # "Send private message" link should NOT be present on own profile
    message_links = browser.find_elements(By.LINK_TEXT, "Send private message")
    assert len(message_links) == 0

    # Follow/Unfollow buttons should NOT be present on own profile
    follow_inputs = browser.find_elements(By.CSS_SELECTOR, "input[value='Follow']")
    assert len(follow_inputs) == 0
    unfollow_inputs = browser.find_elements(By.CSS_SELECTOR, "input[value='Unfollow']")
    assert len(unfollow_inputs) == 0

    export_link = browser.find_element(By.LINK_TEXT, "Export your posts")
    assert export_link.is_displayed()

    edit_link = browser.find_element(By.LINK_TEXT, "Edit your profile")
    assert edit_link.is_displayed()


def test_user_profile_page_renders_with_avatar_bio_and_counts(browser, live_server):
    login_user(browser, live_server)

    browser.get(f"{live_server}/user/{SEEDED_USERS['testuser']['username']}")
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

    assert SEEDED_USERS["testuser"]["username"] in browser.page_source

    assert SEEDED_USERS["testuser"]["about_me"] in browser.page_source

    assert browser.find_element(By.CSS_SELECTOR, "img")

    assert "0 followers" in browser.page_source and "0 following" in browser.page_source


def test_edit_profile_updates_data_and_shows_success(browser, live_server):
    """Test that edit profile updates data and shows success flash."""
    login_user(browser, live_server)

    browser.get(f"{live_server}/edit_profile")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    username_field = browser.find_element(By.NAME, "username")
    about_me_field = browser.find_element(By.NAME, "about_me")

    username_field.clear()
    username_field.send_keys("updateduser")
    about_me_field.clear()
    about_me_field.send_keys("Updated bio")

    browser.find_element(By.CSS_SELECTOR, "#submit").click()

    # Wait for the flash message to appear
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".alert.alert-info"))
    )

    assert "Your changes have been saved." in browser.page_source

    browser.get(f"{live_server}/user/updateduser")
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

    assert "updateduser" in browser.page_source
    assert "Updated bio" in browser.page_source

    browser.get(f"{live_server}/user/{SEEDED_USERS['testuser']['username']}")
    assert "Not Found" in browser.page_source


def test_user_profile_shows_links_for_other_users(browser, live_server):
    login_user(browser, live_server)

    browser.get(f"{live_server}/user/{SEEDED_USERS['otheruser']['username']}")
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

    message_link = browser.find_element(By.LINK_TEXT, "Send private message")
    assert message_link.is_displayed()
    assert (
        message_link.get_attribute("href")
        == f"{live_server}/send_message/{SEEDED_USERS['otheruser']['username']}"
    )

    # Initially, user should not be following, so Follow button should be present
    follow_input = browser.find_element(By.CSS_SELECTOR, "input[value='Follow']")
    assert follow_input.is_displayed()
    
    # Unfollow button should NOT be present when not following
    unfollow_inputs = browser.find_elements(By.CSS_SELECTOR, "input[value='Unfollow']")
    assert len(unfollow_inputs) == 0


def test_other_user_profile_shows_unfollow_button_when_following(
    browser, live_server, monkeypatch
):
    login_user(browser, live_server)

    browser.get(f"{live_server}/user/{SEEDED_USERS['otheruser']['username']}")
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

    # Initially should show Follow button, not Unfollow
    follow_input = browser.find_element(By.CSS_SELECTOR, "input[value='Follow']")
    assert follow_input.is_displayed()
    unfollow_inputs = browser.find_elements(By.CSS_SELECTOR, "input[value='Unfollow']")
    assert len(unfollow_inputs) == 0

    # Click Follow button
    follow_input.click()
    
    # Wait for the follow action to complete and page to reload
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[value='Unfollow']"))
    )
    
    # Check that success message appears
    assert (
        f"You are following {SEEDED_USERS['otheruser']['username']}!"
        in browser.page_source
    )
    
    # Now should show Unfollow button, not Follow
    unfollow_input = browser.find_element(By.CSS_SELECTOR, "input[value='Unfollow']")
    assert unfollow_input.is_displayed()
    follow_inputs = browser.find_elements(By.CSS_SELECTOR, "input[value='Follow']")
    assert len(follow_inputs) == 0

    # Click Unfollow button
    unfollow_input.click()
    
    # Wait for the unfollow action to complete and page to reload
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[value='Follow']"))
    )
    
    # Check that success message appears
    assert (
        f"You are not following {SEEDED_USERS['otheruser']['username']}."
        in browser.page_source
    )
    
    # Now should show Follow button again, not Unfollow
    follow_input = browser.find_element(By.CSS_SELECTOR, "input[value='Follow']")
    assert follow_input.is_displayed()
    unfollow_inputs = browser.find_elements(By.CSS_SELECTOR, "input[value='Unfollow']")
    assert len(unfollow_inputs) == 0

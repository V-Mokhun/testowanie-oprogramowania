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


def test_edit_profile_duplicate_username_shows_validation_error(browser, live_server):
    login_user(browser, live_server)

    browser.get(f"{live_server}/edit_profile")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    username_field = browser.find_element(By.NAME, "username")
    username_field.clear()
    username_field.send_keys(SEEDED_USERS["otheruser"]["username"])

    browser.find_element(By.CSS_SELECTOR, "#submit").click()

    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    error_div = browser.find_element(By.CSS_SELECTOR, ".invalid-feedback")
    assert "Please use a different username." in error_div.text


def test_user_profile_shows_appropriate_links_for_own_profile(browser, live_server):
    login_user(browser, live_server)

    browser.get(f"{live_server}/user/{SEEDED_USERS['testuser']['username']}")
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

    message_links = browser.find_elements(By.LINK_TEXT, "Send private message")
    assert len(message_links) == 0

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

    follow_input = browser.find_element(By.CSS_SELECTOR, "input[value='Follow']")
    assert follow_input.is_displayed()

    unfollow_inputs = browser.find_elements(By.CSS_SELECTOR, "input[value='Unfollow']")
    assert len(unfollow_inputs) == 0


def test_other_user_profile_shows_unfollow_button_when_following(browser, live_server):
    login_user(browser, live_server)

    browser.get(f"{live_server}/user/{SEEDED_USERS['otheruser']['username']}")
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

    follow_input = browser.find_element(By.CSS_SELECTOR, "input[value='Follow']")
    assert follow_input.is_displayed()
    unfollow_inputs = browser.find_elements(By.CSS_SELECTOR, "input[value='Unfollow']")
    assert len(unfollow_inputs) == 0

    follow_input.click()

    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[value='Unfollow']"))
    )

    assert (
        f"You are following {SEEDED_USERS['otheruser']['username']}!"
        in browser.page_source
    )

    unfollow_input = browser.find_element(By.CSS_SELECTOR, "input[value='Unfollow']")
    assert unfollow_input.is_displayed()
    follow_inputs = browser.find_elements(By.CSS_SELECTOR, "input[value='Follow']")
    assert len(follow_inputs) == 0

    unfollow_input.click()

    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[value='Follow']"))
    )

    assert (
        f"You are not following {SEEDED_USERS['otheruser']['username']}."
        in browser.page_source
    )

    follow_input = browser.find_element(By.CSS_SELECTOR, "input[value='Follow']")
    assert follow_input.is_displayed()
    unfollow_inputs = browser.find_elements(By.CSS_SELECTOR, "input[value='Unfollow']")
    assert len(unfollow_inputs) == 0

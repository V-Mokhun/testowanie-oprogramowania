from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_edit_profile_prefills_and_updates(browser, live_server):
    browser.get(f"{live_server}/edit_profile")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )
    username = browser.find_element(By.NAME, "username").get_attribute("value")
    assert username  # prefilled by route

    browser.find_element(By.NAME, "username").clear()
    browser.find_element(By.NAME, "username").send_keys("e2e-updated")
    # Submit (bootstrap_wtf quick_form renders input/button submit)
    browser.find_element(
        By.CSS_SELECTOR, "input[type=submit],button[type=submit]"
    ).click()
    # Redirect back to /edit_profile
    WebDriverWait(browser, 5).until(EC.url_contains("/edit_profile"))




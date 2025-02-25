from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image
import time
import random
import os
import io

def random_delay(min_time=2, max_time=4):
    """Introduce a random delay to mimic human behavior."""
    time.sleep(random.uniform(min_time, max_time))

def move_mouse_randomly(driver):
    """Move the mouse cursor randomly to mimic human behavior."""
    actions = ActionChains(driver)
    for _ in range(random.randint(5, 10)):
        actions.move_by_offset(random.randint(-10, 10), random.randint(-10, 10)).perform()
        random_delay(0.1, 0.3)

def login_to_instagram(driver, username, password):
    """Log in to Instagram."""
    driver.get("https://www.instagram.com/accounts/login/")
    random_delay(3, 6)

    username_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )
    username_field.send_keys(username)
    random_delay(1, 2)

    password_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "password"))
    )
    password_field.send_keys(password)
    random_delay(1, 2)

    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
    )
    move_mouse_randomly(driver)
    login_button.click()
    random_delay(5, 7)

def navigate_to_account(driver, target_username):
    """Navigate to the target Instagram account."""
    driver.get(f"https://www.instagram.com/{target_username}/")
    random_delay(5, 7)

    # Check if the account exists
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Page Not Found')]"))
        )
        print("The target account does not exist or is private.")
        return False
    except:
        print("Navigated to the target account successfully.")
        return True

def expand_bio_and_take_screenshot(driver, target_username):
    """Expand the 'More' button in the bio and take a screenshot."""
    try:
        # Wait for the bio section
        bio_section = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.-vDIg"))
        )

        # Check for the 'More' button using the provided XPath
        try:
            more_button = WebDriverWait(driver, 30).until(  # Increased wait time to 30 seconds
                EC.visibility_of_element_located((By.XPATH, "//button[contains(text(), 'more')]"))
            )
            if more_button.is_displayed():
                driver.execute_script("arguments[0].scrollIntoView(true);", more_button)
                move_mouse_randomly(driver)
                driver.execute_script("arguments[0].click();", more_button)
                random_delay(2, 3)
                print("'More' button clicked to expand the bio.")
            else:
                print("The 'More' button is not displayed. Bio might already be expanded.")
        except Exception:
            print("No 'More' button found. Bio might already be expanded.")

        # Take a screenshot of the bio section
        screenshot_path = f"info_screenshots/{target_username}_bio.png"
        bio_location = bio_section.location
        bio_size = bio_section.size

        # Capture full screenshot and crop
        screenshot = driver.get_screenshot_as_png()
        image = Image.open(io.BytesIO(screenshot))
        left = bio_location['x']
        top = bio_location['y']
        right = left + bio_size['width']
        bottom = top + bio_size['height']
        cropped_image = image.crop((left, top, right, bottom))
        cropped_image.save(screenshot_path)

        print(f"Bio section screenshot saved as {screenshot_path}.")
    except Exception as e:
        print(f"An error occurred while expanding bio or taking screenshot: {e}")

def main():
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Initialize WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        username = "jackpage217"
        password = "jack12#"
        target_username = "jackpage219"

        # Create screenshots directory
        os.makedirs('info_screenshots', exist_ok=True)

        # Log in to Instagram
        login_to_instagram(driver, username, password)

        # Navigate to the target account
        if navigate_to_account(driver, target_username):
            # Expand bio and take a screenshot
            expand_bio_and_take_screenshot(driver, target_username)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import time
import random
import os
import io

def random_delay(min_time=2, max_time=4):
    """Introduce a random delay to mimic human behavior."""
    time.sleep(random.uniform(min_time, max_time))

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

def open_followers_list(driver, target_username):
    """Open the followers list of the target account."""
    try:
        # Wait for the followers button to be clickable
        followers_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/followers/')]"))
        )
        followers_button.click()
        random_delay(3, 5)  # Wait for the followers modal to open
        print("Followers list opened.")
    except Exception as e:
        print(f"An error occurred while opening followers list: {e}")

def scroll_and_capture_followers(driver, target_username):
    """Scroll through the followers list and take screenshots of their names."""
    try:
        # Wait for the followers modal to be visible
        followers_modal = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="mount_0_0_I1"]/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/header/section[4]/div/span/span/div/span'))
        )

        # Locate the scrollable area for followers using the provided XPath
        scrollable_area = driver.find_element(By.XPATH, '/html/body/div[6]/div[2]/div/div/div[1]/div/div[2]/div/div/div/div/div[2]/div/div/div[3]')

        # Create a directory for screenshots
        os.makedirs('followers_screenshots', exist_ok=True)

        # Scroll and capture screenshots
        last_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_area)
        scroll_count = 0
        max_scrolls = 10  # Limit the number of scrolls to avoid infinite scrolling

        while scroll_count < max_scrolls:
            # Capture the current view
            screenshot_path = f"followers_screenshots/{target_username}_followers_scroll_{scroll_count + 1}.png"
            screenshot = driver.get_screenshot_as_png()
            image = Image.open(io.BytesIO(screenshot))
            image.save(screenshot_path)
            print(f"Captured screenshot of followers list: {screenshot_path}")

            # Scroll down using the scrollable area
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_area)
            random_delay(2, 3)  # Wait for the new followers to load

            # Check new height and compare
            new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_area)
            if new_height == last_height:
                print("No new content loaded. Stopping scroll.")
                break  # Exit if no new content is loaded
            last_height = new_height
            scroll_count += 1

    except Exception as e:
        print(f"An error occurred while scrolling through followers: {e}")

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
        target_username = "be_a_little_dramatic_"  # Target account

        # Log in to Instagram
        login_to_instagram(driver, username, password)

        # Navigate to the target account
        if navigate_to_account(driver, target_username):
            # Open the followers list
            open_followers_list(driver, target_username)
            # Scroll through followers and take screenshots
            scroll_and_capture_followers(driver, target_username)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
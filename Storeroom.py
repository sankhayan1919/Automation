from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import os
from PIL import Image
import io

def random_delay(min_time=2, max_time=4):
    time.sleep(random.uniform(min_time, max_time))

def wait_and_find_element(driver, by, value, timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except Exception as e:
        print(f"Error finding element {value}: {e}")
        return None

def login_to_instagram(driver, username, password):
    try:
        driver.get("https://www.instagram.com/accounts/login/")
        random_delay(3, 6)

        username_field = wait_and_find_element(driver, By.NAME, "username")
        if not username_field:
            return False
        username_field.send_keys(username)
        random_delay(1, 2)

        password_field = wait_and_find_element(driver, By.NAME, "password")
        if not password_field:
            return False
        password_field.send_keys(password)
        random_delay(1, 2)

        login_button = wait_and_find_element(driver, By.XPATH, "//button[@type='submit']")
        if not login_button:
            return False
        login_button.click()
        random_delay(5, 7)

        if wait_and_find_element(driver, By.XPATH, "//a[contains(@href, '/direct/inbox/')]"):
            print("Successfully logged in")
            return True
        return False

    except Exception as e:
        print(f"Login failed: {str(e)}")
        return False

def search_for_user(driver, target_username):
    try:
        driver.get(f"https://www.instagram.com/{target_username}/")
        random_delay(5, 8)
        WebDriverWait(driver, 15).until(EC.title_contains(target_username))
        print(f"Successfully navigated to {target_username}'s profile.")
        return True
    except Exception as e:
        print(f"An error occurred while searching for user: {e}")
        return False

def capture_post_screenshots(driver, target_username):
    """Capture screenshots of individual posts and save to a single file"""
    os.makedirs('screenshots', exist_ok=True)
    output_file = f"screenshots/{target_username}_posts.pdf"
    
    try:
        post_links = get_post_links(driver)
        if not post_links:
            print("No posts found.")
            return
        
        images = []
        first_image = None
        
        for index, post_link in enumerate(post_links, 1):
            try:
                driver.get(post_link)
                random_delay(3, 4)
                
                # Wait for post to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
                )
                
                # Additional delay to ensure media loads
                random_delay(2, 3)
                
                # Handle carousel posts
                slide_number = 1
                while True:
                    # Take screenshot of current slide
                    screenshot = driver.get_screenshot_as_png()
                    image = Image.open(io.BytesIO(screenshot))
                    
                    if first_image is None:
                        first_image = image
                    else:
                        images.append(image)
                    
                    print(f"Captured slide {slide_number} for post {index}/{len(post_links)}")
                    
                    # Check for next button
                    try:
                        next_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Next']")
                        if not next_button.is_displayed():
                            break
                        next_button.click()
                        random_delay(1, 2)
                        slide_number += 1
                    except:
                        # No next button found or not a carousel post
                        break
                
            except Exception as e:
                print(f"Error capturing post {index}: {e}")
                continue
        
        if first_image:
            first_image.save(
                output_file,
                "PDF",
                save_all=True,
                append_images=images[0:]
            )
            print(f"All screenshots saved to {output_file}")
        
    except Exception as e:
        print(f"Error during screenshot capture: {e}")

def get_post_links(driver):
    """Get all post links from the profile page"""
    post_links = []
    try:
        # Scroll the profile page to load all posts
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_attempts = 3  # Try scrolling a few times to ensure all posts are loaded
        
        while scroll_attempts < max_attempts:
            # Scroll down
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            random_delay(2, 3)
            
            # Calculate new scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                scroll_attempts += 1
            else:
                scroll_attempts = 0
                last_height = new_height

        # Get all post links after scrolling
        posts = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/p/']"))
        )
        # Remove any duplicate links
        post_links = list(dict.fromkeys([post.get_attribute('href') for post in posts]))
        print(f"Found {len(post_links)} posts")
        return post_links
    except Exception as e:
        print(f"Error getting post links: {e}")
        return []

# Browser setup
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)

try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_window_size(1920, 1080)
    driver.set_page_load_timeout(30)
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
except Exception as e:
    print(f"Error initializing WebDriver: {e}")
    exit(1)

# Main execution
username = "jackpage217"
password = "jack12#"

if login_to_instagram(driver, username, password):
    target_username = "jackpage219"  
    
    if search_for_user(driver, target_username):
        print("\nCapturing posts...")
        capture_post_screenshots(driver, target_username)
        print("\nAll captures completed!")
    else:
        print(f"User {target_username} not found!")

print("\nProcess finished. Closing browser...")
driver.quit() 
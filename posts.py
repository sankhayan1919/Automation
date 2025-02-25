from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
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

def get_post_links(driver):
    """Get all post links from the profile page"""
    post_links = set()  # Use set to prevent duplicates
    try:
        print("Loading posts...")
        last_count = 0
        no_new_posts_count = 0
        max_attempts = 30  # Increased maximum attempts
        
        while no_new_posts_count < 5:  # Try multiple times to ensure we've loaded all
            # Get current post links
            posts = driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
            current_links = {post.get_attribute('href') for post in posts}
            post_links.update(current_links)
            
            current_count = len(post_links)
            
            if current_count > last_count:
                print(f"Found {current_count} posts...")
                last_count = current_count
                no_new_posts_count = 0
            else:
                no_new_posts_count += 1
            
            # Scroll with different methods
            try:
                # Method 1: Normal scroll
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Method 2: Scroll with offset
                height = driver.execute_script("return document.body.scrollHeight")
                driver.execute_script(f"window.scrollTo(0, {height - 1000});")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Method 3: Scroll in smaller increments
                current_height = driver.execute_script("return window.pageYOffset;")
                driver.execute_script(f"window.scrollTo(0, {current_height + 500});")
                time.sleep(1)
                
            except Exception as e:
                print(f"Scroll error: {e}")
                continue
            
            print(f"Scroll attempt {no_new_posts_count}/5 - Current posts: {current_count}")
            
            # Additional check for loading indicator
            try:
                loading = driver.find_element(By.CSS_SELECTOR, "circle[role='progressbar']")
                if loading.is_displayed():
                    print("Loading more posts...")
                    time.sleep(3)
                    no_new_posts_count = 0  # Reset counter if still loading
            except:
                pass

        post_links = sorted(list(post_links))  # Convert to sorted list
        print(f"\nTotal unique posts found: {len(post_links)}")
        
        # Verify post count matches expected
        try:
            # Try to find post count from profile
            post_count_elem = driver.find_element(By.CSS_SELECTOR, "span._ac2a")
            expected_count = int(post_count_elem.text.replace(',', ''))
            print(f"Expected posts according to profile: {expected_count}")
            
            if len(post_links) < expected_count:
                print("Warning: Not all posts were loaded!")
                print(f"Found {len(post_links)} out of {expected_count} posts")
                
                # Try one more time with longer delays
                print("Attempting final load of remaining posts...")
                driver.execute_script("window.scrollTo(0, 0);")  # Scroll back to top
                time.sleep(3)
                
                for _ in range(5):  # Try 5 more times
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(4)  # Longer delay
                    
                    posts = driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
                    current_links = {post.get_attribute('href') for post in posts}
                    post_links.update(current_links)
                
                post_links = sorted(list(post_links))
                print(f"Final post count: {len(post_links)}")
            
        except Exception as e:
            print(f"Error verifying post count: {e}")
        
        return post_links
        
    except Exception as e:
        print(f"Error getting post links: {e}")
        return list(post_links)  # Return what we have so far

def capture_post_screenshots(driver, target_username):
    """Capture screenshots of individual posts and save to a single file"""
    os.makedirs('screenshots', exist_ok=True)
    output_file = f"screenshots/{target_username}_posts.pdf"
    
    try:
        # Set consistent window size
        driver.set_window_size(1920, 1080)
        
        # Get all post links first
        print("\nLoading all posts from profile...")
        post_links = get_post_links(driver)
        if not post_links:
            print("No posts found.")
            return
        
        images = []
        first_image = None
        processed_posts = set()
        failed_posts = []
        
        total_posts = len(post_links)
        print(f"\nStarting to capture {total_posts} posts...")
        
        for index, post_link in enumerate(post_links, 1):
            if post_link in processed_posts:
                continue
                
            try:
                print(f"\nProcessing post {index}/{total_posts}")
                print(f"URL: {post_link}")
                
                # Try loading the post multiple times if needed
                max_load_attempts = 3
                for attempt in range(max_load_attempts):
                    try:
                        driver.get(post_link)
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
                        )
                        break
                    except:
                        if attempt < max_load_attempts - 1:
                            print(f"Retrying post load... (attempt {attempt + 2}/{max_load_attempts})")
                            time.sleep(3)
                        else:
                            raise Exception("Failed to load post")
                
                # Additional delay to ensure media loads
                random_delay(2, 3)
                
                # Now handle carousel posts and take screenshots
                slide_number = 1
                while True:
                    # Scroll to the top of the post
                    driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(1)
                    
                    # Take screenshot of current slide with expanded replies
                    screenshot = driver.get_screenshot_as_png()
                    image = Image.open(io.BytesIO(screenshot))
                    
                    # Crop the image to remove 12% from the bottom, 25% from the left, and 10% from the right
                    width, height = image.size
                    left = width * 0.25
                    top = 0
                    right = width * 0.90
                    bottom = height * 0.88
                    cropped_image = image.crop((left, top, right, bottom))
                    
                    if first_image is None:
                        first_image = cropped_image
                    else:
                        images.append(cropped_image)
                    
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
                
                processed_posts.add(post_link)
                print(f"Successfully captured post {index}/{total_posts}")
                
            except Exception as e:
                print(f"Error processing post {index}: {e}")
                failed_posts.append(post_link)
                continue
        
        # Report on failed posts
        if failed_posts:
            print("\nFailed to capture the following posts:")
            for failed_post in failed_posts:
                print(failed_post)
        
        # Save to PDF
        if first_image:
            first_image.save(
                output_file,
                "PDF",
                save_all=True,
                append_images=images[0:]
            )
            print(f"\nAll screenshots saved to {output_file}")
            print(f"Successfully processed {len(processed_posts)} out of {total_posts} posts")
            print(f"Failed posts: {len(failed_posts)}")
        else:
            print("No posts were captured successfully")
        
    except Exception as e:
        print(f"Error during capture process: {e}")

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
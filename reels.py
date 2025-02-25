from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
import random
import os
from datetime import datetime
import requests
from selenium.webdriver.common.action_chains import ActionChains
import urllib.request
import json
import re
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import logging
from urllib.parse import unquote
import av
import subprocess
import shutil
from urllib.parse import urlparse
import m3u8
import cv2
import numpy as np
from PIL import ImageGrab
import pyautogui
import sys
import ffmpeg
 
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

        # Wait for the Instagram feed to load instead of checking for inbox
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "main[role='main']"))
            )
            print("Successfully logged in")
            return True
        except:
            print("Login verification failed")
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

def get_reel_links(driver):
    """Get all reel links from the profile page"""
    reel_links = []
    try:
        # Wait for profile page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "main[role='main']"))
        )
        random_delay(2, 3)

        # Find and click the reels tab
        try:
            reels_tab = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/reels/')]"))
            )
            reels_tab.click()
            random_delay(3, 4)
        except Exception as e:
            print(f"No reels tab found: {e}")
            return []

        # Wait for reels to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/reel/']"))
        )

        # Scroll to load all reels
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_attempts = 3
        
        while scroll_attempts < max_attempts:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            random_delay(2, 3)
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                scroll_attempts += 1
            else:
                scroll_attempts = 0
                last_height = new_height

        # Get all reel links
        reels = driver.find_elements(By.CSS_SELECTOR, "a[href*='/reel/']")
        reel_links = list(dict.fromkeys([reel.get_attribute('href') for reel in reels]))
        print(f"Found {len(reel_links)} reels")
        return reel_links
    except Exception as e:
        print(f"Error getting reel links: {e}")
        return []

def get_video_url(driver):
    """Extract the direct video URL from the page"""
    try:
        # Wait for video element and network activity
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "video"))
        )
        time.sleep(2)  # Wait for network requests
        
        # Method 1: Try to get from video element directly
        try:
            video_element = driver.find_element(By.TAG_NAME, "video")
            video_url = video_element.get_attribute('src')
            if video_url and not video_url.startswith('blob:'):
                logger.info(f"Found video URL from video element: {video_url[:100]}...")
                return video_url
        except Exception as e:
            logger.info(f"Method 1 failed: {e}")

        # Method 2: Parse page source
        page_source = driver.page_source
        patterns = [
            r'"video_url":"([^"]+)"',
            r'"playbackUrl":"([^"]+)"',
            r'"contentUrl":"([^"]+)"',
            r'"video_versions":\[{"type":\d+,"url":"([^"]+)"'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, page_source)
            if matches:
                video_url = matches[0].replace('\\u0026', '&')
                video_url = unquote(video_url)
                logger.info(f"Found video URL in page source: {video_url[:100]}...")
                return video_url

        # Method 3: Use performance logs to find video URL
        logs = driver.get_log('performance')
        for log in logs:
            log_message = json.loads(log['message'])
            message = log_message['message']
            if message['method'] == 'Network.responseReceived':
                url = message['params']['response']['url']
                if 'video' in url:
                    logger.info(f"Found video URL in performance logs: {url[:100]}...")
                    return url

        return None
    except Exception as e:
        logger.error(f"Error extracting video URL: {e}")
        return None

def download_reel(driver, target_username, reel_number):
    """Download reel with audio"""
    try:
        # Create reels directory
        reels_dir = os.path.join('screenshots', 'reels')
        os.makedirs(reels_dir, exist_ok=True)
        
        # Get video URL
        video_url = get_video_url(driver)
        if not video_url:
            logger.error(f"Could not find video URL for reel {reel_number}")
            return False
            
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(reels_dir, f"{target_username}_reel_{reel_number}_{timestamp}.mp4")
        
        # Set up headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'identity;q=1, *;q=0',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.instagram.com/',
            'Origin': 'https://www.instagram.com',
            'Connection': 'keep-alive'
        }
        
        # Download video
        try:
            response = requests.get(video_url, headers=headers, stream=True, timeout=30)
            
            if response.status_code == 200:
                # Download the video
                temp_path = os.path.join(reels_dir, f"{target_username}_reel_{reel_number}_{timestamp}.tmp")
                with open(temp_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Convert to mp4 using ffmpeg-python
                try:
                    ffmpeg.input(temp_path).output(output_path).run(overwrite_output=True)
                    os.remove(temp_path)
                    logger.info(f"Successfully downloaded reel {reel_number}")
                    return True
                except Exception as e:
                    logger.error(f"Error converting video: {e}")
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    return False
            else:
                logger.error(f"Failed to download: Status code {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error during download: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error downloading reel {reel_number}: {e}")
        return False

def expand_view_replies(driver):
    """Expand all 'View replies' buttons in comments"""
    try:
        # Scroll to load all comments first
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll down
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for content to load
            
            # Calculate new scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # Find and click all "View replies" buttons
        while True:
            try:
                view_replies_buttons = driver.find_elements(By.XPATH, "//span[contains(text(), 'View replies')]")
                if not view_replies_buttons:
                    break
                    
                for button in view_replies_buttons:
                    try:
                        # Scroll button into view
                        driver.execute_script("arguments[0].scrollIntoView(true);", button)
                        time.sleep(1)  # Wait for smooth scrolling
                        
                        # Click using JavaScript for better reliability
                        driver.execute_script("arguments[0].click();", button)
                        logger.info("Clicked 'View replies' button")
                        time.sleep(1)  # Wait for replies to load
                    except Exception as e:
                        logger.error(f"Error clicking individual button: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"Error finding View replies buttons: {e}")
                break
        
        # Take screenshot after expanding all replies
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_dir = os.path.join('screenshots', 'comments')
        os.makedirs(screenshot_dir, exist_ok=True)
        
        # Take full page screenshot
        total_height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(1920, total_height)
        
        screenshot_path = os.path.join(screenshot_dir, f"comments_expanded_{timestamp}.png")
        driver.save_screenshot(screenshot_path)
        logger.info(f"Saved expanded comments screenshot to {screenshot_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error expanding replies: {e}")
        return False

def capture_reels(driver, target_username):
    """Download all reels from the profile"""
    try:
        reel_links = get_reel_links(driver)
        if not reel_links:
            logger.info("No reels found.")
            return
        
        logger.info(f"Found {len(reel_links)} reels")
        
        for index, reel_link in enumerate(reel_links, 1):
            try:
                logger.info(f"\nProcessing reel {index}/{len(reel_links)}")
                driver.get(reel_link)
                
                # Wait for page load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "video"))
                )
                
                # Download the reel
                success = download_reel(driver, target_username, index)
                if not success:
                    logger.error(f"Failed to capture reel {index}")
                
                # Expand and capture comments
                logger.info("Expanding comment replies...")
                expand_view_replies(driver)
                
                random_delay(2, 3)
                
            except Exception as e:
                logger.error(f"Error processing reel {index}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error during reel capture: {e}")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modified browser setup
def setup_driver():
    try:
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
        
        # Add performance logging
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_window_size(1920, 1080)
        driver.set_page_load_timeout(30)
        
        # Enable network interception
        driver.execute_cdp_cmd('Network.enable', {})
        driver.execute_cdp_cmd('Network.setBypassServiceWorker', {'bypass': True})
        
        return driver
    except Exception as e:
        logger.error(f"Error initializing WebDriver: {e}")
        return None

# Main execution
if __name__ == "__main__":
    driver = setup_driver()
    if not driver:
        exit(1)

    try:
        username = "jackpage219"
        password = "jack12#"
        
        if login_to_instagram(driver, username, password):
            target_username = "blackjack2365"
            
            if search_for_user(driver, target_username):
                logger.info("\nCapturing reels...")
                capture_reels(driver, target_username)
                logger.info("\nAll captures completed!")
            else:
                logger.error(f"User {target_username} not found!")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        logger.info("\nProcess finished. Closing browser...")
        driver.quit()

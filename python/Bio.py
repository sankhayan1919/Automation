from playwright.sync_api import sync_playwright
import time
import random
import os

def random_delay(min_time=2, max_time=4):
    """Introduce a random delay to mimic human behavior."""
    time.sleep(random.uniform(min_time, max_time))

def login_to_instagram(page, username, password):
    """Log in to Instagram."""
    page.goto("https://www.instagram.com/accounts/login/")
    random_delay(3, 6)

    # Fill username
    page.fill("input[name='username']", username)
    random_delay(1, 2)

    # Fill password
    page.fill("input[name='password']", password)
    random_delay(1, 2)

    # Click login button
    page.click("button[type='submit']")
    random_delay(5, 7)

def navigate_to_account(page, target_username):
    """Navigate to the target Instagram account."""
    page.goto(f"https://www.instagram.com/{target_username}/")
    random_delay(5, 7)

    # Check if the account exists
    try:
        if page.locator("h1:has-text('Page Not Found')").is_visible(timeout=10000):
            print("The target account does not exist or is private.")
            return False
        print("Navigated to the target account successfully.")
        return True
    except:
        print("Navigated to the target account successfully.")
        return True

def take_bio_screenshot(page, target_username):
    """Take a screenshot of the bio section."""
    try:
        # Wait for the bio section
        bio_section = page.locator("div.x1iyjqo2").first
        bio_section.wait_for(state="visible", timeout=30000)

        # Take screenshot
        random_delay(2, 3)
        screenshot_path = f"screenshots/{target_username}_bio.png"
        
        # Take screenshot of the bio section
        bio_section.screenshot(path=screenshot_path)
        print(f"Bio section screenshot saved as {screenshot_path}.")

    except Exception as e:
        print(f"An error occurred while taking screenshot: {e}")

def main():
    with sync_playwright() as p:
        # Launch browser with specific options
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--start-maximized',
                '--kiosk',
                '--disable-infobars',
                '--disable-notifications'
            ]
        )
        
        # Create a new context with maximum viewport size
        context = browser.new_context(
            viewport=None,  # Removes viewport limitations
            no_viewport=True,  # Ensures true fullscreen
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        
        # Create a new page
        page = context.new_page()
        
        try:
            # Set window to fullscreen mode
            page.bring_to_front()
            page.keyboard.press("F11")
            random_delay(1, 2)
            
            username = "jackpage219"
            password = "jack12#"
            target_username = "jackpage217"

            # Create screenshots directory
            os.makedirs('screenshots', exist_ok=True)

            # Log in to Instagram
            login_to_instagram(page, username, password)

            # Navigate to the target account
            if navigate_to_account(page, target_username):
                # Take bio screenshot
                take_bio_screenshot(page, target_username)

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # Exit fullscreen before closing
            try:
                page.keyboard.press("F11")
                random_delay(1, 2)
            except:
                pass
            context.close()
            browser.close()

if __name__ == "__main__":
    main()

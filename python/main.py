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

    # Handle potential save login info popup
    try:
        save_info_button = page.locator("button:has-text('Save Info')").first
        if save_info_button.is_visible(timeout=5000):
            save_info_button.click()
            random_delay(2, 3)
    except:
        pass

    # Handle potential turn on notifications popup
    try:
        not_now_button = page.locator("button:has-text('Not Now')").first
        if not_now_button.is_visible(timeout=5000):
            not_now_button.click()
            random_delay(2, 3)
    except:
        pass

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

def open_expanded_followers_list(page, target_username):
    """Open followers list in full-width view showing 15-20 followers per screen"""
    try:
        # Store original viewport size
        original_viewport = page.viewport_size or {"width": 1280, "height": 720}
        
        # Set temporary ultra-wide viewport
        page.set_viewport_size({"width": 2000, "height": 1200})
        random_delay(1, 2)
        
        # Open followers list with precise click
        followers_button = page.locator("a[href$='/followers/'] >> visible=true").first
        followers_button.scroll_into_view_if_needed()
        page.mouse.click(
            followers_button.bounding_box()['x'] + 10,
            followers_button.bounding_box()['y'] + 10
        )
        random_delay(3, 5)
        
        # Expand dialog using CSS injection
        page.evaluate("""() => {
            const dialog = document.querySelector("div[role='dialog'][aria-label='Followers']");
            if (dialog) {
                // Remove size constraints
                dialog.style.width = '95vw !important';
                dialog.style.height = '85vh !important';
                dialog.style.maxWidth = 'none !important';
                dialog.style.maxHeight = 'none !important';
                dialog.style.left = '2.5% !important';
                dialog.style.top = '7.5% !important';
                
                // Expand inner container
                const listContainer = dialog.querySelector('div[style*="overflow-y: auto"]');
                if (listContainer) {
                    listContainer.style.height = '75vh !important';
                    listContainer.style.minHeight = '600px !important';
                }
            }
        }""")
        
        # Force UI refresh
        page.mouse.move(500, 500)
        page.mouse.wheel(0, 200)
        random_delay(2, 3)
        
        # Take screenshot of the followers list
        capture_followers_screenshot(page, target_username)
        
        # Restore original viewport
        page.set_viewport_size(original_viewport)
        
        print("Followers list opened in expanded view")
        return True
        
    except Exception as e:
        print(f"Failed to open expanded followers list: {e}")
        return False

def capture_followers_screenshot(page, target_username):
    """Capture screenshot of the followers list"""
    try:
        # Wait for followers dialog
        dialog = page.locator("div[role='dialog']").first
        dialog.wait_for(state="visible", timeout=30000)
        
        # Get dialog dimensions
        box = dialog.bounding_box()
        
        # Calculate screenshot area (dialog + 10% padding)
        screenshot_options = {
            'path': f'screenshots/{target_username}_followers_list.png',
            'clip': {
                'x': box['x'],
                'y': box['y'],
                'width': box['width'],
                'height': box['height']
            },
            'scale': 'css'
        }
        
        # Capture screenshot
        page.screenshot(**screenshot_options)
        print(f"Saved followers list screenshot: {screenshot_options['path']}")
        
    except Exception as e:
        print(f"Error capturing followers screenshot: {e}")

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
            target_username = "jackpage217"  # Target account

            # Create screenshots directory
            os.makedirs('screenshots', exist_ok=True)

            # Log in to Instagram
            login_to_instagram(page, username, password)

            # Navigate to the target account
            if navigate_to_account(page, target_username):
                open_expanded_followers_list(page, target_username)
                    
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
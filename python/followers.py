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

def get_followers_list(page, target_username):
    """Extract visible follower usernames without scrolling"""
    try:
        # Wait for followers dialog
        dialog = page.locator("div[role='dialog']").first
        dialog.wait_for(state="visible", timeout=60000)
        
        # Extract visible followers
        followers = dialog.locator("a[href^='/']:not([href*='explore'])")
        count = followers.count()
        
        usernames = []
        for i in range(count):
            user_element = followers.nth(i)
            href = user_element.get_attribute("href")
            if href:
                username = href.split("/")[-2]
                if username and username != "accounts":
                    usernames.append(username)
        
        # Remove duplicates
        return list(dict.fromkeys(usernames))

    except Exception as e:
        print(f"Error extracting followers: {e}")
        return []

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

def capture_collective_follower_screenshots(page, target_username, group_size=6):
    """Capture collective screenshots of visible followers in groups"""
    try:
        # Wait for followers dialog
        dialog = page.locator("div[role='dialog']").first
        dialog.wait_for(state="visible", timeout=50000)
        
        # Get all visible followers
        followers = dialog.locator("a[href^='/']:not([href*='explore'])")
        count = followers.count()
        
        
        # Loop through followers in groups
        for i in range(0, count, group_size):
            # Create a list to hold the bounding boxes of the followers in the current group
            boxes = []
            for j in range(group_size):
                if i + j < count:  # Ensure we don't go out of bounds
                    user_element = followers.nth(i + j)
                    user_element.scroll_into_view_if_needed()  # Ensure the follower is in view
                    box = user_element.bounding_box()
                    boxes.append(box)
            
            # Calculate the collective bounding box
            if boxes:
                collective_x = min(box['x'] for box in boxes) - 10  # Add some padding
                collective_y = min(box['y'] for box in boxes) - 10  # Add some padding
                collective_width = max(box['x'] + box['width'] for box in boxes) - collective_x + 20  # Add some padding
                collective_height = max(box['y'] + box['height'] for box in boxes) - collective_y + 20  # Add some padding
                
                # Screenshot options for the collective group
                screenshot_options = {
                    'path': f'followers_screenshots/{target_username}followers{i // group_size + 1}.png',
                    'clip': {
                        'x': collective_x,
                        'y': collective_y,
                        'width': collective_width,
                        'height': collective_height
                    },
                    'scale': 'css'
                }
                
                # Capture screenshot of the collective followers
                page.screenshot(**screenshot_options)
                print(f"Saved collective screenshot of followers {i + 1} to {min(i + group_size, count)}: {screenshot_options['path']}")
        
    except Exception as e:
        print(f"Error capturing collective follower screenshots: {e}")

def capture_followers_screenshots(page, target_username):
    """Capture screenshots of followers in groups of 5"""
    try:
        # Wait for followers dialog
        dialog = page.locator("div[role='dialog']").first
        dialog.wait_for(state="visible", timeout=30000)
        
        # Create screenshots directory
        os.makedirs('screenshots', exist_ok=True)
        
        group_count = 0
        captured_followers = set()

        while True:
            # Get visible followers
            followers = dialog.locator("a[href^='/']:not([href*='explore'])")
            count = followers.count()
            
            current_group = []
            for i in range(count):
                if len(current_group) >= 5:
                    break
                    
                user_element = followers.nth(i)
                href = user_element.get_attribute("href")
                username = href.split("/")[-2]
                
                if username not in captured_followers:
                    current_group.append(user_element)
                    captured_followers.add(username)

            # Take screenshot of group
            if len(current_group) == 5:
                group_count += 1
                boxes = [user.bounding_box() for user in current_group]
                
                # Calculate group dimensions
                min_x = min(box['x'] for box in boxes) - 10
                min_y = min(box['y'] for box in boxes) - 10
                max_x = max(box['x'] + box['width'] for box in boxes) + 10
                max_y = max(box['y'] + box['height'] for box in boxes) + 10
                
                page.screenshot(
                    path=f'screenshots/{target_username}group{group_count}.png',
                    clip={
                        'x': min_x,
                        'y': min_y,
                        'width': max_x - min_x,
                        'height': max_y - min_y
                    }
                )
                print(f"Captured group {group_count}")

                # Scroll down
                page.mouse.wheel(0, 300)
                time.sleep(2)  # Wait for new followers to load
            else:
                break  # Exit if no new followers found

    except Exception as e:
        print(f"Error capturing followers screenshots: {e}")

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
                if open_expanded_followers_list(page, target_username):
                    capture_followers_screenshots(page, target_username)
                    
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
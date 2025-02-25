from playwright.sync_api import sync_playwright
import time
import random
import os
from datetime import datetime

def random_delay(min_time=2, max_time=4):
    """Introduce a random delay to mimic human behavior."""
    time.sleep(random.uniform(min_time, max_time))

def login_to_instagram(page, username="jackpage217", password="jack12#"):
    """Log in to Instagram."""
    try:
        page.goto("https://www.instagram.com/accounts/login/")
        random_delay(3, 6)

        page.fill("input[name='username']", username)
        random_delay(1, 2)

        page.fill("input[name='password']", password)
        random_delay(1, 2)

        page.click("button[type='submit']")
        random_delay(5, 7)
        print("Successfully logged in to Instagram")
    except Exception as e:
        print(f"Error during login: {e}")

def navigate_to_tagged(page, target_username="sadhukhansankhayan"):
    """Navigate to the target account's tagged posts."""
    try:
        # First navigate to profile
        page.goto(f"https://www.instagram.com/{target_username}/")
        random_delay(5, 7)
        print(f"Navigated to {target_username}'s profile")

        # Wait for profile to load completely
        page.wait_for_load_state("networkidle")
        random_delay(5, 7)

        # Click on tagged tab using multiple possible selectors
        tagged_selectors = [
            "//a[contains(@href, '/tagged/')]",
            "//a[contains(text(), 'Tagged')]",
            "//div[@role='tablist']//a[contains(@href, '/tagged')]"
        ]

        for selector in tagged_selectors:
            try:
                # Wait for the selector to be visible
                page.wait_for_selector(f"xpath={selector}", timeout=10000)
                element = page.locator(f"xpath={selector}").first
                if element.is_visible():
                    element.click()
                    print("Clicked on Tagged tab")
                    random_delay(5, 7)
                    return True
            except Exception:
                continue

        print("Could not click Tagged tab, trying direct URL...")
        # If clicking failed, try direct navigation
        page.goto(f"https://www.instagram.com/{target_username}/tagged/")
        random_delay(5, 7)
        return True

    except Exception as e:
        print(f"Error navigating to tagged posts: {e}")
        return False

def get_tagged_post_links(page):
    """Get all tagged post links from the profile page."""
    post_links = set()  # Using set to avoid duplicates
    try:
        print("Collecting all tagged post links...")
        
        # Scroll to load all posts
        last_height = page.evaluate("document.body.scrollHeight")
        scroll_attempts = 0
        max_attempts = 3  # Try scrolling a few times to ensure all posts are loaded
        
        while scroll_attempts < max_attempts:
            # Scroll down
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            random_delay(2, 3)
            
            # Get all post links in current view
            posts = page.locator("a[href*='/p/']").all()
            for post in posts:
                href = post.get_attribute('href')
                if href:
                    post_links.add(href)

            # Calculate new scroll height
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                scroll_attempts += 1
            else:
                scroll_attempts = 0
                last_height = new_height

        post_links = list(post_links)  # Convert set to list
        print(f"Found {len(post_links)} unique tagged posts")
        return post_links
        
    except Exception as e:
        print(f"Error getting post links: {e}")
        return []

def capture_individual_tagged_posts(page):
    """Open and capture each tagged post individually."""
    try:
        # Create directory for screenshots
        screenshots_dir = "tagged_posts_individual"
        os.makedirs(screenshots_dir, exist_ok=True)
        
        # Get all post links first
        post_links = get_tagged_post_links(page)
        
        if not post_links:
            print("No tagged posts found")
            return
        
        # Process each post
        for index, post_url in enumerate(post_links, 1):
            try:
                print(f"\nProcessing post {index}/{len(post_links)}: {post_url}")
                
                # Ensure the URL is absolute
                if not post_url.startswith("http"):
                    post_url = f"https://www.instagram.com{post_url}"
                
                # Navigate to the post
                page.goto(post_url)  # Ensure this is a full URL
                page.wait_for_load_state("networkidle")
                random_delay(3, 5)
                
                # Wait for the post content to load
                post_content_selectors = [
                    "//article[contains(@class, '_aatb')]",
                    "//article[contains(@role, 'presentation')]",
                    "//div[contains(@class, '_aagv')]"
                ]
                
                for selector in post_content_selectors:
                    try:
                        page.wait_for_selector(f"xpath={selector}", timeout=10000)
                        break
                    except Exception:
                        continue
                
                # Wait for images/videos to load
                random_delay(2, 3)
                
                # Take screenshot of the post
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = os.path.join(screenshots_dir, f"post_{index:03d}_{timestamp}.png")
                
                # Take screenshot
                page.screenshot(path=screenshot_path)
                print(f"Captured post {index}/{len(post_links)}")
                
            except Exception as e:
                print(f"Error processing post {index}: {e}")
                continue
            
            random_delay(2, 3)
        
        print(f"\nFinished processing all posts")
        print(f"Total posts captured: {len(post_links)}")

    except Exception as e:
        print(f"Error in capture_individual_tagged_posts: {e}")

def main():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )
        
        # Create context with full viewport
        context = browser.new_context(
            viewport=None,
            no_viewport=True
        )
        
        page = context.new_page()
        
        try:
            # Go to blank page first
            page.goto("about:blank")
            
            # Enter full screen mode
            page.evaluate("""() => {
                document.documentElement.requestFullscreen()
                    .catch(err => console.log('Fullscreen request failed'));
                
                // Maximize window
                window.moveTo(0, 0);
                window.resizeTo(
                    window.screen.availWidth,
                    window.screen.availHeight
                );
            }""")
            
            random_delay(1, 2)

            # Execute the scraping process
            login_to_instagram(page)
            if navigate_to_tagged(page):
                capture_individual_tagged_posts(page)
            else:
                print("Failed to navigate to tagged posts")

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    main()
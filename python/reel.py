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

def navigate_to_reels(page, target_username="blackjack2365"):
    """Navigate to the target account's reels tab."""
    try:
        # Navigate to target profile
        page.goto(f"https://www.instagram.com/{target_username}/")
        random_delay(5, 7)
        print(f"Navigated to {target_username}'s profile")

        # Wait for profile page to load completely
        page.wait_for_load_state("networkidle")
        random_delay(3, 5)

        # Try multiple selectors for Reels tab
        reels_selectors = [
            "a[href*='/reels/']",
            "a:has-text('Reels')",
            "//a[contains(@href, '/reels')]",
            "//a[contains(text(), 'Reels')]"
        ]

        for selector in reels_selectors:
            try:
                if page.locator(selector).count() > 0:
                    page.click(selector)
                    print("Clicked Reels tab")
                    random_delay(5, 7)
                    
                    # Verify we're on the reels page
                    if "/reels" in page.url:
                        print("Successfully navigated to reels section")
                        return True
                    break
            except Exception:
                continue

        # If we couldn't click the Reels tab, try direct URL
        page.goto(f"https://www.instagram.com/{target_username}/reels/")
        random_delay(5, 7)
        
        # Verify we reached the reels page
        if "/reels" in page.url:
            print("Successfully navigated to reels section using direct URL")
            return True
            
        print("Failed to navigate to reels section")
        return False

    except Exception as e:
        print(f"Error navigating to reels: {e}")
        return False

def record_and_save_reels(page):
    """Record and save all reels from the profile."""
    try:
        # Create directory for reels if it doesn't exist
        reels_dir = "reels"
        os.makedirs(reels_dir, exist_ok=True)

        # Wait for reels to load and find all reel links
        print("Looking for reels...")
        
        # Try multiple selectors to find reels
        reel_selectors = [
            "//div[@role='tabpanel']//a[contains(@href, '/reel/')]",  # XPath for reel links
            "a[href*='/reel/']",  # CSS selector for reel links
            "div[role='tabpanel'] article a",  # General article links in reels tab
            "//div[contains(@class, '_aajw')]//a",  # Instagram's reel container class
            "//div[@role='tabpanel']//article//a"  # Any link within articles in the reels tab
        ]

        reel_links = None
        for selector in reel_selectors:
            try:
                if selector.startswith("//"):
                    # XPath selector
                    reel_links = page.locator(f"xpath={selector}").all()
                else:
                    # CSS selector
                    reel_links = page.locator(selector).all()
                
                if len(reel_links) > 0:
                    print(f"Found {len(reel_links)} reels using selector: {selector}")
                    break
            except Exception:
                continue

        if not reel_links or len(reel_links) == 0:
            print("No reels found. Trying alternative method...")
            # Try to find any clickable elements that might be reels
            try:
                page.wait_for_selector("article", timeout=10000)
                reel_links = page.locator("article a").all()
            except Exception as e:
                print(f"Alternative method failed: {e}")
                return
        
        if not reel_links or len(reel_links) == 0:
            print("No reels found after all attempts")
            return
            
        print(f"Found total {len(reel_links)} reels")
        
        for index, reel_link in enumerate(reel_links):
            try:
                print(f"\nProcessing reel {index + 1}/{len(reel_links)}")
                
                # Get href attribute to verify it's a reel
                href = reel_link.get_attribute("href")
                if href:
                    print(f"Reel URL: {href}")
                
                # Click the reel link
                reel_link.click()
                random_delay(5, 7)
                print("Opened reel")
                
                # Wait for video element with multiple selectors
                video_selectors = [
                    "video",
                    "//video",
                    "//div[@role='dialog']//video",
                    "div[role='dialog'] video"
                ]
                
                video = None
                for selector in video_selectors:
                    try:
                        if selector.startswith("//"):
                            video = page.wait_for_selector(f"xpath={selector}", timeout=10000)
                        else:
                            video = page.wait_for_selector(selector, timeout=10000)
                        if video:
                            print(f"Found video element using selector: {selector}")
                            break
                    except Exception:
                        continue
                
                if not video:
                    print("No video element found")
                    continue
                    
                print("Video element found")
                random_delay(2, 3)

                # Start recording
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                recording_path = os.path.join(reels_dir, f"reel_{timestamp}.webm")
                recording = page.start_recording_video(path=recording_path)

                # Get video duration
                try:
                    duration = page.evaluate("""() => {
                        const video = document.querySelector('video');
                        return video ? video.duration : 30;
                    }""")
                    record_time = min(duration + 2, 65)  # Add 2 seconds buffer, max 65 seconds
                    print(f"Recording for {record_time} seconds")
                except:
                    record_time = 30
                    print("Using default 30 seconds duration")

                # Wait for recording to complete
                time.sleep(record_time)
                
                # Stop recording
                page.stop_recording_video()
                print(f"Saved reel {index + 1}")

                # Go back to reels page
                page.go_back()
                random_delay(3, 5)
                
                # Wait for reels page to load
                page.wait_for_selector("article", timeout=10000)
                random_delay(2, 3)

            except Exception as e:
                print(f"Error processing reel {index + 1}: {e}")
                # Try to go back to reels page
                try:
                    page.go_back()
                    random_delay(3, 5)
                except:
                    print("Failed to go back to reels page")
                continue

    except Exception as e:
        print(f"Error in record_and_save_reels: {e}")

def main():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--start-maximized',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        # Create context with full viewport
        context = browser.new_context(
            viewport=None,
            no_viewport=True,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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
            if navigate_to_reels(page):
                record_and_save_reels(page)
            else:
                print("Failed to navigate to reels")

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    main()
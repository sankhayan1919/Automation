from playwright.sync_api import sync_playwright
import time

def login_to_instagram(page):
    # Navigate to Instagram login page
    page.goto('https://www.instagram.com/')
    time.sleep(3)
    
    # Fill in login credentials
    page.fill('input[name="username"]', 'jackpage216')
    page.fill('input[name="password"]', 'jack12#')
    
    # Click login button
    page.click('button[type="submit"]')
    time.sleep(5)
    
    # Handle save login info popup if it appears
    try:
        if page.locator('text="Save Your Login Info?"').is_visible():
            page.click('text="Not Now"')
    except:
        pass
    
    # Handle notifications popup if it appears
    try:
        if page.locator('text="Turn on Notifications"').is_visible():
            page.click('text="Not Now"')
    except:
        pass

def scrape_post_comments(page, post_link):
    comments = []
    page.goto(post_link)
    time.sleep(5)  # Wait for post to load
    
    try:
        # Click "Load more comments" button until all comments are loaded
        while True:
            try:
                load_more = page.locator('text="Load more comments"').first
                if load_more and load_more.is_visible():
                    load_more.click()
                    time.sleep(2)
                else:
                    break
            except:
                break
        
        # Click all "View replies" buttons
        while True:
            try:
                view_replies_buttons = page.locator('text="View replies"').all()
                if not view_replies_buttons:
                    break
                
                for button in view_replies_buttons:
                    if button.is_visible():
                        button.click()
                        time.sleep(2)  # Wait for replies to load
            except:
                break
        
        # Wait for all comments to load
        time.sleep(3)
        
        # Get all comments using a more specific selector
        comment_elements = page.locator('ul ul div[role="button"] span').all()
        
        for element in comment_elements:
            try:
                text = element.inner_text().strip()
                
                # Skip empty or invalid comments
                if not text or len(text) <= 1:
                    continue
                    
                # Skip common UI elements and metadata
                skip_texts = [
                    'Reply', 'View replies', 'Load more comments', 
                    'See translation', 'Verified', 'Creator',
                    'w', 'd', 'h', 'm' # Time indicators
                ]
                
                # Skip if text contains any of the skip_texts
                if any(skip in text for skip in skip_texts):
                    continue
                    
                # Skip if text starts with @ (username) or contains timestamp patterns
                if text.startswith('@') or any(x in text for x in ['w ago', 'd ago', 'h ago', 'm ago']):
                    continue
                
                # Skip if text is just a number followed by 'w', 'd', 'h', or 'm'
                if text.replace('w', '').replace('d', '').replace('h', '').replace('m', '').isdigit():
                    continue
                
                # Add unique comments only
                if text not in comments:
                    comments.append(text)
                    
            except:
                continue
                
    except Exception as e:
        print(f"Error scraping comments: {str(e)}")
    
    return comments

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        page = context.new_page()
        
        try:
            # Login to Instagram
            print("Logging in to Instagram...")
            login_to_instagram(page)
            time.sleep(5)
            print("Successfully logged in")
            
            # Navigate to target account
            target_account = "jackpage217"
            page.goto(f'https://www.instagram.com/{target_account}/')
            time.sleep(5)
            
            # Get visible post links
            post_elements = page.locator('a[href*="/p/"]').all()
            post_links = []
            for post in post_elements:
                link = 'https://www.instagram.com' + post.get_attribute('href')
                if link not in post_links:
                    post_links.append(link)
            
            print(f"Found {len(post_links)} posts")
            
            # Scrape comments from each post
            with open('comments.txt', 'w', encoding='utf-8') as f:
                for i, link in enumerate(post_links, 1):
                    print(f"\nScraping post {i}/{len(post_links)}")
                    comments = scrape_post_comments(page, link)
                    
                    # Write comments with post separator
                    f.write(f"\n{'='*50}\n")
                    f.write(f"Comments from Post {i}\n")
                    f.write(f"{'='*50}\n\n")
                    
                    if comments:
                        for comment in comments:
                            f.write(comment + '\n')
                    else:
                        f.write("No comments found for this post\n")
                    
                    print(f"Scraped {len(comments)} comments")
                    time.sleep(2)  # Wait between posts
            
            print("\nScraping completed! Comments saved to comments.txt")
            
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        
        finally:
            browser.close()

if __name__ == "__main__":
    main()
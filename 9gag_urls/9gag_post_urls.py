#This code extract the post link againts each input from search list and save it in a csv file
import time
import sys
import random
import pandas as pd
from urllib.parse import urlparse, urlunparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from collections import Counter



# if len(sys.argv) > 1:
#     search = sys.argv[1]
# else:
#     search = input("Enter the search term: ")
# Setting up the WebDriver
chrome_options = Options()
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15",
]
user_agent = random.choice(user_agents)
# chrome_options.add_argument("--headless")
chrome_options.add_argument(f"user-agent={user_agent}")
chrome_options.add_argument("window-size=1000,400")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})
search_list=['african','europe','israel','israel hamas war','trump','crime','black','white','terrorist', 'asian','immigrant','muslim','women','immigrants']
# Use this part of you want to use search query
search=search_list[7]
# search_url = f"https://9gag.com/search?query={search}"
# print(search_url)
# # Use this part if you want to use a page
search="top"
search_url = f"https://9gag.com/{search}"

print(search_url)

k_post = 2000  # Total number of posts to process
posts_opened = 0  # Count of posts opened
processed_posts = set()  # Set to store URLs of processed posts

def clean_url(url):
    """Remove the #comment part from the URL"""
    parsed = urlparse(url)
    cleaned = parsed._replace(fragment='')
    return urlunparse(cleaned)

def scroll_and_get_post_links(min_posts):
    post_links = []
    max_scroll_attempts = 600  # Increased from 5 to 10
    scroll_attempts = 0

    while len(post_links) < min_posts and scroll_attempts < max_scroll_attempts:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print(f"Scrolled down. Waiting for new posts to load...")
        time.sleep(random.uniform(3, 5))  # Randomized wait time

        # Find all post links
        elements = driver.find_elements(By.CSS_SELECTOR, "a[href^='/gag/']")
        for element in elements:
            post_url = clean_url(element.get_attribute('href'))
            if post_url not in processed_posts and post_url not in post_links:
                post_links.append(post_url)
        
        print(f"Currently found {len(post_links)} new unique post links.")
        scroll_attempts += 1

        if scroll_attempts % 10 == 0:
            print(f"Scrolled {scroll_attempts} times. Taking a short break...")
            time.sleep(random.uniform(3, 5))  # Longer pause every 5 scrolls

    if scroll_attempts == max_scroll_attempts:
        print(f"Reached maximum scroll attempts. Found {len(post_links)} new post links.")
    else:
        print(f"Found {len(post_links)} new post links. Stopping scroll.")
    
    return post_links


def extract_comments():
    comments = []
    seen_comments = set()
    repeated_count = Counter()
    max_scroll_attempts = 30  # Increased from implicit limit
    scroll_attempts = 0
    
    while scroll_attempts < max_scroll_attempts:
        # Extract comments
        comment_elements = driver.find_elements(By.CSS_SELECTOR, ".comment-item-text")
        current_comments = [comment.text for comment in comment_elements if comment.text.strip()]
        
        # Add new comments to the list
        new_comments = [c for c in current_comments if c not in seen_comments]
        comments.extend(new_comments)
        seen_comments.update(new_comments)

        # Update repeated counts
        repeated_count.update([c for c in current_comments if c in seen_comments])
        
        # Check if 20 comments are repeated 5 times
        if sum(1 for count in repeated_count.values() if count >= 3) >= 10:
            print("Detected enough repeated comments. Breaking the loop.")
            break

        # Scroll down to load more comments
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(2, 5))  # Sleep to mimic human behavior
        scroll_attempts += 1

        print(f"Scroll attempt {scroll_attempts}/{max_scroll_attempts}. Found {len(comments)} unique comments so far.")

    return comments




all_comments = []

def open_post(post_url):
    global posts_opened
    try:

        posts_opened += 1
        return True
    except Exception as e:
        print(f"Error opening post {post_url}: {str(e)}")
        # if len(driver.window_handles) > 1:
        #     driver.close()
        #     driver.switch_to.window(driver.window_handles[0])
        return False

# Main execution
try:
    driver.get(search_url)
    time.sleep(10)  # Wait for initial page load

    while posts_opened < k_post:
        new_post_links = scroll_and_get_post_links(k_post - posts_opened)
        
        if not new_post_links:
            print("No new posts found. Ending process.")
            break
        
        for post_url in new_post_links:
            if posts_opened >= k_post:
                break
            
            if post_url not in processed_posts:
                if open_post(post_url):
                    processed_posts.add(post_url)
                
                # Add a random delay between processing posts
                # time.sleep(random.uniform(2, 4))

except Exception as e:
    print(f"An unexpected error occurred: {str(e)}")

finally:
    print(f"Total posts processed: {posts_opened}")
    driver.quit()

    
df = pd.DataFrame(new_post_links, columns=["links"])
df.to_csv(f"./urls_{search}.csv", mode='a',index=False)
print(f"Saved {len(new_post_links)} comments to 'urls_{search}'.")
# Save all comments to a CSV file after processing all posts
# df = pd.DataFrame(all_comments, columns=["Comment"])
# df.to_csv(f"/home/research/9gag/all_comments_{search}.csv", index=False)
# print(f"Saved {len(all_comments)} comments to 'all_comment_{search}'.")

# Close the driver after completing the task
driver.quit()
print("Driver closed. Task completed.")

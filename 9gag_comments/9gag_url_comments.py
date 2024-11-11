# this code extract the comments from  url csv file against each input
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
chrome_options.add_argument("--headless")
chrome_options.add_argument(f"user-agent={user_agent}")
chrome_options.add_argument("window-size=1920,1080")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})

search_list=['africa','europe','israel','israel hamas war','trump','black','terrorist','white', 'asian','muslim','immigrants']
# Use this part of you want to use search query
search=search_list[1]
url_file=f"urls_{search}"
search_url = f"https://9gag.com/search?query={search}"
print(search_url)

k_post = 2  # Total number of posts to process
posts_opened = 0  # Count of posts opened
processed_posts = set()  # Set to store URLs of processed posts




def extract_comments():
    comments = []
    seen_comments = set()
    repeated_count = Counter()
    max_scroll_attempts = 8  # Increased from implicit limit
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

def open_post(post_url,index):
    global posts_opened
    try:
        driver.get(post_url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "post-container")))
        
        comments = extract_comments()
        all_comments.extend(comments)
        print(f"Extracted {len(comments)} comments from post {index}.")

        posts_opened += 1
        return True
    except Exception as e:
        print(f"Error opening post {post_url}: {str(e)}")
        if len(driver.window_handles) > 1:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        return False
post_links=pd.read_csv(f"./urls_{search}.csv")
post_links = post_links.iloc[::-1].reset_index(drop=True)
print(post_links.shape[0])
# Main execution
try:


        for i in range(0,post_links.shape[0] ):
            index = post_links.index[i]
            post_url = post_links.iloc[i]['links']
            open_post(post_url,index)
            processed_posts.add(post_url)
        
                
                # Add a random delay between processing posts
            time.sleep(random.uniform(2, 4))

except Exception as e:
    print(f"An unexpected error occurred: {str(e)}")
    print(f"Index: {index}, Post URL: {post_url}")

finally:
    print(f"Total posts processed: {posts_opened}")
    driver.quit()

    
df = pd.DataFrame(all_comments, columns=["links"])
df.to_csv(f"./comments_{search}.csv",mode='a', index=False)
print(f"Saved {len(all_comments)} comments to 'comments_{search}'.")


# Close the driver after completing the task
driver.quit()
print("Driver closed. Task completed.")

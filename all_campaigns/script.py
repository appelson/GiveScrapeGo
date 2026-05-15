# Importing libraries
import time
import json
import os
import random
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import glob
import pandas as pd

# Results folder
output_folder = "results"
os.makedirs(output_folder, exist_ok=True)

# Driver setup
options = uc.ChromeOptions()
driver = uc.Chrome(options=options, version_main=147)

base_url = "https://api-v2.givesendgo.com/api/v1/public-campaigns?page={page}"

try:
    # Fetch page 1 to get total pages
    driver.get(base_url.format(page=1))
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    data = json.loads(soup.find("pre").text.strip())
    total_pages = data["pagination"]["last_page"]

    # Save page 1
    with open(os.path.join(output_folder, "sitemap_page1.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved page 1 ({len(data.get('data', []))} campaigns)")

    # Scrape pages 2 through total_pages
    for page in range(2, total_pages + 1):
        url = BASE_URL.format(page=page)
        print(f"Grabbing page {page}/{total_pages}...")
        driver.get(url)

        # Random sleep between pages to avoid detection
        sleep_time = random.uniform(1, 3)
        print(f" Sleeping {sleep_time:.1f}s...")
        time.sleep(sleep_time)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        pre = soup.find("pre")
        if not pre:
            break

        try:
            data = json.loads(pre.text.strip())
        except json.JSONDecodeError as e:
            break

        # Save page
        filename = os.path.join(output_folder, f"sitemap_page{page}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  → Saved {len(data.get('data', []))} campaigns")

finally:
    driver.quit()

# Combining JSONs
pattern = os.path.join(output_folder, "sitemap_page*.json")
files = sorted(glob.glob(pattern), key=lambda x: int(x.split("page")[1].split(".")[0]))

combined_campaigns = []
for file in files:
    with open(file, "r", encoding="utf-8") as f:
        combined_campaigns.extend(json.load(f).get("data", []))

combined_file = os.path.join(output_folder, "all_campaigns.json")
with open(combined_file, "w", encoding="utf-8") as f:
    json.dump({"data": combined_campaigns}, f, ensure_ascii=False, indent=2)

# Saving as CSV
with open(combined_file, "r", encoding="utf-8") as f:
    df = pd.DataFrame(json.load(f).get("data", []))

csv_file = os.path.join(output_folder, "all_campaigns.csv")
df.to_csv(csv_file, index=False)

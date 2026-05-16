# ----------------------- IMPORTING LIBRARIES ---------------------------------
# Importing libraries
import re
import time
import json
import os
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import glob
import pandas as pd
from selenium.common.exceptions import SessionNotCreatedException

# ----------------------- DOWNLOADING DATA ------------------------------------

# Defining the output folder
output_folder = "results"

# Campaign URL from "https://www.givesendgo.com/rift-connor-emergency-fund"
campaign = "rift-connor-emergency-fund"

# Creating the output folder directory
os.makedirs(output_folder, exist_ok=True)


def _create_chrome_driver(options):
    """Create Chrome driver, auto-detecting version_main from error if Chrome/ChromeDriver version mismatch."""
    try:
        return uc.Chrome(options=options)
    except SessionNotCreatedException as e:
        msg = str(e)
        match = re.search(r"Current browser version is (\d+)\.\d+\.\d+", msg)
        if match:
            return uc.Chrome(options=uc.ChromeOptions(), version_main=int(match.group(1)))
        raise


# Initializing the chrome driver
options = uc.ChromeOptions()
driver = _create_chrome_driver(options)

# Definign donations list
all_donations = []

# Running through a driver loop
try:
    for page in range(1, 140): # Note that 140 was arbitrarily put for this case since I know it will work
      
        # Adding the "givesendgo" API url
        url = f"https://www.givesendgo.com/api/v2/campaigns/{campaign}/get-recent-donations?pageNo={page}"
        driver.get(url)

        # If page 1, then wait 10 seconds
        if page == 1:
            time.sleep(10)
            
        # If not, go almost immediatly
        else:
            time.sleep(0.1)

        # Get the page and parse it
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Find "pre"
        pre = soup.find("pre")
        if not pre:
            print(f"No JSON found on page {page}")
            break

        # Getting the raw JSON data
        raw_json = pre.text.strip()

        # For the JSON data, downlowd
        try:
            data = json.loads(raw_json)
            
            # Getting donations (API returns under returnData.donations)
            donations = data.get("returnData", {}).get("donations", [])
            
            # Adding to an all donations list
            all_donations.extend(donations)

            # Saving the JSON page in the output folder
            filename = os.path.join(output_folder, f"donations_page{page}.json")
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"JSON for page {page} saved to {filename}")

        # Error for failing to decode
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON on page {page}:", e)
            break

# Quitting the driver
finally:
    driver.quit()

# ----------------------- COMBINING JSONS ------------------------------------

# Getting all downloaded JSON files 
pattern = os.path.join(output_folder, "donations_page*.json")
files = sorted(glob.glob(pattern))

# Combining donation JSON files into a list
combined_donations = []

for file in files:
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
        donations = data.get("returnData", {}).get("donations", [])
        combined_donations.extend(donations)
        
# Saving that list into a single JSON called `all_donations.json`. 
combined_file = os.path.join(output_folder, "all_donations.json")
with open(combined_file, "w", encoding="utf-8") as f:
    json.dump({"donations": combined_donations}, f, ensure_ascii=False, indent=2)
    
# ----------------------- SAVING AS CSV ------------------------------------

# Defining donations 
with open(combined_file, "r", encoding="utf-8") as f:
    data = json.load(f)

donations = data.get("donations", [])

# Converting donations to a DataFrame
df = pd.DataFrame(donations)

# Saving the dataframe as a CSV
csv_file = os.path.join(output_folder, "all_donations.csv")
df.to_csv(csv_file, index=False)










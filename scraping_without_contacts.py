import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import signal
import sys
import random

# Constants
BASE_URL = "https://www.booking.com/searchresults.html?ss={city}"
OUTPUT_FILE = "accommodations_without_contacts.xlsx"
all_accommodations = []  # Global variable to store progress

# Graceful Exit Handling
def save_and_exit(signum, frame):
    print("\nInterrupt detected! Saving progress...")
    save_data_to_excel()
    sys.exit(0)

signal.signal(signal.SIGINT, save_and_exit)

# Dismiss the Modal by Clicking the Close Button
def dismiss_sign_in_modal(driver):
    try:
        print("Waiting for Sign-in modal to appear...")
        time.sleep(10)  # Wait for the modal to appear (adjustable delay)
        close_button = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Dismiss sign-in info."]')
        close_button.click()
        print("Sign-in modal dismissed by clicking the close button.")
    except Exception as e:
        print(f"Sign-in modal not found or could not be dismissed: {e}")

# Step 1: Scrape Booking.com for Accommodation Details
def scrape_booking(city):
    formatted_city = city.replace(" ", "+")
    if city.lower() == "alba":
        formatted_city += "+italy"

    url = BASE_URL.format(city=formatted_city)

    # Set up the Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.headless = False  # Disable headless mode to visually debug if needed
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)

    # Dismiss the Sign-in modal if it appears
    dismiss_sign_in_modal(driver)

    accommodations = []

    while True:
        # Scroll to the bottom to load the "Load More results" button
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Allow time for content to load
        
        # Scrape accommodations
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        for item in soup.select('[data-testid="property-card-container"]'):
            name = item.select_one('[data-testid="title"]').get_text(strip=True) if item.select_one('[data-testid="title"]') else "N/A"
            link_element = item.select_one('[data-testid="property-card-desktop-single-image"]')
            link = link_element["href"] if link_element else "N/A"
            if not link.startswith("https"):
                link = f"https://www.booking.com{link}"

            accommodations.append({"Name": name, "City": city, "Link": link})

        # Check if "Load more results" button is present
        try:
            load_more_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[.//span[text()="Load more results"]]'))
            )
            # print("Found 'Load more results'. Clicking to load more accommodations...")
            load_more_button.click()
            time.sleep(2)  # Wait for the new results to load
        except Exception as e:
            print("No 'Load more results' button found or an error occurred.")
            print(f"Started the Scraping accommodations for city: {city}...")
            break  # Exit loop when the button is not found (all results loaded)

    driver.quit()
    return accommodations

# Step 2: Scrape the Address from the Accommodation Page
def scrape_address_property(link):
    try:
        response = requests.get(link)
        soup = BeautifulSoup(response.text, 'html.parser')
        address_element = soup.select_one('div[tabindex="0"].a53cbfa6de.f17adf7576')
        if address_element:
           address = re.sub(r"(Italy.*)", "Italy", address_element.get_text(strip=True))
        
        property_element = soup.select_one('a.bui_breadcrumb__link_masked')
        if property_element:
            property_text = property_element.get_text(strip=True)
            # Extract property type from the text
            match = re.search(r"\((.*?)\)", property_text)
            if match:
                property_type = match.group(1) 

        return address, property_type
            
    except Exception as e:
        print(f"Error scraping address and property type for {link}: {e}")
        return "N/A", "N/A"


# Save Data to Excel
def save_data_to_excel():
    global all_accommodations
    if all_accommodations:
        df = pd.DataFrame(all_accommodations)
        df.to_excel(OUTPUT_FILE, index=False)
    else:
        print("No data to save.")

# Main Function
def main():
    global all_accommodations

    target_cities = ["Milan"]

    for city in target_cities:
        try:
            accommodations = scrape_booking(city)
            for accommodation in accommodations:
                # Pause to avoid rate limits
                time.sleep(random.uniform(1, 3))
                
                # Scrape the address
                address, property_type = scrape_address_property(accommodation["Link"])
                accommodation["Address"] = address
                accommodation["Property"] = property_type

                # print(f"Processed: {accommodation['Name']} in {city}", flush=True)

                all_accommodations.append(accommodation)
                save_data_to_excel()  # Save progress after each accommodation

        except Exception as e:
            print(f"Error processing city {city}: {e}")
            continue

    save_data_to_excel()

if __name__ == "__main__":
    main()

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from googlesearch import search
import pandas as pd
import re
import time
import signal
import sys
import random

# Constants
BASE_URL = "https://www.booking.com/searchresults.html?ss={city}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
}
MAX_LIMIT = 30  # Set MAX_LIMIT here, change to 0 for unlimited scraping
all_accommodations = []  # Global variable to store progress
scraping_in_progress = True  # Global flag to control the scraping process

def save_and_exit(signum, frame):
    print("\nInterrupt detected! Saving progress and stopping scraping...")

    # Ensure each city's data is saved before exiting
    global all_accommodations
    global scraping_in_progress
    
    if all_accommodations:
        # Create a set of cities in the accommodations data
        cities = set(accom['City'] for accom in all_accommodations)
        for city in cities:
            save_data_to_excel(city)  # Save each city's data
        save_total_result()  # Save the total result at the end

    scraping_in_progress = False  # Stop the entire scraping process
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
    options.headless = True  # Disable headless mode to visually debug if needed
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)

    # Dismiss the Sign-in modal if it appears
    dismiss_sign_in_modal(driver)

    accommodations = []
    accommodation_count = 0  # Track number of accommodations scraped

    while True:
        # Check if scraping should stop
        if not scraping_in_progress:
            print("Scraping stopped.")
            break

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
            accommodation_count += 1
            if MAX_LIMIT != 0 and accommodation_count >= MAX_LIMIT:  # Stop after reaching MAX_LIMIT
                break

        if MAX_LIMIT != 0 and accommodation_count >= MAX_LIMIT:
            break  # Exit the loop once MAX_LIMIT is reached

        # Check if "Load more results" button is present
        try:
            load_more_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[.//span[text()="Load more results"]]'))
            )
            load_more_button.click()
            time.sleep(2)  # Wait for the new results to load
        except Exception as e:
            print("No 'Load more results' button found or an error occurred.")
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

def normalize_phone(phone):
    """Normalize phone numbers to the format '+39 XXX XXX XXXX'."""
    # Remove all unwanted characters (keep digits and '+')
    phone_cleaned = re.sub(r"[^\d\s\+]", "", phone)
    phone_cleaned = re.sub(r"\s+", "", phone_cleaned)  # Remove spaces for formatting
    if phone_cleaned.startswith("+39"):  # Ensure it starts with +39
        # Reformat into +39 XXX XXX XXXX
        formatted_phone = f"{phone_cleaned[:3]} {phone_cleaned[3:6]} {phone_cleaned[6:9]} {phone_cleaned[9:]}"
        return formatted_phone.strip()
    return None  # Return None if it doesn't match the expected pattern

def validate_email(email):
    """Ensure emails start with a letter and are valid."""
    email_pattern = r"^[a-zA-Z][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return email if re.match(email_pattern, email) else None

def find_contact_details(name, city):
    try:
        query = f"{name} {city} phone email"
        emails = []
        phones = []

        for result in search(query, num_results=5):
            try:
                response = requests.get(result, headers=HEADERS)
                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract emails
                raw_emails = re.findall(r"[a-zA-Z][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", soup.get_text())
                emails += [validate_email(email) for email in raw_emails if validate_email(email) is not None]

                # Extract phone numbers
                raw_phones = re.findall(r"\+39[\s\-()0-9]{8,}", soup.get_text())  # Italian numbers
                phones += [normalize_phone(phone) for phone in raw_phones if normalize_phone(phone) is not None]

            except Exception as e:
                print(f"Error fetching contact details from {result}: {e}")
                continue

        return {
            "Emails": list(set(emails)) if emails else ["N/A"],
            "Phones": list(set(phones)) if phones else ["N/A"]
        }
    except Exception as e:
        print(f"Error during Google search: {e}")
        return {"Emails": ["N/A"], "Phones": ["N/A"]}

# Save Data to Excel (city file)
def save_data_to_excel(city):
    global all_accommodations
    if all_accommodations:
        # Save only the accommodations for the current city
        city_accommodations = [accom for accom in all_accommodations if accom['City'] == city]
        df = pd.DataFrame(city_accommodations)
        # Save the file with the city name
        city_filename = f"{city}_accommodations.xlsx"
        df.to_excel(city_filename, index=False)
        print(f"Saved {len(city_accommodations)} accommodations for {city}.")

# Save the Total Data to Excel
def save_total_result():
    global all_accommodations
    if all_accommodations:
        df = pd.DataFrame(all_accommodations)
        df.to_excel("total_accommodations.xlsx", index=False)
        print(f"Saved total results of {len(all_accommodations)} accommodations.")

def main():
    target_cities = [
        "Venice", "Verona", "Padova", "Vicenza", "Bassano del Grappa", "Cortina d'Ampezzo", "Jesolo", 
        "Milan", "Como", "Bergamo", "Brescia", "Mantua", "Sirmione", "Pavia", "Cremona", "Lecco",
        "Rome", "Tivoli", "Viterbo", "Ostia Antica", "Ostia", "Fiumicino", "Gaeta", 
        "Florence", "Pisa", "Siena", "Lucca", "Forte dei Marmi", "Viareggio",
        "Naples", "Pompeii", "Amalfi", "Sorrento", "Capri", "Ischia", "Procida", "Caserta",
        "Bologna", "Rimini", "Ferrara", "Modena", "Parma", "Ravenna", "Cesenatico", "Riccione",
        "Palermo", "Catania", "Taormina", "Syracuse", "Agrigento", "Cefalù", "Ragusa", "Trapani",
        "Bari", "Lecce", "Alberobello", "Ostuni", "Polignano a Mare", "Monopoli", "Gallipoli", "Otranto",
        "Cinque Terre", "Portofino", "Sanremo", "Alassio",
        "Turin", "Alba", "Asti",
        "Trento", "Bolzano", "Madonna di Campiglio", "Riva del Garda",
        "Olbia", "Cagliari", "Sardinia",
        "Ancona", "Urbino", "San Benedetto del Tronto", "Macerata",
        "Perugia",
        "Trieste", "Udine",
        "Aosta", "Courmayeur", "Cervinia", "La Thuile", "Gressoney-Saint-Jean", "Saint-Vincent", "Cogne", "Champoluc", "Antey-Saint-André", "Valtournenche"
    
    ]

    for city in target_cities:
        if not scraping_in_progress:
            break  # Stop scraping if the flag is set to False
        try:
            accommodations = scrape_booking(city)
            for accommodation in accommodations:
                time.sleep(random.uniform(1, 3))  # Pause to avoid rate limits
                address, property_type = scrape_address_property(accommodation["Link"])
                accommodation["Address"] = address
                accommodation["Property Type"] = property_type

                contact_details = find_contact_details(accommodation["Name"], city)
                accommodation["Email"] = contact_details["Emails"][0]
                accommodation["Phone Number"] = contact_details["Phones"][0]

                all_accommodations.append(accommodation)

            save_data_to_excel(city)  # Save progress after each city
        except Exception as e:
            print(f"Error processing city {city}: {e}")
            continue

    save_total_result()  # Save total data after all cities are scraped

if __name__ == "__main__":
    main()

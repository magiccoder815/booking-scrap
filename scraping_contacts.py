import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from googlesearch import search  # Install via `pip install googlesearch-python`
import time
import signal
import sys
import os

# Constants
BASE_URL = "https://www.booking.com/searchresults.html?ss={city}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
}
OUTPUT_FILE = "accommodations_with_contacts.xlsx"
all_accommodations = []  # Global variable to store progress

# Graceful Exit Handling
def save_and_exit(signum, frame):
    print("\nInterrupt detected! Saving progress...")
    save_data_to_excel()
    sys.exit(0)

signal.signal(signal.SIGINT, save_and_exit)

# Step 1: Scrape Booking.com for Accommodation Details
def scrape_booking(city):
    print(f"Scraping accommodations for city: {city}...")
    formatted_city = city.replace(" ", "+")
    if city.lower() == "alba":
        formatted_city += "+italy"

    url = BASE_URL.format(city=formatted_city)
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    accommodations = []
    for item in soup.select('[data-testid="property-card-container"]'):
        name = item.select_one('[data-testid="title"]').get_text(strip=True) if item.select_one('[data-testid="title"]') else "N/A"
        link_element = item.select_one('[data-testid="property-card-desktop-single-image"]')
        link = link_element["href"] if link_element else "N/A"
        if not link.startswith("https"):
            link = f"https://www.booking.com{link}"

        accommodations.append({"Name": name, "City": city, "Link": link})

    return accommodations

# Step 2: Scrape the Address from the Accommodation Page
def scrape_address(link):
    try:
        response = requests.get(link, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        address_element = soup.select_one('div[tabindex="0"].a53cbfa6de.f17adf7576')
        address = re.sub(r"(Italy.*)", "Italy", address_element.get_text(strip=True) if address_element else "N/A")
        return address
    except Exception as e:
        return "N/A"

# Step 3: Use Google Search to Find Contact Details
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

    target_cities = [
        "Venice"
        # "Venice", "Verona", "Padova", "Vicenza", "Bassano del Grappa", "Cortina d'Ampezzo", "Jesolo", 
        # "Milan", "Como", "Bergamo", "Brescia", "Mantua", "Sirmione", "Pavia", "Cremona", "Lecco",
        # "Rome", "Tivoli", "Viterbo", "Ostia Antica", "Ostia", "Fiumicino", "Gaeta", "Anzio",
        # "Florence", "Pisa", "Siena", "Lucca", "Forte dei Marmi", "Viareggio",
        # "Naples", "Pompeii", "Amalfi", "Sorrento", "Capri", "Ischia", "Procida", "Caserta",
        # "Bologna", "Rimini", "Ferrara", "Modena", "Parma", "Ravenna", "Cesenatico", "Riccione",
        # "Palermo", "Catania", "Taormina", "Syracuse", "Agrigento", "Cefalù", "Ragusa", "Trapani",
        # "Bari", "Lecce", "Alberobello", "Ostuni", "Polignano a Mare", "Monopoli", "Gallipoli", "Otranto",
        # "Cinque Terre", "Portofino", "Sanremo", "Alassio",
        # "Turin", "Alba", "Asti",
        # "Trento", "Bolzano", "Madonna di Campiglio", "Riva del Garda",
        # "Olbia", "Cagliari", "Sardinia",
        # "Ancona", "Urbino", "San Benedetto del Tronto", "Macerata",
        # "Perugia",
        # "Trieste", "Udine",
        # "Aosta", "Courmayeur", "Cervinia", "La Thuile", "Gressoney-Saint-Jean", "Saint-Vincent", "Cogne", "Champoluc", "Antey-Saint-André", "Valtournenche"
    ]
    
    for city in target_cities:
        try:
            accommodations = scrape_booking(city)
            for accommodation in accommodations:
                # Pause to avoid rate limits
                time.sleep(1)
                
                # Scrape the address
                address = scrape_address(accommodation["Link"])
                accommodation["Address"] = address

                # Search for contact details via Google
                contact_details = find_contact_details(accommodation["Name"], city)
                accommodation["Email"] = contact_details["Emails"][0]
                accommodation["Phone Number"] = contact_details["Phones"][0]

                all_accommodations.append(accommodation)
                save_data_to_excel()  # Save progress after each accommodation

        except Exception as e:
            print(f"Error processing city {city}: {e}")
            continue

    save_data_to_excel()

if __name__ == "__main__":
    main()

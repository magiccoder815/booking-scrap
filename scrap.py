import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from googlesearch import search  # Install via `pip install googlesearch-python`
import time

# Constants
BASE_URL = "https://www.booking.com/searchresults.html?ss={city}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
}

# Step 1: Scrape Booking.com for Accommodation Details
def scrape_booking(city):
    print(f"Scraping accommodations for city: {city}...")
    # url = BASE_URL.format(city=city.replace(" ", "+"))
    formatted_city = city.replace(" ", "+")
    if city.lower() == "alba":
        formatted_city += "+italy"

    url = BASE_URL.format(city=formatted_city)
    print(url)
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    accommodations = []
    for item in soup.select('[data-testid="property-card-container"]'):  # Adjust this selector if needed
        name = item.select_one('[data-testid="title"]').get_text(strip=True) if item.select_one('[data-testid="title"]') else "N/A"
        city = city
        link_element = item.select_one('[data-testid="property-card-desktop-single-image"]')
        link = link_element["href"] if link_element else "N/A"

        # link = "https://www.booking.com" + item.select_one('.hotel_name_link')['href'] if item.select_one('.hotel_name_link') else "N/A"
        # address = item.select_one('.address').get_text(strip=True) if item.select_one('.address') else "N/A"
        # accommodations.append({"Name": name, "Link": link, "Address": address, "City": city})

        if not link.startswith("https"):
            link = f"https://www.booking.com{link}"

        accommodations.append({"Name": name, "City": city, "Link": link})

    
    return accommodations

# Step 2: Scrape the Address from the Accommodation Page
def scrape_address(link):
    try:
        # print(f"Scraping address from: {link}")
        response = requests.get(link, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract the address
        address_element = soup.select_one('div[tabindex="0"].a53cbfa6de.f17adf7576')
        address = re.sub(r"(Italy.*)", "Italy", address_element.get_text(strip=True) if address_element else "N/A")

        print(address)
        return address
    except Exception as e:
        # print(f"Error scraping address: {e}")
        return "N/A"


# Step 2: Search for Missing Contact Details
# def find_contact_details(name, address):
#     query = f"{name} {address} contact email phone"
#     print(f"Searching Google for contact details: {query}...")
    
#     for result in search(query, num_results=5):  # Adjust `num_results` if needed
#         try:
#             response = requests.get(result, headers=HEADERS)
#             emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", response.text)
#             phones = re.findall(r"\+?\d[\d\s\-\(\)]+", response.text)
#             if emails or phones:
#                 return {"Email": emails[0] if emails else "N/A", "Phone": phones[0] if phones else "N/A"}
#         except Exception as e:
#             print(f"Error fetching contact details: {e}")
#             continue
    
#     return {"Email": "N/A", "Phone": "N/A"}

# Step 3: Combine Data and Save to Excel
def main():
    target_cities = [
        # Add the target cities here
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
    ]
    
    all_accommodations = []
    for city in target_cities:
        accommodations = scrape_booking(city)
        for accommodation in accommodations:
            # Pause to avoid rate limits
            time.sleep(1)
            
            # Scrape the address from the accommodation page
            address = scrape_address(accommodation["Link"])
            accommodation["Address"] = address
        
        all_accommodations.extend(accommodations)
    
    # Save to Excel
    df = pd.DataFrame(all_accommodations)
    df.to_excel("accommodations_with_addresses.xlsx", index=False)
    print("Data saved to accommodations_with_addresses.xlsx!")

if __name__ == "__main__":
    main()

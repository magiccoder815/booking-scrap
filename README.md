# Booking.com Accommodation Scraper

This Python script scrapes accommodation details (name, link, address, and property type) from Booking.com for specified cities. The scraped data is saved in an Excel file.

## Features

- Scrapes accommodation names and links from the Booking.com search results page.
- Extracts address and property type from individual accommodation pages.
- Saves the scraped data to an Excel file.
- Handles graceful termination to save progress in case of interruptions.

## Requirements

- Python 3.11.2 or higher
- Google Chrome installed
- Selenium WebDriver for Chrome

## Installation

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run Script
   ```bash
   python scraping.py
   ```

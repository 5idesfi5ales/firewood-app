import requests
import urllib.parse
import os

# ==========================================
# 1. SETTINGS (Same as main.py)
# ==========================================
AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN")
BASE_ID = "appXE1r8SZN0q1JzK"
TABLE_NAME = "tblFK1EC9tBrCYR6W"

# ==========================================
# 2. THE ROUTE GENERATOR
# ==========================================
def generate_route(city_name):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}
    
    # Filter: Status must be Unchecked (0) AND City must match
    # We use Airtable's formula syntax
    params = {
        "filterByFormula": f"AND({{Status}} = 0, FIND(LOWER('{city_name}'), LOWER({{City}})))"
    }

    print(f"Searching Airtable for pending orders in {city_name}...")
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error fetching data: {response.text}")
        return

    records = response.json().get('records', [])

    if not records:
        print(f"No pending orders found for '{city_name}'. Check your spelling or Airtable checkboxes.")
        return

    # Extract all street addresses
    addresses = []
    total_value = 0
    
    for r in records:
        addr = r['fields'].get('Street Address')
        city = r['fields'].get('City')
        price = r['fields'].get('Price', 0)
        
        if addr:
            # Combine address and city for better Google Maps accuracy
            full_address = f"{addr}, {city}"
            addresses.append(full_address)
            total_value += price

    # --- BUILD THE GOOGLE MAPS LINK ---
    # We use 'My Location' as the start. 
    # The last address is the 'Destination'. Everything else is a 'Waypoint'.
    
    base_map_url = "https://www.google.com/maps/dir/?api=1&origin=My+Location"
    
    if len(addresses) > 0:
        destination = urllib.parse.quote(addresses[-1])
        
        if len(addresses) > 1:
            waypoints = "|".join([urllib.parse.quote(a) for a in addresses[:-1]])
            final_url = f"{base_map_url}&destination={destination}&waypoints={waypoints}"
        else:
            final_url = f"{base_map_url}&destination={destination}"

        print("\n" + "="*40)
        print(f"🚗 ROUTE FOUND FOR: {city_name.upper()}")
        print(f"💰 TOTAL REVENUE: ${total_value}")
        print(f"📍 STOPS: {len(addresses)}")
        print("="*40)
        print(f"\nCLICK TO START NAVIGATING:\n{final_url}\n")
    else:
        print("No valid addresses found in those records.")

if __name__ == "__main__":
    target = input("Enter the City Shane is visiting today: ")
    generate_route(target)
import requests
import os
import random
import time
import json

# ==========================================
# 1. SETTINGS (Same as main.py)
# ==========================================
AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN")
BASE_ID = "appXE1r8SZN0q1JzK"
TABLE_NAME = "tblFK1EC9tBrCYR6W"

PRICES = { "quarter": 150.00, "half": 250.00, "full": 450.00 }

# ==========================================
# 2. TEST DATA POOLS
# ==========================================
FIRST_NAMES = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "William", "Elizabeth"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

# Real Public Addresses in Quinlan/Terrell Area for Testing
REAL_LOCATIONS = [
    {"address": "102 E Main St", "city": "Quinlan"},
    {"address": "8891 State Hwy 34", "city": "Quinlan"},
    {"address": "2000 W Panther Path", "city": "Quinlan"},
    {"address": "1562 E Quinlan Pkwy", "city": "Quinlan"},
    {"address": "201 E Nash St", "city": "Terrell"},
    {"address": "1900 W Moore Ave", "city": "Terrell"},
    {"address": "1200 W Brin St", "city": "Terrell"},
    {"address": "1400 W Moore Ave", "city": "Terrell"},
    {"address": "301 S Virginia St", "city": "Terrell"},
    {"address": "100 Hunt St", "city": "Terrell"}
]

AMOUNTS = ["quarter", "half", "full"]

# ==========================================
# 3. GENERATOR LOGIC
# ==========================================
def create_random_records(count=10):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json"
    }

    print(f"🚀 Generating {count} random orders for Shane...")

    for i in range(count):
        # Pick random data
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        loc = random.choice(REAL_LOCATIONS)
        amt = random.choice(AMOUNTS)
        phone = f"({random.randint(200,999)}) {random.randint(100,999)}-{random.randint(1000,9999)}"
        fb_id = random.randint(100000, 999999)
        
        payload = {
            "fields": {
                "Real Name": name,
                "FB Profile": f"https://facebook.com/user{fb_id}",
                "City": loc["city"],
                "Street Address": loc["address"],
                "Phone": phone,
                "Amount": amt,
                "Price": PRICES[amt],
                "Status": False
            }
        }

        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print(f"✅ Created: {name} in {loc['city']} (${PRICES[amt]})")
        else:
            print(f"❌ Error: {response.text}")
        
        # Small delay to respect Airtable's speed limit
        time.sleep(0.2)

if __name__ == "__main__":
    create_random_records(10)
    print("\n✨ Done! Your Airtable is now full of test data.")
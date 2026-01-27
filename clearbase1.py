import requests
import os
import time

# ==========================================
# 1. SETTINGS (Same as main.py)
# ==========================================
AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN")
BASE_ID = "appXE1r8SZN0q1JzK"
TABLE_NAME = "tblFK1EC9tBrCYR6W"

# ==========================================
# 2. THE CLEANER LOGIC
# ==========================================
def clear_all_records():
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}

    print("🔍 Fetching all records to delete...")
    
    # 1. Get all record IDs
    all_ids = []
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching: {response.text}")
        return

    records = response.json().get('records', [])
    all_ids = [r['id'] for r in records]

    if not all_ids:
        print("Table is already empty! Nothing to delete.")
        return

    print(f"Found {len(all_ids)} records. Starting deletion...")

    # 2. Delete in batches of 10 (Airtable API Limit)
    # We loop through the list 10 items at a time
    for i in range(0, len(all_ids), 10):
        batch = all_ids[i:i+10]
        
        # Build the delete URL with multiple IDs
        # Format: ?records[]=id1&records[]=id2...
        delete_params = [('records[]', record_id) for record_id in batch]
        
        del_response = requests.delete(url, headers=headers, params=delete_params)
        
        if del_response.status_code == 200:
            print(f"✅ Deleted batch of {len(batch)}...")
        else:
            print(f"❌ Error deleting batch: {del_response.text}")
        
        # Respect Airtable rate limits (5 requests per second)
        time.sleep(0.25)

    print("\n✨ DATABASE IS NOW CLEAN! Ready for new orders.")

if __name__ == "__main__":
    confirm = input("ARE YOU SURE? This will delete EVERY row in Shane's list. (y/n): ")
    if confirm.lower() == 'y':
        clear_all_records()
    else:
        print("Action cancelled.")
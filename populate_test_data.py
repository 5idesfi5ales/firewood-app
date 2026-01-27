import openai 
import json 
import requests 
import os
import time

# ==========================================
# 1. SETTINGS & KEYS
# ==========================================
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN")

BASE_ID = "appXE1r8SZN0q1JzK"
TABLE_NAME = "tblFK1EC9tBrCYR6W"

# Shane's Price List
PRICES = { "quarter": 150.00, "half": 250.00, "full": 450.00 }

# ==========================================
# 2. THE BRAIN
# ==========================================
def process_message(user_text, fb_profile_link): 
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    system_prompt = """
    You are an order-taking assistant. Extract: name, city, address, phone, amount.
    The amount must be exactly one of these: 'quarter', 'half', or 'full'.
    Return ONLY JSON.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_text}],
        response_format={"type": "json_object"}
    )
    result = json.loads(response.choices[0].message.content)
    result['fb_link'] = fb_profile_link
    return result

def normalize_and_calculate(ai_response): 
    # 1. Extract the amount the AI found
    amt = str(ai_response.get("amount")).lower().strip()
    
    # 2. PYTHON calculates the price (Much more reliable than AI)
    # If the AI found "half", we look up 250.00
    calculated_price = PRICES.get(amt, 0)
    
    return {
        "Real Name": ai_response.get("name") or ai_response.get("real_name"),
        "FB Profile": ai_response.get("fb_link"),
        "City": ai_response.get("city"),
        "Street Address": ai_response.get("address") or ai_response.get("street_address"),
        "Phone": str(ai_response.get("phone")) if ai_response.get("phone") else None,
        "Amount": amt, 
        "Price": calculated_price, # Math done by Python
        "Status": False
    }

def save_to_airtable(data): 
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}" 
    headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}", "Content-Type": "application/json"}
    fields = {k: v for k, v in data.items() if v is not None}
    response = requests.post(url, headers=headers, json={"fields": fields})
    return response.status_code == 200

# ==========================================
# 3. DATASET
# ==========================================
REAL_DATA = [
    {"text": "Hey I'm David Anderson. I need a full cord at 2500 Stonewall St in Greenville. 903-555-0100", "link": "fb.com/da1"},
    {"text": "Susan Taylor here from Wills Point. 120 N 4th St. Half cord please. 903-555-0200", "link": "fb.com/st2"},
    {"text": "Thomas Moore, 305 N Arch St, Royse City. Need a quarter cord. 972-555-0300", "link": "fb.com/tm3"},
    {"text": "I'm Lisa Martin in Rockwall. 1101 Ridge Rd. Need a full cord. 972-555-0400", "link": "fb.com/lm4"},
    {"text": "Matthew Jackson, Caddo Mills. 2307 Main St. Half cord hmu 903-555-0500", "link": "fb.com/mj5"},
    {"text": "Yo its Chris White in Fate. 1900 CD Boren Pkwy. Full cord. 972-555-0600", "link": "fb.com/cw6"},
    {"text": "Donna Harris from Emory. 100 N Texas St. Quarter cord. 903-555-0700", "link": "fb.com/dh7"},
    {"text": "Matthew Anderson, Grand Saline. 128 E Frank St. Half cord. 903-555-0800", "link": "fb.com/ma8"}
]

# ==========================================
# 4. RUNNER
# ==========================================
if __name__ == "__main__": 
    print("🚀 RE-POPULATING WITH RELIABLE MATH...")
    for item in REAL_DATA:
        ai_raw = process_message(item['text'], item['link'])
        final = normalize_and_calculate(ai_raw)
        if save_to_airtable(final):
            print(f"✅ Saved {final['Real Name']} - Amount: {final['Amount']} - Price: ${final['Price']}")
        time.sleep(0.5)
    print("\n✨ DONE! Every entry now has a correct price.")
import openai 
import json 
import requests 
import os

# ==========================================
# 1. SETTINGS & KEYS
# ==========================================
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN")

BASE_ID = "appXE1r8SZN0q1JzK"
TABLE_NAME = "tblFK1EC9tBrCYR6W"

PRICES = { "quarter": 150.00, "half": 250.00, "full": 450.00 }

# ==========================================
# 2. THE BRAIN (Extracting Info)
# ==========================================
def process_message(user_text, fb_profile_link): 
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    system_prompt = f"""
    You are an order-taking assistant for Shane's Firewood Business.
    Extract the following from the customer message:
    - name: Full name
    - city: City
    - address: Street address
    - phone: Phone number
    - amount: (quarter, half, or full)
    
    PRICING: Quarter: ${PRICES['quarter']}, Half: ${PRICES['half']}, Full: ${PRICES['full']}

    Respond with ONLY this exact JSON structure: 
    {{ 
      "name": "string or null", 
      "city": "string or null", 
      "address": "string or null", 
      "phone": "string or null", 
      "amount": "string or null", 
      "price": number or null, 
      "complete": true/false, 
      "reply": "your response to customer" 
    }} 
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ],
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)
    result['fb_link'] = fb_profile_link
    return result

# ==========================================
# 3. NORMALIZING (Matching Airtable Columns)
# ==========================================
def normalize_data(ai_response): 
    # Try different possible keys the AI might use
    name = ai_response.get("name") or ai_response.get("real_name")
    city = ai_response.get("city")
    address = ai_response.get("address") or ai_response.get("street_address")
    phone = ai_response.get("phone") or ai_response.get("phone_number")
    amount_raw = str(ai_response.get("amount")).lower()
    price = ai_response.get("price") or ai_response.get("total_price")
    fb_link = ai_response.get("fb_link")

    # This part handles the Amount (turning 'half' into 'half')
    # or you can change 0.5 back to "half" if your Airtable is a text field
    return {
        "Real Name": name,
        "FB Profile": fb_link,
        "City": city,
        "Street Address": address,
        "Phone": str(phone) if phone else None,
        "Amount": amount_raw, 
        "Price": float(price) if price else None,
        "Status": False
    }

# ==========================================
# 4. DATABASE PUSHER
# ==========================================
def save_to_airtable(normalized_data): 
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}" 
    headers = { 
        "Authorization": f"Bearer {AIRTABLE_TOKEN}", 
        "Content-Type": "application/json" 
    }

    # Filter out empty values so we don't send 'None' to Airtable
    fields = {k: v for k, v in normalized_data.items() if v is not None}
    payload = {"fields": fields}

    print(f"\n--- SENDING TO AIRTABLE ---\n{json.dumps(payload, indent=2)}")

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        print("✅ SUCCESS: Saved to Airtable!")
        return True
    else:
        print(f"❌ Airtable Error ({response.status_code}): {response.text}")
        return False
# ==========================================
# 5. TEST DATA POPULATOR
# ==========================================
if __name__ == "__main__": 
    test_scenarios = [
        {
            "text": "Hey I'm Sarah Miller. I need a full cord delivered to 456 Oak Ave in Quinlan. My cell is 555-0202",
            "link": "https://facebook.com/sarah.miller.99"
        },
        {
            "text": "Yo Shane, its Mike Jones. Need a quarter cord in Austin. 789 Maple Rd. 555-0303",
            "link": "https://facebook.com/mike.jones.firewood"
        },
        {
            "text": "Need fire wood. Half cord. 101 Lake Dr, Austin. 555-0404. Name is Ann Taylor.",
            "link": "https://facebook.com/ann.taylor.test"
        },
        {
            "text": "How much for a full cord? I'm in Quinlan. - Bobby Draper",
            "link": "https://facebook.com/bobby.d"
        }
    ]

    print("=" * 50)
    print("🚀 POPULATING DATABASE WITH TEST DATA")
    print("=" * 50)

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"Processing Scenario {i}...")
        ai_data = process_message(scenario['text'], scenario['link'])
        final_data = normalize_data(ai_data)
        
        if save_to_airtable(final_data):
            print(f"✅ Saved: {final_data['Real Name']}")
        else:
            print(f"❌ Failed to save record for scenario {i}")

    print("\nDONE! Go check your Airtable.")



# ==========================================
# 6. MAIN EXECUTION
# ==========================================
if __name__ == "__main__": 
    incoming_text = "Hey Shane my name is Jack. I live in Quinlan at 123 Pine St. I need a half cord. My number is 555-0101" 
    fb_link = "https://facebook.com/jack_smith_123"

    print("=" * 50)
    print("SHANES FIREWOOD ORDER SYSTEM")
    print("=" * 50)

    print(f"\nINCOMING MESSAGE: {incoming_text}")
    
    print("\nProcessing with AI...")
    ai_data = process_message(incoming_text, fb_link)

    print(f"AI SUGGESTED REPLY: {ai_data.get('reply')}")

    print("\nNormalizing for Airtable...")
    final_data = normalize_data(ai_data)

    print("\nSaving...")
    save_to_airtable(final_data)

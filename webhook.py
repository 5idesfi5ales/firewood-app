from flask import Flask, request, jsonify
import os
import json
# Import the logic we already built in your main.py
from main import process_message, normalize_data, save_to_airtable

app = Flask(__name__)

# This is a password you make up. You will give it to Facebook later.
VERIFY_TOKEN = "shanes_firewood_secret_123"

# 1. VERIFICATION (For Facebook to check if your server is real)
@app.route('/webhook', methods=['GET'])
def verify():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode == 'subscribe' and token == VERIFY_TOKEN:
        return app.response_class(challenge or "", status=200, mimetype='text/plain')
    else:
        return 'Verification failed', 403

# 2. MESSAGE RECEIVER
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    
    # Check if this is a message event
    if data.get('object') == 'page':
        for entry in data.get('entry', []):
            for messaging_event in entry.get('messaging', []):
                if messaging_event.get('message'):
                    # Get the raw text and sender ID
                    sender_id = messaging_event['sender']['id']
                    message_text = messaging_event['message'].get('text')
                    fb_link = f"https://facebook.com/{sender_id}"
                    
                    print(f"📥 New Message from {sender_id}: {message_text}")
                    
                    # RUN OUR ENTIRE PIPELINE
                    ai_raw = process_message(message_text, fb_link)
                    final_data = normalize_data(ai_raw)
                    save_to_airtable(final_data)
                    
                    # (Optional) Here you would add the code to send a reply back
                    
    return "EVENT_RECEIVED", 200

if __name__ == '__main__':
    app.run(port=5000)
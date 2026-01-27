import streamlit as st
import pandas as pd
import requests
import os
import json
import urllib.parse
from openai import OpenAI

# ==========================================
# 1. CONFIGURATION & SECRETS
# ==========================================
try:
    AIRTABLE_TOKEN = st.secrets["AIRTABLE_TOKEN"]
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    BASE_ID = "appXE1r8SZN0q1JzK"
    TABLE_NAME = "tblFK1EC9tBrCYR6W"
except:
    AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    BASE_ID = "appXE1r8SZN0q1JzK"
    TABLE_NAME = "tblFK1EC9tBrCYR6W"

# Page Setup
st.set_page_config(page_title="Shane's Firewood", page_icon="🪵", layout="centered")

# ==========================================
# 2. CUSTOM STYLING (The Full Suite)
# ==========================================
st.markdown("""
    <style>
    /* --- BASE THEME --- */
    .stApp { background-color: #0f172a; color: #e2e8f0; }
    
    /* Push content down for the HUD */
    .main .block-container { padding-top: 80px !important; }

    /* --- HUD HEADER ELEMENTS --- */
    /* 1. LEFT: Delivered Badge */
    .delivered-badge {
        position: fixed; top: 0; left: 20px;
        background-color: #22c55e; color: white;
        padding: 12px 20px; border-radius: 0 0 12px 12px;
        font-weight: 900; font-size: 14px; z-index: 1000000;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); text-transform: uppercase;
    }

    /* 2. RIGHT: Money Map Badge */
    .money-map-badge {
        position: fixed; top: 0; right: 70px;
        background-color: #ea580c; color: white;
        padding: 12px 20px; border-radius: 0 0 12px 12px;
        font-weight: 900; font-size: 14px; z-index: 1000000;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); text-transform: uppercase;
    }

    /* 3. CENTER: Title */
    .wood-header-center {
        position: fixed; top: 10px; left: 50%;
        transform: translateX(-50%); z-index: 1000000;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 900; font-size: 24px;
        color: #ea580c; text-shadow: 0px 0px 10px rgba(0,0,0,0.8);
        text-transform: uppercase; white-space: nowrap;
    }

    /* --- INPUTS & SELECTORS (Green Text / Grey BG) --- */
    div[data-baseweb="input"] > div, 
    div[data-baseweb="select"] > div {
        background-color: #334155 !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
    }
    input[type="number"], 
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div {
        color: #22c55e !important; /* Bright Green Text */
        font-weight: 900 !important;
        -webkit-text-fill-color: #22c55e !important;
    }
    div[data-baseweb="select"] svg,
    button[kind="secondary"] {
        color: #22c55e !important; fill: #22c55e !important;
        border-color: #334155 !important;
    }

    /* --- CARD & UI ELEMENTS --- */
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #1e293b;
        border: 1px solid #334155 !important;
        border-radius: 12px; padding: 16px;
    }
    
    /* Badges */
    .badge {
        display: inline-block; padding: 4px 8px; border-radius: 6px;
        font-size: 0.8rem; font-weight: bold; text-transform: uppercase;
        margin-bottom: 8px; color: white;
    }
    .badge-full { background-color: #dc2626; } 
    .badge-half { background-color: #ea580c; } 
    .badge-quarter { background-color: #f59e0b; color: black; }
    
    /* Metrics */
    div[data-testid="stMetric"] {
        background-color: #1e293b; border-radius: 10px;
        padding: 15px; border: 1px solid #334155;
    }
    div[data-testid="stMetricLabel"] { color: #94a3b8; }
    div[data-testid="stMetricValue"] { color: #ffffff; }

    /* Action Buttons */
    .action-btn {
        display: block; width: 100%; padding: 10px;
        text-align: center; border-radius: 8px;
        color: white !important; text-decoration: none !important;
        font-weight: bold; margin-top: 5px;
    }
    .btn-msg { background-color: #2563eb; }
    .btn-call { background-color: #059669; }
    .btn-chat { background-color: #475569; }
    .action-btn:hover { opacity: 0.9; }
    
    .stButton button { border-radius: 8px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. BACKEND FUNCTIONS
# ==========================================

def get_airtable_headers():
    return {
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json"
    }

def fetch_orders(view_completed=False):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    status_filter = "1" if view_completed else "0"
    params = {
        "filterByFormula": f"{{Status}} = {status_filter}",
        "sort[0][field]": "City",
        "sort[0][direction]": "asc"
    }
    try:
        response = requests.get(url, headers=get_airtable_headers(), params=params)
        response.raise_for_status()
        return response.json().get('records', [])
    except:
        return []

def update_order_status(record_id, is_complete=True):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}/{record_id}"
    requests.patch(url, headers=get_airtable_headers(), json={"fields": {"Status": is_complete}})

def create_order(data):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    response = requests.post(url, headers=get_airtable_headers(), json={"fields": data})
    return response.status_code == 200

def parse_order_with_ai(text, fb_link, prices):
    client = OpenAI(api_key=OPENAI_API_KEY)
    system_prompt = f"""
    You are an order-taking assistant for Shane's Firewood.
    Extract: name, city, address, phone, amount (quarter, half, full).
    Pricing: Quarter ${prices['quarter']}, Half ${prices['half']}, Full ${prices['full']}.
    Output JSON only: {{ "Real Name": str, "City": str, "Street Address": str, "Phone": str, "Amount": str, "Price": float, "reply": str }}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": text}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        result['FB Profile'] = fb_link
        result['Status'] = False 
        return result
    except Exception as e:
        return {"error": str(e)}

def get_badge_color(amount_str):
    amt = str(amount_str).lower()
    if "full" in amt: return "badge-full"
    if "half" in amt: return "badge-half"
    return "badge-quarter"

# ==========================================
# 4. MAIN APP INTERFACE
# ==========================================

# --- INJECT THE HEADER ---
st.markdown("""
    <div class="delivered-badge">✅ Delivered Today</div>
    <div class="wood-header-center">🪵 5IDES</div>
    <div class="money-map-badge">💰 Money Map</div>
""", unsafe_allow_html=True)

# --- SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("⚙️ Settings")
    with st.expander("Pricing Configuration"):
        p_q = st.number_input("Quarter Cord", value=150)
        p_h = st.number_input("Half Cord", value=250)
        p_f = st.number_input("Full Cord", value=450)
        PRICES = {"quarter": p_q, "half": p_h, "full": p_f}

# --- TABS ---
tab_dispatch, tab_add, tab_history = st.tabs(["🚚 Dispatch", "➕ New Order", "📜 History"])

# ----------------------------
# TAB 1: DISPATCH
# ----------------------------
with tab_dispatch:
    pending_records = fetch_orders(view_completed=False)
    
    if not pending_records:
        st.info("No active orders! Time to sell some wood.")
    else:
        # Stats
        df = pd.DataFrame([r['fields'] for r in pending_records])
        total_rev = df['Price'].sum() if 'Price' in df.columns else 0
        c1, c2, c3 = st.columns(3)
        c1.metric("Pending Orders", len(pending_records))
        c2.metric("Revenue", f"${total_rev:,.0f}")
        c3.metric("Cities", df['City'].nunique() if 'City' in df.columns else 0)
        st.divider()

        # Filter
        unique_cities = sorted(list(set(r['fields'].get('City', 'Unknown') for r in pending_records)))
        selected_city = st.selectbox("Filter by Delivery Zone:", ["All Cities"] + unique_cities)
        
        visible_records = pending_records
        if selected_city != "All Cities":
            visible_records = [r for r in pending_records if r['fields'].get('City') == selected_city]
            
            # GPS Button
            addresses = [f"{r['fields'].get('Street Address', '')}, {r['fields'].get('City', '')}" for r in visible_records]
            addresses = [a for a in addresses if len(a) > 5]
            if addresses:
                dest = urllib.parse.quote(addresses[-1])
                waypoints = "|".join([urllib.parse.quote(a) for a in addresses[:-1]])
                maps_url = f"https://www.google.com/maps/dir/?api=1&origin=My+Location&destination={dest}&waypoints={waypoints}"
                st.markdown(f"""
                    <a href="{maps_url}" target="_blank" style="text-decoration:none;">
                        <div style="background-color:#22c55e; color:white; text-align:center; padding:15px; border-radius:8px; font-weight:bold; margin-bottom:20px; display:block;">
                            🚀 LAUNCH GPS ROUTE ({len(addresses)} Stops)
                        </div>
                    </a>
                """, unsafe_allow_html=True)

        # --- ORDER CARDS ---
        for record in visible_records:
            data = record['fields']
            rid = record['id']
            
            with st.container(border=True):
                # Row 1: Name (Left) | Done Button (Right)
                c_top_left, c_top_right = st.columns([0.7, 0.3])
                
                with c_top_left:
                     st.markdown(f"<h2 style='margin:0; color:white;'>{data.get('Real Name', 'Unknown')}</h2>", unsafe_allow_html=True)
                     st.markdown(f"<p style='color:#94a3b8; margin:0;'>📍 {data.get('Street Address')}, {data.get('City')}</p>", unsafe_allow_html=True)

                with c_top_right:
                    # BIG "Done" Button at Top Right
                    if st.button("✅ Done", key=f"done_{rid}", type="primary", use_container_width=True):
                         update_order_status(rid, True)
                         st.toast(f"Completed {data.get('Real Name')}!")
                         st.rerun()

                st.write("") # Spacer

                # Row 2: Badge (Left) | Price (Right)
                c_mid1, c_mid2 = st.columns([0.4, 0.6])
                with c_mid1:
                    amt = data.get('Amount', 'Unknown')
                    badge_class = get_badge_color(amt)
                    st.markdown(f"<span class='badge {badge_class}'>{str(amt).upper()}</span>", unsafe_allow_html=True)
                with c_mid2:
                     price = data.get('Price', 0)
                     st.markdown(f"<h2 style='color:#22c55e; margin:0; text-align:right;'>${price:.0f}</h2>", unsafe_allow_html=True)

                st.divider()

                # Row 3: Action Buttons (HTML)
                c_msg, c_call, c_chat = st.columns(3)
                sms_body = urllib.parse.quote(f"Hi {data.get('Real Name')}, I'm Shane. Headed your way with your firewood!")
                
                with c_msg:
                    if data.get('Phone'):
                        st.markdown(f'<a href="sms:{data.get("Phone")}?&body={sms_body}" class="action-btn btn-msg">MESSAGE</a>', unsafe_allow_html=True)
                with c_call:
                    if data.get('Phone'):
                         st.markdown(f'<a href="tel:{data.get("Phone")}" class="action-btn btn-call">CALL</a>', unsafe_allow_html=True)
                with c_chat:
                    if data.get('FB Profile'):
                         st.markdown(f'<a href="{data.get("FB Profile")}" target="_blank" class="action-btn btn-chat">CHAT</a>', unsafe_allow_html=True)

# ----------------------------
# TAB 2: ADD ORDER
# ----------------------------
with tab_add:
    st.header("🤖 AI Order Entry")
    with st.form("ai_form"):
        raw_text = st.text_area("Customer Message", height=150, placeholder="Message text...")
        fb_link = st.text_input("Facebook/Profile Link (Optional)")
        submitted = st.form_submit_button("✨ Process Order")
    
    if submitted and raw_text:
        with st.spinner("Parsing..."):
            parsed_data = parse_order_with_ai(raw_text, fb_link, PRICES)
            if "error" in parsed_data:
                st.error(f"Error: {parsed_data['error']}")
            else:
                st.session_state['draft_order'] = parsed_data
                st.rerun()

    if 'draft_order' in st.session_state:
        draft = st.session_state['draft_order']
        st.subheader("📝 Review")
        c1, c2 = st.columns(2)
        with c1:
            draft['Real Name'] = st.text_input("Name", draft.get('Real Name'))
            draft['City'] = st.text_input("City", draft.get('City'))
        with c2:
            draft['Amount'] = st.selectbox("Amount", ["quarter", "half", "full"], index=["quarter", "half", "full"].index(draft.get('Amount', 'half')))
            draft['Price'] = st.number_input("Price", value=float(draft.get('Price', 0)))
        
        draft['Street Address'] = st.text_input("Address", draft.get('Street Address'))
        draft['Phone'] = st.text_input("Phone", draft.get('Phone'))
        st.text_area("Reply", draft.get('reply'), height=100)
        
        if st.button("💾 Save", type="primary"):
            save_data = {k: v for k, v in draft.items() if k not in ['reply', 'error']}
            if create_order(save_data):
                st.success("Saved!")
                del st.session_state['draft_order']
                st.rerun()
            else:
                st.error("Save failed.")

# ----------------------------
# TAB 3: HISTORY
# ----------------------------
with tab_history:
    st.header("📜 History")
    hist_records = fetch_orders(view_completed=True)
    if hist_records:
        df_hist = pd.DataFrame([r['fields'] for r in hist_records])
        st.dataframe(df_hist[['Real Name', 'City', 'Price', 'Status']], use_container_width=True, hide_index=True)
    else:
        st.info("No history found.")
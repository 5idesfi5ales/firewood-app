import streamlit as st
import pandas as pd
import requests
import os
import urllib.parse

# ==========================================
# 1. SETTINGS & BRUTE-FORCE STYLING
# ==========================================
AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN")
BASE_ID = "appXE1r8SZN0q1JzK"
TABLE_NAME = "tblFK1EC9tBrCYR6W"

st.set_page_config(page_title="5IDES", page_icon="🪵", layout="centered")

st.markdown(f"""
    <style>
    /* Global Dark Slate Background */
    .stApp {{ background-color: #0f172a !important; color: #ffffff !important; }}
    
    /* Dark Grey Top Bar */
    [data-testid="stHeader"] {{ background-color: #1e293b !important; }}
    
    /* 5IDES wood app - Orange with Brown Glow */
    .wood-title {{
        color: #ea580c !important; 
        font-family: 'Arial Black', sans-serif;
        font-size: 45px !important;
        font-weight: 900 !important;
        text-align: center;
        text-shadow: 3px 3px 6px #5d4037, -3px -3px 6px #5d4037 !important;
        margin-bottom: 20px;
    }}

    /* Sidebar Orange Headers & Gold Toggle */
    [data-testid="stSidebar"] {{ background-color: #0f172a !important; }}
    [data-testid="stSidebar"] .stExpander {{ background-color: #f97316 !important; border-radius: 10px !important; }}
    [data-testid="stSidebar"] .stExpander summary p {{ color: white !important; font-weight: 900 !important; }}
    button[kind="header"] svg {{ fill: #b8860b !important; }}

    /* Tab Styling (Orange Highlights) */
    .stTabs [data-baseweb="tab-list"] {{ background-color: #1e293b; border-radius: 12px; padding: 5px; }}
    .stTabs [aria-selected="true"] {{ background-color: #ea580c !important; color: white !important; border-radius: 8px; }}

    /* Revenue Banner (Orange) */
    .revenue-banner {{
        background-color: #ea580c;
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
    }}

    /* City Table with Green Totals */
    .city-table {{ width: 100%; border-radius: 15px; overflow: hidden; background-color: #1e293b; }}
    .city-table th {{ background-color: #334155; padding: 12px; color: white; }}
    .city-table td {{ padding: 12px; border-bottom: 1px solid #334155; }}
    .green-total {{ color: #22c55e !important; font-weight: 900; }}

    /* Integrated Customer Card */
    .card-top {{
        background-color: #1e293b;
        padding: 25px 25px 5px 25px;
        border-radius: 20px 20px 0 0;
        border: 1px solid #334155;
        border-bottom: none;
    }}
    .card-bottom {{
        background-color: #1e293b;
        padding: 0px 25px 25px 25px;
        border-radius: 0 0 20px 20px;
        border: 1px solid #334155;
        border-top: none;
        margin-bottom: 20px;
    }}

    /* Nested Action Buttons */
    .btn-row {{ display: flex; gap: 10px; margin-top: 15px; }}
    .btn-ui {{
        flex: 1; padding: 12px; border-radius: 10px;
        text-decoration: none !important; font-weight: 900;
        text-align: center; color: white !important; font-size: 14px;
    }}
    .btn-msg {{ background-color: #2563eb; }}
    .btn-call {{ background-color: #059669; }}
    .btn-chat {{ background-color: #475569; }}

    /* Checkbox inside card */
    .stCheckbox label {{ color: #ffffff !important; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. DATA ENGINE
# ==========================================
if 'delivered_list' not in st.session_state:
    st.session_state['delivered_list'] = []

def fetch_data():
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}
    params = {"filterByFormula": "{Status} = 0"}
    res = requests.get(url, headers=headers, params=params)
    return [r['fields'] for r in res.json().get('records', [])] if res.status_code == 200 else []

def calc_price(amt, prices):
    return prices.get(str(amt).lower().strip(), 0)

# ==========================================
# 3. SIDEBAR (Orange Settings & Gold Arrow)
# ==========================================
with st.sidebar:
    with st.expander("💰 Price Settings", expanded=False):
        q_p = st.number_input("Quarter Cord", value=150)
        h_p = st.number_input("Half Cord", value=250)
        f_p = st.number_input("Full Cord", value=450)
        prices = {"quarter": q_p, "half": h_p, "full": f_p}

    raw_data = fetch_data()
    selected_city = None
    
    if raw_data:
        df = pd.DataFrame(raw_data)
        df['Price'] = df['Amount'].apply(lambda x: calc_price(x, prices))
        pending_df = df[~df['Real Name'].isin(st.session_state['delivered_list'])]

        with st.expander("📍 Route Selector", expanded=True):
            unique_cities = sorted(pending_df['City'].unique())
            selected_city = st.selectbox("Dispatch City:", ["Choose..."] + unique_cities)

# ==========================================
# 4. MAIN APP
# ==========================================
st.markdown('<h1 class="wood-title">🪵 5IDES wood app</h1>', unsafe_allow_html=True)

tab_map, tab_history = st.tabs(["💰 Money Map", "✅ Delivered Today"])

# --- TAB 1: MONEY MAP ---
with tab_map:
    if pending_df.empty:
        st.info("No orders pending.")
    else:
        # ORANGE REVENUE BANNER
        st.markdown(f"""
            <div class="revenue-banner">
                <p style="text-transform: uppercase; font-size: 14px; font-weight: 900; margin:0; opacity: 0.8;">Uncollected Revenue</p>
                <h1 style="margin:0; font-size: 70px; font-weight: 900;">${pending_df['Price'].sum():,.0f}</h1>
            </div>
        """, unsafe_allow_html=True)

        # CITY TABLE WITH GREEN TOTALS
        st.subheader("📊 Delivery Zones")
        city_sum = pending_df.groupby('City').agg(Orders=('Real Name', 'count'), Total=('Price', 'sum')).sort_values('Total', ascending=False)
        
        table_html = "<table class='city-table'><tr><th>City</th><th>Orders</th><th style='text-align:right;'>Total</th></tr>"
        for city, row in city_sum.iterrows():
            table_html += f"<tr><td>{city}</td><td style='text-align:center;'>{row['Orders']}</td><td class='green-total' style='text-align:right;'>${row['Total']:,.0f}</td></tr>"
        table_html += "</table>"
        st.markdown(table_html, unsafe_allow_html=True)

        if selected_city and selected_city != "Choose...":
            city_data = pending_df[pending_df['City'] == selected_city]
            st.divider()
            
            # Navigate Button
            addrs = [f"{r['Street Address']}, {r['City']}" for _, r in city_data.iterrows()]
            dest = urllib.parse.quote(addrs[-1])
            wpts = "|".join([urllib.parse.quote(a) for a in addrs[:-1]])
            maps_url = f"https://www.google.com/maps/dir/?api=1&origin=My+Location&destination={dest}&waypoints={wpts}"
            st.link_button(f"🚀 NAVIGATE {selected_city.upper()}", maps_url, use_container_width=True)

            for idx, row in city_data.iterrows():
                # Card Top
                sms_body = urllib.parse.quote(f"Hi {row['Real Name']}, I'm Shane. Headed your way!")
                st.markdown(f"""
                    <div class="card-top">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                                <h1 style="margin:0; font-weight: 900; font-size: 32px;">{row['Real Name']}</h1>
                                <p style="margin:0; color: #94a3b8;">📍 {row['Street Address']}</p>
                                <span style="background: #ea580c; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 900;">{str(row['Amount']).upper()}</span>
                            </div>
                            <div style="text-align: right;">
                """, unsafe_allow_html=True)
                
                # Checkbox nested in Card (Right above Price)
                if st.checkbox("Mark Delivered ✅", key=f"del_{row['Real Name']}"):
                    st.session_state['delivered_list'].append(row['Real Name'])
                    st.rerun()

                st.markdown(f"""
                                <h1 style="margin:0; font-weight: 900; font-size: 45px; color: white;">${row['Price']}</h1>
                            </div>
                        </div>
                        <div class="btn-row">
                            <a href="sms:{row['Phone']}?&body={sms_body}" class="btn-ui btn-msg">MESSAGE</a>
                            <a href="tel:{row['Phone']}" class="btn-ui btn-call">CALL</a>
                            <a href="{row.get('FB Profile','#')}" target="_blank" class="btn-ui btn-chat">CHAT</a>
                        </div>
                    </div>
                    <div class="card-bottom"></div>
                """, unsafe_allow_html=True)

# --- TAB 2: DELIVERED TODAY ---
with tab_history:
    st.title("✅ Completed Today")
    for name in st.session_state['delivered_list']:
        st.success(f"DELIVERED: {name}")
import streamlit as st
import pandas as pd
import numpy as np
import os
import html

# --- 1. SETUP & CACHING ---
st.set_page_config(page_title="TNP Race Results", layout="wide")

# --- 0. EXTERNAL LINKS ---
# We use columns to keep the buttons in a tight row at the top
link_col1, link_col2, link_col3, _ = st.columns([2, 1, 1, 4])  

with link_col1:
    logo_path = "icons/TNP.png" 
    if os.path.exists(logo_path):
        st.image(logo_path, width=200)

with link_col2:
    st.link_button("TNP website", "https://team-not-pogi-hub.vercel.app/")

st.divider() # Adds a clean line between your external links and the app navigation

@st.cache_data
# def load_excel_data(file_path):
#     """Caches the excel reading so switching sheets is nearly instant."""
#     if os.path.exists(file_path):
#         return pd.read_excel(file_path, sheet_name=None)
#     return None
@st.cache_data
def load_excel_data(file_path, last_modified):
    """
    By adding last_modified as an argument, Streamlit will 
    automatically re-run this function whenever the file changes.
    """
    if os.path.exists(file_path):
        return pd.read_excel(file_path, sheet_name=None)
    return None

def clean_data(df):
    """Standardized cleaning for all sheets."""
    if 'name' in df.columns:
        df['name'] = df['name'].apply(lambda x: html.unescape(str(x)))
    if 'team_name' in df.columns:
        df['team_name'] = df['team_name'].apply(lambda x: html.unescape(str(x)) if pd.notnull(x) else "")
    return df.replace(['None', 'none', 'NaN'], '')

def create_rider_links(row):
    name = html.unescape(str(row['name']))
    zwift_id = row.get('zwift_id')

    if pd.isna(zwift_id) or zwift_id == "" or zwift_id == 0:
        return name
    
    # URLs
    zp_url = f"https://zwiftpower.com/profile.php?z={int(zwift_id)}"
    zr_url = f"https://www.zwiftracing.app/riders/{int(zwift_id)}"

    
    return f"{name} ([ZR]({zp_url}))"# [ZRapp]({zr_url}))"

# --- 2. THE LOGIC ENGINE (Configuration) ---
# Add new races here. The app will automatically handle the rest.
EVENT_CONFIG = {
    "The Next Peak": {
        "file": "TheNextPeak/TheNextPeak__March_results.xlsx",
        "default_sheet": "GC",
        "sorting": lambda sheet: (['pen', 'final_points'], [True, False]) if sheet == "GC" else (['pen', 'gap'], [True, True]),
    },
    "London-Watopia": {
        "file": "MarchSeries/London_Watopia.xlsx",
        "default_sheet": "GC",
        "sorting": lambda sheet: 
            (['pen', 'time_offset'], [True, True]) if sheet == "GC" else
            (['pen', 'races', 'egap'], [True, False, True]) if sheet == "egap" else
            (['pen', 'races', 'time_offset'], [True, False, True]) if sheet == "Team GC" else
            (['pen', f"time{sheet[-1]}"], [True, True]) if "Round" in sheet else
            (['pen', 'Total Points'], [True, False])
    },
    "Spring Classics": {
        "file": "SpringClassics/SpringClassics.xlsx",
        "default_sheet": "Ride the White Roads race 1",
        "sorting": lambda sheet: (['pen', 'gap'],[True, True]) if 'race' in sheet else (['pen', 'gap'],[True, True])
    },
    "Total Non-Stop Power (iTT)": {
        "file": "NonStopPower/NonStopPower.xlsx",
        "default_sheet": "Overall",
        "sorting": lambda sheet: (['pen', 'gap'],[True, True]) if 'race' in sheet else (['pen', 'gap'],[True, True])
    },
    "Power Test (Beta)": {
        "file": "PowerTest/PowerTest.xlsx",
        "default_sheet": "The Grade",
        "sorting": lambda sheet: (['pen', 'time'],[True, False]) if 'race' in sheet else (['pen', 'time'],[True,False])
    }
}

# --- 3. URL & NAVIGATION ---
# Handle Event selection via URL
event_list = list(EVENT_CONFIG.keys())
url_event = st.query_params.get("event", event_list[0])
event_idx = event_list.index(url_event) if url_event in event_list else 0

st.write("### Select Event")
selected_event = st.radio("Event", options=event_list, index=event_idx, horizontal=True, label_visibility="collapsed")
st.query_params["event"] = selected_event

# Load Data
config = EVENT_CONFIG[selected_event]
file_path = config["file"]

# Get the last modification time of the file
if os.path.exists(file_path):
    mtime = os.path.getmtime(file_path)
else:
    mtime = 0

# Pass that time into the function
all_sheets = load_excel_data(file_path, mtime)

# config = EVENT_CONFIG[selected_event]
# all_sheets = load_excel_data(config["file"])

if all_sheets is None:
    st.error(f"File not found: {config['file']}")
    st.stop()

# Handle Sheet selection via URL
sheet_names = list(all_sheets.keys())
url_sheet = st.query_params.get("sheet", config["default_sheet"])
sheet_idx = sheet_names.index(url_sheet) if url_sheet in sheet_names else 0

selected_sheet = st.selectbox("Select Leaderboard View", options=sheet_names, index=sheet_idx)
st.query_params["sheet"] = selected_sheet

# --- 4. DATA PROCESSING ---
df = all_sheets[selected_sheet]
if selected_sheet != "Team GC": # Skip cleaning for specific aggregate sheets if needed
    df = clean_data(df)

# if 'zwift_id' in df.columns:
#     df['name'] = df.apply(create_rider_links, axis=1)

# Apply Sorting from Config
sort_cols, sort_orders = config["sorting"](selected_sheet)
df = df.sort_values(by=sort_cols, ascending=sort_orders).reset_index(drop=True)

# --- 5. UI & FILTERING ---
st.title(f"🏆 {selected_event}: {selected_sheet}")
m1, m2, m3, m4 = st.columns(4)
st.divider()

if 'pen' in df.columns:
    categories = sorted(df['pen'].unique().tolist())
    selected_cats = st.multiselect("Filter by pen", options=categories, default=categories)
    filtered_df = df[df['pen'].isin(selected_cats)].copy().reset_index(drop=True)
else:
    filtered_df = df.copy()

# Metric Logic
if not filtered_df.empty:
    m1.metric("Total Participants", len(df))
    if 'pen' in filtered_df.columns:
        m2.metric("Filtered Count", len(filtered_df))
    if selected_event == "Spring Classics" or selected_event == "Total Non-Stop Power (iTT)":
        if 'avg_power' in filtered_df.columns:
            m3.metric("Highest Power", str(
                      np.round(filtered_df['avg_power'].loc[filtered_df['avg_power'] == filtered_df['avg_power'].max()].iloc[0])) + "W",
                      filtered_df['name'].loc[filtered_df['avg_power'] == filtered_df['avg_power'].max()].iloc[0])
        if 'avg_wkg' in filtered_df.columns:
            m4.metric("Highest W/kg", str(
                      np.round(filtered_df['avg_wkg'].loc[filtered_df['avg_wkg'] == filtered_df['avg_wkg'].max()].iloc[0],3)) + "W/kg",
                      filtered_df['name'].loc[filtered_df['avg_wkg'] == filtered_df['avg_wkg'].max()].iloc[0])
    elif selected_event == "Power Test (Beta)":
        if 'Watts' in filtered_df.columns:
            m3.metric("Highest Power", str(
                      np.round(filtered_df['Watts'].loc[filtered_df['Watts'] == filtered_df['Watts'].max()].iloc[0])) + "W",
                      filtered_df['name'].loc[filtered_df['Watts'] == filtered_df['Watts'].max()].iloc[0])
        if 'W/kg' in filtered_df.columns:
            m4.metric("Highest W/kg", str(
                      np.round(filtered_df['W/kg'].loc[filtered_df['W/kg'] == filtered_df['W/kg'].max()].iloc[0],3)) + "W/kg",
                      filtered_df['name'].loc[filtered_df['W/kg'] == filtered_df['W/kg'].max()].iloc[0])
    else:
        if 'name' in filtered_df.columns:
            m3.metric("Current Leader", filtered_df['name'].iloc[0])
        if 'total_points' in filtered_df.columns:
            m4.metric("Top Points", f"{filtered_df['total_points'].max()} pts")
        elif 'final_points' in filtered_df.columns:
            m4.metric("Top Points", f"{filtered_df['final_points'].max()} pts")

# --- 6. STYLING & DISPLAY ---
def highlight_podium(row):
    colors = {0: 'background-color: #D4AF37; color: black; font-weight: bold', 
              1: 'background-color: #C0C0C0; color: black', 
              2: 'background-color: #CD7F32; color: black'}
    return [colors.get(row.name, '')] * len(row)

# Standardize column configs for the dataframe
column_main_config = {
    "name": "Rider",
    "team_name": "Team",
    "total_points": st.column_config.NumberColumn("Points", format="%d ⭐"),
    "final_points": st.column_config.NumberColumn("Points", format="%d ⭐"),
    "total_time": "Time",
    "time_offset": "Gap",
}

st.dataframe(
    filtered_df.style.apply(highlight_podium, axis=1),
    use_container_width=True,
    hide_index=False,
    column_config=column_main_config
)

st.caption(f"Showing results for {selected_event} | {selected_sheet}")

import streamlit as st
import pandas as pd
import numpy as np
import os
import html

# Import your event configs and UI helper
from event_configs import EVENT_CONFIG, render_event_info

# --- 0. SETUP & CACHING ---
st.set_page_config(page_title="TNP Race Results", layout="wide")

# --- 1. EXTERNAL LINKS ---
link_col1, link_col2, link_col3, _ = st.columns([2, 1, 1, 4])  

with link_col1:
    logo_path = "icons/TNP.png" 
    if os.path.exists(logo_path):
        st.image(logo_path, width=100)

with link_col2:
    st.link_button("TNP website", "https://team-not-pogi-hub.vercel.app/")

st.markdown("<hr style='margin-top: 5px; margin-bottom: 5px;'>", unsafe_allow_html=True)

@st.cache_data
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

# --- 3. URL & NAVIGATION ---
event_list = list(EVENT_CONFIG.keys())
url_event = st.query_params.get("event", event_list[0])
event_idx = event_list.index(url_event) if url_event in event_list else 0

selected_event = st.radio("**Select Event**", options=event_list, index=event_idx, horizontal=True)
st.query_params["event"] = selected_event

# Load Data
config = EVENT_CONFIG[selected_event]
file_path = config["file"]

if os.path.exists(file_path):
    mtime = os.path.getmtime(file_path)
else:
    mtime = 0

all_sheets = load_excel_data(file_path, mtime)

if all_sheets is None:
    st.error(f"File not found: {config['file']}")
    st.stop()

# --- RENDER EVENT RULES / IMAGE ---
render_event_info(selected_event)
# -----------------------------------

# Handle Sheet selection via URL
sheet_names = list(all_sheets.keys())
url_sheet = st.query_params.get("sheet", config["default_sheet"])
sheet_idx = sheet_names.index(url_sheet) if url_sheet in sheet_names else 0

selected_sheet = st.selectbox("Select Leaderboard View", options=sheet_names, index=sheet_idx)
st.query_params["sheet"] = selected_sheet

# --- 4. DATA PROCESSING ---
df = all_sheets[selected_sheet]
if selected_sheet != "Team GC":
    df = clean_data(df)

# 1. Create a temporary numeric time column for accurate sorting
if 'total_time' in df.columns:
    # If a time is only "MM:SS.ms" (1 colon), prepend "00:" so pandas reads it as "HH:MM:SS.ms"
    time_str = df['total_time'].astype(str).apply(lambda x: '00:' + x if str(x).count(':') == 1 else x)
    df['temp_sort_time'] = pd.to_timedelta(time_str, errors='coerce')

# Apply Sorting from Config
sort_cols, sort_orders = config["sorting"](selected_sheet)

# 2. If 'total_time' is in the sorting logic, swap it for our temporary time column
if 'total_time' in sort_cols and 'temp_sort_time' in df.columns:
    sort_cols = ['temp_sort_time' if c == 'total_time' else c for c in sort_cols]

# 3. Sort and reset index
df = df.sort_values(by=sort_cols, ascending=sort_orders).reset_index(drop=True)

# --- 5. UI & FILTERING ---
st.title(f"🏆 {selected_event}: {selected_sheet}")
m1, m2, m3, m4 = st.columns(4)
st.divider()

# Check which columns exist to build our filters
has_pen = 'pen' in df.columns
has_category = 'category' in df.columns
has_age = 'age' in df.columns

if has_pen or has_category or has_age:
    # Create two side-by-side columns for the filters
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    # Initialize defaults
    selected_pen = 'All'
    selected_cat = 'All'
    selected_age = 'All'
    
    if has_pen:
        with filter_col1:
            pen_options = ['All'] + sorted(df['pen'].dropna().unique().tolist())
            selected_pen = st.selectbox("Filter by pen", options=pen_options, index=0)

    if selected_sheet == "GC":       
        if has_category:
            if selected_sheet is not "KQOM" and selected_sheet is not "Sprints":
                with filter_col2:
                    cat_options = ['All'] + sorted(df['category'].dropna().unique().tolist())
                    selected_cat = st.selectbox("Filter by category", options=cat_options, index=0)
        
        if has_age:
            if selected_sheet is not "KQOM" and selected_sheet is not "Sprints":
                with filter_col3:
                    age_options = ['All'] + sorted(df['age'].dropna().unique().tolist())
                    selected_age = st.selectbox("Filter by age group", options=age_options, index=0)

    # Apply the filters to a copy of the dataframe
    filtered_df = df.copy()
    
    if selected_pen != 'All':
        filtered_df = filtered_df[filtered_df['pen'] == selected_pen]
        
    if selected_cat != 'All':
        filtered_df = filtered_df[filtered_df['category'] == selected_cat]
    
    if selected_age != 'All':
        filtered_df = filtered_df[filtered_df['age'] == selected_age]
        
    # Re-sort strictly by time if 'All' is selected for either filter
    if selected_pen == 'All' or selected_cat == 'All':
        if 'temp_sort_time' in filtered_df.columns:
            if selected_sheet == "GC":
                filtered_df = filtered_df.sort_values(by=['races','temp_sort_time'], ascending=[False,True])
            if selected_sheet == "Team GC":
                filtered_df = filtered_df.sort_values(by=['racers','temp_sort_time'], ascending=[False,True])
        elif 'total_time' in filtered_df.columns:
            if selected_sheet == "GC":
                filtered_df = filtered_df.sort_values(by=['races','total_time'], ascending=[False,True])
            elif selected_sheet == "Team GC":
                filtered_df = filtered_df.sort_values(by=['racers','total_time'], ascending=[False,True])
            
    filtered_df = filtered_df.reset_index(drop=True)
else:
    filtered_df = df.copy()

if 'temp_sort_time' in filtered_df.columns and not filtered_df.empty:
    # Find the max races and create a mask for those riders
    if 'races' in filtered_df.columns:
        max_races = filtered_df['races'].max()
        mask = filtered_df['races'] == max_races
    elif 'racers' in filtered_df.columns:
        max_races = filtered_df['racers'].max()
        mask = filtered_df['racers'] == max_races
    
    # Calculate the raw gap using the Timedelta column 
    # (Index 0 is guaranteed to be the fastest since we just sorted it)
    fastest_time = filtered_df.loc[0, 'temp_sort_time']
    raw_gaps = filtered_df.loc[mask, 'temp_sort_time'] - fastest_time
    
    # Helper function to convert Timedelta back to "+HH:MM:SS.ms" or "+MM:SS.ms"
    def format_gap(td):
        if pd.isna(td) or td.total_seconds() == 0:
            return "00.000" # Leader / No gap
        
        total_sec = td.total_seconds()
        h = int(total_sec // 3600)
        m = int((total_sec % 3600) // 60)
        s = total_sec % 60
        
        if h > 0:
            return f"+{h:02d}:{m:02d}:{s:06.3f}"
        else:
            return f"+{m:02d}:{s:06.3f}"
            
    # Apply the formatted string back to your gap column
    filtered_df.loc[mask, 'time_offset'] = raw_gaps.apply(format_gap)

# 4. Clean up by dropping the temporary column so it doesn't show in the UI
if 'temp_sort_time' in df.columns:
    df = df.drop(columns=['temp_sort_time'])
if 'temp_sort_time' in filtered_df.columns:
    filtered_df = filtered_df.drop(columns=['temp_sort_time'])

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
    else:
        if 'name' in filtered_df.columns:
            m3.metric("Current Leader", filtered_df['name'].iloc[0])
        if 'total_points' in filtered_df.columns:
            m4.metric("Top Points", f"{filtered_df['total_points'].max()} pts")
        elif 'final_points' in filtered_df.columns:
            m4.metric("Top Points", f"{filtered_df['final_points'].max()} pts")
        elif 'W/kg' in filtered_df.columns:
            m4.metric("Highest W/kg", str(
                      np.round(filtered_df['W/kg'].loc[filtered_df['W/kg'] == filtered_df['W/kg'].max()].iloc[0],3)) + " W/kg",
                      filtered_df['name'].loc[filtered_df['W/kg'] == filtered_df['W/kg'].max()].iloc[0])

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

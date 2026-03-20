import streamlit as st
import pandas as pd
import os
import html

# --- 1. SETUP & CACHING ---
st.set_page_config(page_title="TNP Race Results", layout="wide")

# --- 0. EXTERNAL LINKS ---
# We use columns to keep the buttons in a tight row at the top
link_col1, link_col2, link_col3, _ = st.columns([1, 1, 1, 4]) 

with link_col1:
    st.link_button("TNP website", "https://team-not-pogi-hub.vercel.app/")

with link_col2:
    st.link_button("TNP Results", "https://team-not-pogi-hub.vercel.app/results")

st.divider() # Adds a clean line between your external links and the app navigation

@st.cache_data
def load_excel_data(file_path):
    """Caches the excel reading so switching sheets is nearly instant."""
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

# --- 2. THE LOGIC ENGINE (Configuration) ---
# Add new races here. The app will automatically handle the rest.
EVENT_CONFIG = {
    "The Next Peak": {
        "file": "TheNextPeak/TheNextPeak__March_results.xlsx",
        "default_sheet": "GC",
        "sorting": lambda sheet: (['pen', 'total_points'], [True, False]) if sheet == "GC" else (['pen', 'gap'], [True, True])
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
all_sheets = load_excel_data(config["file"])

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
    if 'name' in filtered_df.columns:
        m3.metric("Current Leader", filtered_df['name'].iloc[0])
    if 'total_points' in filtered_df.columns:
        m4.metric("Top Points", f"{filtered_df['total_points'].max()} pts")

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


# import streamlit as st
# import pandas as pd
# import os
# import html

# # --- 1. SETUP ---
# st.set_page_config(page_title="TNP Race Results", layout="wide")

# # Map your "Buttons" to the actual file paths
# # You can add as many as you want here!
# available_events = {
#     "The Next Peak": "TheNextPeak/TheNextPeak__March_results.xlsx",
#     "London-Watopia": "MarchSeries/London_Watopia.xlsx"
# }

# # --- 2. URL PARAMETER LOGIC ---
# # Get current event from URL (if it exists)
# event_list = list(available_events.keys())
# url_event = st.query_params.get("event")

# # Determine which index the radio button should start at
# default_event_index = 0
# if url_event in event_list:
#     default_event_index = event_list.index(url_event)

# # --- 3. TOP-LEVEL NAVIGATION ---
# st.write("### Select Event")
# selected_event_name = st.radio(
#     "Select Event",
#     options=event_list,
#     index=default_event_index, # Starts at the URL choice
#     horizontal=True,
#     label_visibility="collapsed"
# )

# # Update the URL immediately so the user can copy/paste it
# st.query_params["event"] = selected_event_name

# # # --- 2. TOP-LEVEL NAVIGATION (FILES) ---
# # st.write("### Select Event")
# # selected_event_name = st.radio(
# #     "Select Event",
# #     options=list(available_events.keys()),
# #     horizontal=True,
# #     label_visibility="collapsed" # Hides the 'Select Event' text for a cleaner button look
# # )

# # Load the chosen file
# file_path = available_events[selected_event_name]

# # Safety check in case a file is missing
# if not os.path.exists(file_path):
#     st.error(f"File not found: {file_path}")
#     st.stop()

# # Replace this with your actual data loading: df = pd.read_csv("your_data.csv")
# # For this example, I'll assume your dataframe 'df' is already loaded.
# all_sheets = pd.read_excel(file_path, sheet_name=None)

# def clean_data(df):
#     # Decode HTML entities in names (converts &#127793; to emojis)
#     df['name'] = df['name'].apply(lambda x: html.unescape(str(x)))
#     df['team_name'] = df['team_name'].apply(lambda x: html.unescape(str(x)))
    
#     # Clean up 'None' strings and NaNs for a cleaner UI
#     df = df.replace(['None', 'none', 'NaN'], '')
#     return df

#     # --- 4. STYLING LOGIC ---
# def highlight_podium(row):
#     """Applies Gold, Silver, and Bronze colors to the top 3 rows."""
#     gold = 'background-color: #D4AF37; color: black; font-weight: bold'
#     silver = 'background-color: #C0C0C0; color: black'
#     bronze = 'background-color: #CD7F32; color: black'
    
#     if row.name == 0:
#         return [gold] * len(row)
#     elif row.name == 1:
#         return [silver] * len(row)
#     elif row.name == 2:
#         return [bronze] * len(row)
#     return [''] * len(row)

# if "TheNextPeak" in file_path:
#     # Dropdown to select sheet - defaults to 'GC'
#     sheet_names = list(all_sheets.keys())
#     default_index = sheet_names.index("GC") if "GC" in sheet_names else 0

#     selected_sheet = st.selectbox(
#         "Select Leaderboard View", 
#         options=sheet_names, 
#         index=default_index
#     )

#     # Grab the active dataframe
#     df = all_sheets[selected_sheet]

#     df = clean_data(df)

#     # --- 2. HEADER & METRICS ---

#     if selected_sheet == "GC":
#         df = df.sort_values(by=['pen','total_points'], ascending=[True,False]).reset_index(drop=True)
#     else:  
#         df = df.sort_values(by=['pen','gap'], ascending=[True,True]).reset_index(drop=True)

#     # --- 5. HEADER & METRICS ---
#     st.title(f"🏆 {selected_event_name}: {selected_sheet}")
#     # Create top-level metrics for quick insights
#     m1, m2, m3, m4 = st.columns(4)

#     st.divider()

#     # --- 3. FILTERING UI ---
#     # Sidebar or top-level filter
#     categories = sorted(df['pen'].unique().tolist())
#     selected_cats = st.multiselect(
#         "Filter by pen", 
#         options=categories, 
#         default=categories
#     )

#     # Filter the data
#     filtered_df = df[df['pen'].isin(selected_cats)].copy()
#     # Ensure it's sorted by points or time for the podium logic
#     if selected_sheet == "GC":
#         filtered_df = filtered_df.sort_values(by=['pen','total_points'], ascending=[True,False]).reset_index(drop=True)
#     else:
#         filtered_df = filtered_df.sort_values(by=['pen','gap'], ascending=[True,True]).reset_index(drop=True)

#     if len(filtered_df)>0:
#         if selected_sheet == "GC":
#             m1.metric("Pen", f"{filtered_df['pen'].iloc[0]}")
#             m2.metric("Total Participants", len(df))
#             m3.metric("Top Points", f"{filtered_df['total_points'].max()} pts")
#             m4.metric("Current Leader", f"{filtered_df['name'].iloc[0]}")
#         else:
#             m1.metric("Pen", f"{filtered_df['pen'].iloc[0]}")
#             m2.metric("Total Participants", len(df))
#             time_str = f"time{int(selected_sheet[-1])}"
#             m3.metric("Best Time", f"{filtered_df[time_str].iloc[0]}")
#             m4.metric("Fastest Rider", f"{filtered_df['name'].iloc[0]}")

#     # Apply the styles
#     styled_df = filtered_df.style.apply(highlight_podium, axis=1)

#     # --- 5. DISPLAY TABLE ---
#     if selected_sheet == "GC":
#         st.dataframe(
#             styled_df,
#             use_container_width=True,
#             hide_index=False, # Removes the 0, 1, 2... column
#             column_config={
#                 "name": "Rider",
#                 "team_name": "Team",
#                 "total_points": st.column_config.NumberColumn("Points", format="%d ⭐"),
#                 "total_time": "Total Time (s)",
#             }
#         )
#     else:
#         time_str = f"time{int(selected_sheet[-1])}"
#         st.dataframe(
#             styled_df,
#             use_container_width=True,
#             hide_index=False, # Removes the 0, 1, 2... column
#             column_config={
#                 "name": "Rider",
#                 "team_name": "Team",
#                 time_str: "Time (s)",
#             }
#         )

#     st.caption(f"Showing {len(filtered_df)} of {len(df)} results.")

# elif "London-Watopia" in selected_event_name:
#     # Dropdown to select sheet - defaults to 'GC'
#     sheet_names = list(all_sheets.keys())
#     default_index = sheet_names.index("GC") if "GC" in sheet_names else 0

#     selected_sheet = st.selectbox(
#         "Select Leaderboard View", 
#         options=sheet_names, 
#         index=default_index
#     )

#     # Grab the active dataframe
#     df = all_sheets[selected_sheet]

#     if selected_sheet != "Team GC":
#         df = clean_data(df)

#     if selected_sheet == "GC":
#         df = df.sort_values(by=['pen','time_offset'], ascending=[True,True]).reset_index(drop=True)
#     elif selected_sheet == "egap":  
#         df = df.sort_values(by=['pen','races','egap'], ascending=[True,False,True]).reset_index(drop=True)
#     elif selected_sheet == "Team GC":  
#         df = df.sort_values(by=['pen','races','time_offset'], ascending=[True,False,True]).reset_index(drop=True)
#     elif "Round" in selected_sheet:
#         time_str = f"time{str(int(selected_sheet[-1]))}"
#         df = df.sort_values(by=['pen',time_str], ascending=[True,True]).reset_index(drop=True)
#     else:
#         df = df.sort_values(by=['pen', 'Total Points'], ascending = [True, False]).reset_index(drop=True)

#     # --- 5. HEADER & METRICS ---
#     st.title(f"🏆 {selected_event_name}: {selected_sheet}")
#     # Create top-level metrics for quick insights
#     m1, m2, m3 = st.columns(3)

#     st.divider()

#     # --- 3. FILTERING UI ---
#     # Sidebar or top-level filter
#     categories = sorted(df['pen'].unique().tolist())
#     selected_cats = st.multiselect(
#         "Filter by pen", 
#         options=categories, 
#         default=categories
#     )

#     # Filter the data
#     filtered_df = df[df['pen'].isin(selected_cats)].copy().reset_index(drop=True)

#     if len(filtered_df)>0:
#         if selected_sheet != "Team GC":
#             m1.metric("Pen", f"{filtered_df['pen'].iloc[0]}")
#             m2.metric("Total Participants", len(df))
#             m3.metric("Current Leader", f"{filtered_df['name'].iloc[0]}")

#     # Apply the styles
#     styled_df = filtered_df.style.apply(highlight_podium, axis=1)

#     st.dataframe(
#             styled_df,
#             use_container_width=True,
#             hide_index=False, # Removes the 0, 1, 2... column
#             column_config={
#                 "name": "Rider",
#                 "team_name": "Team",
#             }
#         )
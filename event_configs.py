import os
import streamlit as st

# --- 1. EVENT CONFIGURATIONS ---
EVENT_CONFIG = {
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
    "La Blanca": {
        "file": "LaBlanca/LaBlanca.xlsx",
        "default_sheet": "GC",
        "sorting": lambda sheet: 
            (['races', 'total_time'], [True, True]) if sheet == "GC" else
            (['racers', 'total_time'], [False, True]) if sheet == "Team GC" else
            (['pen', f"time{sheet[-1]}"], [True, True]) if "Round" in sheet else
            (['pen', 'e_gap'], [True, True]) if "e_gap" in sheet else
            (['pen', 'Total Points'], [True, False]),
        "GC_calc": "raw_GC"
    },
    "La Roja": {
        "file": "LaRoja/LaRoja.xlsx",
        "default_sheet": "GC",
        "sorting": lambda sheet: 
            (['races', 'total_time'], [True, True]) if sheet == "GC" else
            (['racers', 'total_time'], [False, True]) if sheet == "Team GC" else
            (['pen', f"time{sheet[-1]}"], [True, True]) if "Round" in sheet else
            (['pen', 'Total Points'], [True, False])
    },
    "TNP Summer Championships": {
        "file": "TNP_Summer_Championships/SummerChamps.xlsx",
        "default_sheet": "GC",
        "sorting": lambda sheet: 
            (['races', 'total_time'], [True, True]) if sheet == "GC" else
            (['racers', 'total_time'], [False, True]) if sheet == "Team GC" else
            (['pen', f"time{sheet[-1]}"], [True, True]) if "Round" in sheet else
            (['pen', 'Total Points'], [True, False])
    }
}

# --- 2. EVENT RULES & INFO RENDERER ---
def render_event_info(selected_event):
    """Renders images, rules, and announcements for the selected event."""
    if selected_event == "La Blanca":
        st.markdown("""
                    # La Blanca
                    ### Why not check out our upcoming La Roja tour using the link above.
                    """)
        
        # Display image if present
        hero_image = "icons/La_Blanca_hero.jpeg"
        if os.path.exists(hero_image):
            st.image(hero_image, width=600)

        st.markdown("""
**Results will be updated at least twice a day, at approximately 8 am and 10 pm Pacific Time**
                
## Rules
Total time across the 5 stages will determine the GC winner. For team GC the best three times for each team on each stage will be counted. We won't calculate egap initially, this may change based on demand and numbers.

### Sprint and KQOM standings
To be included in the Sprint/KQOM standings you must complete every stage!

There are three sprint segments (stages 1, 2 and 5). Each will be scored via FTS. Points will be awarded to the top 15 times (across all races) in each category from 20 points for 1st to 1 point for 15th:  
* 20, 18, 16, 14, 12, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1

There are 8 registered KQOM segments split across stages 1 and 4. These will also be scored via FTS, taking the best times across all races. The climbs are split into three categories and scored appropriately:
* **Category 3** – Breakaway Brae, Breakaway Brae Reverse, The Clyde Kicker
  * Points: 5, 3, 2, 1
* **Category 2** – Sgurr Summit North, Sgurr Summit South, London Fox Hill, London Leith Hill
  * Points: 10, 8, 6, 5, 4, 3, 2, 1
* **Category 1** – London Keith Hill
  * Points: 20, 15, 12, 10, 8, 7, 6, 5, 4, 3, 2, 1
                    
### GC Classifications
The main GC classification is based on the pen entered by each rider. As these are mass start events each rider will be classified in the highest pen they entered unless they ride 4 races in a lower pen. Please use the options below to see how the GC would look if you filter by pace category or age group!

        """)

    elif selected_event == "La Roja":
        st.markdown("## La Roja")
        
        # Display image if present
        hero_image = "icons/La_Roja_Tour_poster.png"
        if os.path.exists(hero_image):
            st.image(hero_image, width=600)

        st.markdown("""
**Results will be updated at least twice a day, at approximately 8 am and 10 pm Pacific Time**
                
## Rules
Total time across the 5 stages will determine the GC winner. For team GC the best three times for each team on each stage will be counted. We won't calculate egap initially, this may change based on demand and numbers.

### Sprint and KQOM standings
TBD
        """)

    elif selected_event == "TNP Summer Championships":
        st.markdown("## TNP Summer Championships")
        
        # Display image if present
        hero_image = "icons/SummerChamps.png"
        if os.path.exists(hero_image):
            st.image(hero_image, width=600)

        st.markdown("""            
## Rules
Total time across the 2 stages will determine the GC winner. There are two time slots for each race, if you race both your best time will be counted.

### Sprint and KQOM standings
Stage 1 is mostly about the sprints, stage 2 is where the KQOM will be decided!
                    
All segments are scored as FTS with only your best time counting! All segments are counted once, regardless of whether you go through that segment just once, or multiple times.
                    
Sprint segments: \n
Stage 1 - Lutece Sprint, Tchou Tchou Sprint, Monceau Sprint \n
Stage 2 - Watopia Sprint \n
Fastest 15 times through each segment are awared the following points: [20,18,16,14,12,10,9,8,7,6,5,4,3,2,1]

KQOM segments: \n
Stage 1 - Montmartre KOM \n
Stage 2 - Titans Grove Reverse KOM & Volcano KOM \n 

As in the La Blanca series, the climbs are split into different categorites:
* **Category 2** – Montmartre KOM and Titans Grove Reverse KOM
  * Points: [10,8,6,5,4,3,2,1]
* **Category 1** – Volcano KOM
  * Points: [20,15,12,10,8,7,6,5,4,3,2,1]            
        """)
        
       

    elif selected_event == "London-Watopia":
        # Add future text or images for London-Watopia here if needed
        pass

    elif selected_event == "The Next Peak":
        # Add future text or images for The Next Peak here if needed
        pass
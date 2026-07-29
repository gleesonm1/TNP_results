import pandas as pd
import numpy as np

pen_order = ['A', 'B', 'C', 'D', 'E']
pen_rank = {p: i for i, p in enumerate(pen_order)}

# define how to determine rank of rider if present in multiple rounds
def choose_pen(df):
    eligible = df[df['count'] >= len(round) - 1]
    if not eligible.empty:
        return (
            eligible
            .sort_values(
                by=['count', 'pen'],
                ascending=[False, True],
                key=lambda s: s.map(pen_rank) if s.name == 'pen' else s
            )
            .iloc[0]['pen']
        )

    return (
        df
        .sort_values(by='pen', key=lambda s: s.map(pen_rank))
        .iloc[0]['pen']
    )

def assign_points(df, segment, points_scale):
    points_col = segment + " points"

    df[points_col] = 0  # default

    for pen, g in df.groupby('pen'):
        valid = g[g[segment].notna()].copy()

        if valid.empty:
            continue

        valid = valid.sort_values(segment)
        valid['rank'] = range(1, len(valid) + 1)

        valid[points_col] = valid['rank'].apply(
            lambda r: points_scale[r - 1] if r <= len(points_scale) else 0
        )

        df.loc[valid.index, points_col] = valid[points_col]

    return df

# Function to convert seconds to hh:mm:ss
def format_seconds(total_seconds):
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    dec = int(np.round(1000*(total_seconds % 1)))
    if np.nanmax(hours) > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{dec:03d}"
    elif np.nanmax(minutes) > 0:
        return f"{minutes:02d}:{seconds:02d}.{dec:03d}"
    else:
        return f"{seconds:02d}.{dec:03d}"

def raw_gc_calc(out):
    gc_cols = ['pen', 'category', 'zwift_id', 'name', 'team_name', 'age']

    for i in out.keys():
        gc_cols.append(out[i].columns[out[i].columns.str.startswith('time')][0])

    all_rounds = [
            df[df.columns.intersection(gc_cols)] # Only take columns that exist in THIS df
            for key, df in out.items()
            if key != 'GC' and not df.empty
        ]

    all_gc_rows = pd.concat(all_rounds, ignore_index=True)
    time_cols = [c for c in all_gc_rows.columns if c.startswith('time')]
    assert all_gc_rows.groupby('zwift_id')[time_cols].count().max().max() <= 1

    pen_counts = (
        all_gc_rows
        .groupby(['zwift_id', 'pen'])
        .size()
        .reset_index(name='count')
    )

    gc_pen = (
        pen_counts
        .groupby('zwift_id')
        .apply(choose_pen, include_groups = False)
        .reset_index(name='pen')
    )

    gc_base = (
        all_gc_rows
        .groupby('zwift_id', as_index=False)
        .agg({
            'category': 'first',
            'name': 'first',
            'team_name': 'first',
            'age': 'first',
            **{c: 'min' for c in time_cols}   # keep round times
        })
    )

    gc = (
        gc_base
        .merge(gc_pen, on='zwift_id', how='left')
        .sort_values(by='pen', key=lambda s: s.map(pen_rank), ignore_index=True)
    )

    gc['races'] = gc[time_cols].count(axis=1)

    # calculate offsets
    gc['total_time'] = gc[time_cols].sum(axis=1)

    gc['time_offset'] = np.zeros(len(gc))
    gc.loc[gc['races'] == gc['races'].max(),'time_offset'] = gc['total_time'] - gc.loc[gc['races'] == gc['races'].max()].groupby('pen')['total_time'].transform('min')
    gc.loc[gc['races'] < gc['races'].max(), 'time_offset'] = np.nan

    gc.sort_values(by = ['pen', 'races', 'total_time'], ascending = [True, False, True], 
                ignore_index=True, inplace = True)

    out['GC'] = gc[['pen', 'category', 'age', 'name', 'team_name', 'total_time', 'time_offset', 'races']]

    #### TEAM GC ######
    teams = gc['team_name'].unique()

    team_gc = {}
    team_gc_cols = ['pen','team_name']

    for idx, key in enumerate(round):
        rows = []
        if key != "GC" and not out[key].empty:
            df = out[key]
            time_col = f"time{idx+1}"

            for (pen, team), g in df.groupby(['pen', 'team_name']):
                if len(g) >= 3:
                    if len(team)>0:
                        team_time = g[time_col].nsmallest(3).sum()
                        rows.append({
                            'round': key,
                            'pen': pen,
                            'team_name': team,
                            f'time{idx+1}': team_time,
                            f'racers{idx+1}': 3,
                        })
                else:
                    if len(team)>0:
                        team_time = g[time_col].sum()
                        rows.append({
                            'round': key,
                            'pen': pen,
                            'team_name': team,
                            f'time{idx+1}': team_time,
                            f'racers{idx+1}': len(g),
                        })

            team_gc_cols.append(f"time{idx+1}")
            team_gc_cols.append(f"racers{idx+1}")

        team_gc[key] = pd.DataFrame(rows)

    all_rounds = [
        df[df.columns.intersection(team_gc_cols)] # Only take columns that exist in THIS df
        for key, df in team_gc.items()
        if key != 'GC' and not df.empty
    ]

    if len(all_rounds) > 0:
        all_team_rows = pd.concat(all_rounds, ignore_index=True)
        time_cols = [c for c in all_team_rows.columns if c.startswith('time')]
        racer_cols = [c for c in all_team_rows.columns if c.startswith('racers')]
        # assert all_team_rows.groupby('team_name')[time_cols].count().max().max() <= 1

        pen_counts = (
            all_team_rows
            .groupby(['pen', 'team_name'])
            .size()
            .reset_index(name='count')
        )

        gc_team = (
            all_team_rows
            .groupby(['team_name', 'pen'], as_index=False)
            .agg({
                **{c: 'min' for c in time_cols},     # Keep round times (minimum time)
                **{c: 'first' for c in racer_cols}  # Copy across racer data
            })
        )

        gc_team['racers'] = gc_team[racer_cols].sum(axis=1)
        gc_team['total_time'] = gc_team[time_cols].sum(axis=1)

        gc_team['time_offset'] = np.zeros(len(gc_team))
        gc_team.loc[gc_team['racers'] == gc_team['racers'].max(),'time_offset'] = gc_team['total_time'] - gc_team.loc[gc_team['racers'] == gc_team['racers'].max()].groupby('pen')['total_time'].transform('min')
        gc_team.loc[gc_team['racers'] < gc_team['racers'].max(), 'time_offset'] = np.nan

        gc_team.sort_values(by=['pen', 'racers', 'total_time'], ascending=[True, False, True], 
                    ignore_index=True, inplace=True)

        # 1. Interleave time_cols and racer_cols (e.g., time1, racers1, time2, racers2)
        alternating_cols = [col for pair in zip(time_cols, racer_cols) for col in pair]
        
        # 2. Define your base columns
        base_cols = ['pen', 'team_name', 'total_time', 'time_offset', 'racers']
        
        # 3. Combine them to slice the DataFrame
        team_gc['GC'] = gc_team[base_cols + alternating_cols]
    else:
        team_gc['GC'] = pd.DataFrame()

    return out, team_gc['GC']
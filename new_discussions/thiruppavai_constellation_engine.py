import matplotlib.pyplot as plt
import numpy as np
import csv
import re
import os
from skyfield.api import load, wgs84, Star
from skyfield.data import hipparcos
from datetime import datetime, timedelta

# ==========================================
# 1. CORE DATASET & ENVIRONMENT INITIALIZATION
# ==========================================
EPHEMERIS_FILE = 'de431_part-2.bsp'
OUTPUT_DIR = "thiruppavai_sky_sequence"

print("Initializing Constellation Rendering Framework...")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

eph = load(EPHEMERIS_FILE)
ts = load.timescale()

with load.open('hip_main.dat') as f:
    df_stars = hipparcos.load_dataframe(f)

# Observation Coordinates: Srivilliputhur
LAT = 9.5161
LON = 77.6284

# ==========================================
# 2. STELLAR CONNECTIONS & BOUNDARY MAPS
# ==========================================
# Direct Hipparcos IDs for all anchor stars
STAR_REGISTRY = {
    # Simha Rasi (Leo) - Pasuram 23 Lion Shape
    'Regulus': 49669, 'Zosma': 54872, 'Denebola': 57632, 
    'Algieba': 50583, 'Adhafera': 50335, 'Rasalas': 48455,
    
    # Mrigashirsha/Ardra Axis (Orion Shield & Body)
    'Betelgeuse': 27989, 'Rigel': 24436, 'Bellatrix': 26311, 
    'Alnilam': 26727, 'Alnitak': 26777, 'Mintaka': 25930, 'Saiph': 27366,
    
    # Sapta Rishis (Ursa Major)
    'Dubhe': 54061, 'Merak': 53910, 'Phecda': 58001, 'Megrez': 59774,
    'Alioth': 62956, 'Mizar': 65378, 'Alkaid': 67301,
    
    # Fundamental Core Sidereal Anchor Point
    'Chitra (Spica)': 65474
}

# Geometric connection vectors mapping the star shapes
CONSTELLATION_LINES = {
    'Simha (Leo)': [
        ('Denebola', 'Zosma'), ('Zosma', 'Regulus'), ('Regulus', 'Algieba'),
        ('Algieba', 'Adhafera'), ('Adhafera', 'Rasalas'), ('Rasalas', 'Algieba')
    ],
    'Orion Axis': [
        ('Betelgeuse', 'Bellatrix'), ('Bellatrix', 'Mintaka'), ('Mintaka', 'Alnilam'),
        ('Alnilam', 'Alnitak'), ('Alnitak', 'Saiph'), ('Saiph', 'Rigel'),
        ('Rigel', 'Betelgeuse'), ('Mintaka', 'Rigel'), ('Alnitak', 'Betelgeuse')
    ],
    'Sapta Rishis (Ursa Major)': [
        ('Alkaid', 'Mizar'), ('Mizar', 'Alioth'), ('Alioth', 'Megrez'),
        ('Megrez', 'Phecda'), ('Phecda', 'Merak'), ('Merak', 'Dubhe'), ('Dubhe', 'Megrez')
    ]
}

def to_scalar(val):
    if hasattr(val, '__len__') or isinstance(val, (np.ndarray, list)):
        return float(val)
    return float(val)

# ==========================================
# 3. GRAPHICAL PLOTTING CORE
# ==========================================
def render_sky_map(t_utc, local_dt, day_num):
    observer = eph['earth'] + wgs84.latlon(LAT, LON)
    obs_time = observer.at(t_utc)
    
    # Track Planets
    bodies = {
        'Sun': eph['sun'], 'Moon': eph['moon'], 'Mercury': eph['mercury'],
        'Venus': eph['venus'], 'Mars': eph['mars barycenter'],
        'Jupiter': eph['jupiter barycenter'], 'Saturn': eph['saturn barycenter']
    }
    
    planet_coords = {}
    for name, b_obj in bodies.items():
        alt, az, _ = obs_time.observe(b_obj).apparent().altaz()
        alt_d, az_d = to_scalar(alt.degrees), to_scalar(az.degrees)
        if alt_d > 0:
            planet_coords[name] = {'alt': alt_d, 'az': az_d}

    # Calculate Star Positions
    star_coords = {}
    for name, hip_id in STAR_REGISTRY.items():
        star_obj = Star.from_dataframe(df_stars.loc[hip_id])
        alt, az, _ = obs_time.observe(star_obj).apparent().altaz()
        alt_d, az_d = to_scalar(alt.degrees), to_scalar(az.degrees)
        if alt_d > -10:  # Calculate slightly below horizon to render continuous line cuts
            star_coords[name] = {'alt': alt_d, 'az': az_d}

    # Canvas Settings
    plt.clf()
    fig, ax = plt.subplots(figsize=(11, 11), subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    
    def to_polar(alt_val, az_val):
        return np.radians(az_val), (90.0 - alt_val)

    # A. Draw Constellation Constellation Geometric Wireframes
    for c_name, lines in CONSTELLATION_LINES.items():
        for start_star, end_star in lines:
            if start_star in star_coords and end_star in star_coords:
                s_data = star_coords[start_star]
                e_data = star_coords[end_star]
                
                # Render line only if both nodes sit safely near or above horizon view boundaries
                if s_data['alt'] > 0 or e_data['alt'] > 0:
                    t1, r1 = to_polar(s_data['alt'], s_data['az'])
                    t2, r2 = to_polar(e_data['alt'], e_data['az'])
                    ax.plot([t1, t2], [r1, r2], color='#38bdf8', linestyle='-', linewidth=1.2, alpha=0.5, zorder=2)

    # B. Plot Star Points
    for name, s_data in star_coords.items():
        if s_data['alt'] > 0:
            theta, r = to_polar(s_data['alt'], s_data['az'])
            
            # CRITICAL CORE REFINEMENT: Highlight Spica (Chitra) uniquely as reference anchor
            if name == 'Chitra (Spica)':
                ax.scatter(theta, r, s=110, c='#ef4444', marker='o', edgecolors='white', linewidth=1.5, zorder=4, label='Sidereal Anchor Reference')
                ax.text(theta, r + 4, "CHITRA (SPICA)\n[Zodiac Axis Point]", color='#ef4444', fontsize=9, ha='center', fontweight='bold')
            else:
                ax.scatter(theta, r, s=40, c='#fef08a', marker='*', edgecolors='none', zorder=3)
                ax.text(theta, r + 3, name, color='#93c5fd', fontsize=8, ha='center')

    # C. Plot Planets
    for name, p_data in planet_coords.items():
        theta, r = to_polar(p_data['alt'], p_data['az'])
        color = '#f59e0b' if name == 'Sun' else '#cbd5e1' if name == 'Moon' else '#e11d48' if name == 'Venus' else '#f97316' if name == 'Jupiter' else '#ec4899'
        size = 200 if name in ['Sun', 'Moon'] else 100
        
        ax.scatter(theta, r, s=size, c=color, edgecolors='white', zorder=5)
        ax.text(theta, r - 4, name, color='white', fontsize=9, ha='center', fontweight='bold')

    # Compass and Ring Adjustments
    ax.set_ylim(0, 90)
    ax.set_yticklabels([])
    ax.set_xticks(np.radians([0, 45, 90, 135, 180, 225, 270, 315]))
    ax.set_xticklabels(['NORTH\n(Uttara)', 'NE', 'EAST\n(Purva)\n[Venus Rises]', 'SE', 'SOUTH\n(Dakshina)', 'SW', 'WEST\n(Prachya)\n[Jupiter Sets]', 'NW'], color='#94a3b8', fontsize=9)
    
    ax.patch.set_facecolor('#020617')
    ax.spines['polar'].set_color('#475569')
    ax.spines['polar'].set_linewidth(3)
    
    formatted_time = local_dt.strftime('%Y-%b-%d %H:%M') + " IST"
    plt.title(f"Thiruppavai Vow Sky Architecture ── DAY {day_num:02d}\nSrivilliputhur Ground Track | {formatted_time}", color='black', fontsize=12, pad=25)
    
    filename = os.path.join(OUTPUT_DIR, f"day_{day_num:02d}_thiruppavai.png")
    plt.tight_layout()
    plt.savefig(filename, dpi=150, facecolor='white')
    plt.close(fig)

# ==========================================
# 4. RUNTIME AUTOMATION CONTROL LOOP
# ==========================================
if __name__ == "__main__":
    #start_local_dt = datetime(862, 12, 26, 5, 15)  # 05:15 AM IST (Brahma Muhurtham)
    start_local_dt = datetime(862, 12, 14, 5, 15)

    print(f"Executing 30-Day Constellation Asset Generator Engine Pipeline...")
    print("-" * 70)
    
    for day_idx in range(1, 31):
        current_local_dt = start_local_dt + timedelta(days=(day_idx - 1))
        current_utc_dt = current_local_dt - timedelta(hours=5, minutes=30)
        t_skyfield = ts.utc(current_utc_dt.year, current_utc_dt.month, current_utc_dt.day, current_utc_dt.hour, current_utc_dt.minute)
        
        print(f"Rendering Day Frame {day_idx:02d}/30 ── Local Sky Step Date: {current_local_dt.strftime('%Y-%b-%d')}")
        render_sky_map(t_skyfield, current_local_dt, day_idx)
        
    print("-" * 70)
    print(f"All 30 advanced planetarium star-line files saved to: ./{OUTPUT_DIR}/")


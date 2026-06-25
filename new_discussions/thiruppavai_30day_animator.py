import matplotlib.pyplot as plt
import numpy as np
import re
import os
from skyfield.api import load, wgs84, Star
from skyfield.data import hipparcos
from datetime import datetime, timedelta

# ==========================================
# 1. INITIALIZATION & CORE DATASETS
# ==========================================
EPHEMERIS_FILE = 'de431_part-2.bsp'

print("Initializing 30-Day Automated Planetarium Grid...")
if not os.path.exists(EPHEMERIS_FILE):
    print(f"Error: Missing '{EPHEMERIS_FILE}' in execution root directory.")
    exit()

eph = load(EPHEMERIS_FILE)
ts = load.timescale()

with load.open('hip_main.dat') as f:
    df_stars = hipparcos.load_dataframe(f)

# Srivilliputhur Ground Track Configuration
LAT = 9.5161
LON = 77.6284

# Exact Hipparcos Anchor Catalog Mappings
VEDIC_CONSTELLATIONS = {
    'Magha (Regulus)': 49669,
    'Purva Phalguni': 54872,
    'Uttara Phalguni': 57632,
    'Mrigashira (Meissa)': 27072,
    'Ardra (Betelgeuse)': 27989,
    'Rigel': 24436,
    'SaptaRishi-Kratu': 54061,
    'SaptaRishi-Pulaha': 53910,
    'SaptaRishi-Marichi': 67301,
    'Rohini (Aldebaran)': 21421,
    'Chitra (Spica)': 65474,
    'Swati (Arcturus)': 69673
}

# Helper to flatten vector array dimensions safely
def to_scalar(val):
    if hasattr(val, '__len__') or isinstance(val, (np.ndarray, list)):
        return float(val)
    return float(val)

# ==========================================
# 2. CORE PLANETARIUM VIEW ENGINE
# ==========================================
def render_single_day(t_utc, local_dt, day_number, output_folder):
    observer_loc = wgs84.latlon(LAT, LON)
    observer = eph['earth'] + observer_loc
    obs_time = observer.at(t_utc)
    
    bodies = {
        'Sun': eph['sun'], 'Moon': eph['moon'], 'Mercury': eph['mercury'],
        'Venus': eph['venus'], 'Mars': eph['mars barycenter'],
        'Jupiter': eph['jupiter barycenter'], 'Saturn': eph['saturn barycenter']
    }
    
    planet_data = []
    for name, body_obj in bodies.items():
        alt, az, _ = obs_time.observe(body_obj).apparent().altaz()
        alt_deg = to_scalar(alt.degrees)
        az_deg = to_scalar(az.degrees)
        if alt_deg > 0:
            planet_data.append({'name': name, 'alt': alt_deg, 'az': az_deg})

    star_data = []
    for label, hip_id in VEDIC_CONSTELLATIONS.items():
        star_obj = Star.from_dataframe(df_stars.loc[hip_id])
        alt, az, _ = obs_time.observe(star_obj).apparent().altaz()
        alt_deg = to_scalar(alt.degrees)
        az_deg = to_scalar(az.degrees)
        if alt_deg > 0:
            star_data.append({'name': label, 'alt': alt_deg, 'az': az_deg})

    # Plot Layout Generation
    plt.clf()
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    
    def altaz_to_polar(alt_val, az_val):
        return np.radians(az_val), (90.0 - alt_val)

    # Plot Stars
    for s in star_data:
        theta, r = altaz_to_polar(s['alt'], s['az'])
        ax.scatter(theta, r, s=60, c='#fef08a', marker='*', edgecolors='none', zorder=4)
        short_label = s['name'].split()
        ax.text(theta, r + 3, short_label, color='#93c5fd', fontsize=8, ha='center', fontweight='semibold')

    # Plot Planets
    for p in planet_data:
        theta, r = altaz_to_polar(p['alt'], p['az'])
        color = '#f59e0b' if p['name'] == 'Sun' else '#cbd5e1' if p['name'] == 'Moon' else '#38bdf8' if p['name'] == 'Venus' else '#f97316' if p['name'] == 'Jupiter' else '#ec4899'
        size = 180 if p['name'] in ['Sun', 'Moon'] else 90
        
        ax.scatter(theta, r, s=size, c=color, edgecolors='white', zorder=5)
        ax.text(theta, r - 4, p['name'], color='white', fontsize=9, ha='center', fontweight='bold')

    # Grid Customization & Compass Markings
    ax.set_ylim(0, 90)
    ax.set_yticklabels([])
    ax.set_xticks(np.radians([0, 45, 90, 135, 180, 225, 270, 315]))
    ax.set_xticklabels(['NORTH\n(Uttara)', 'NE', 'EAST\n(Purva)\n[Rising]', 'SE', 'SOUTH\n(Dakshina)', 'SW', 'WEST\n(Prachya)\n[Setting]', 'NW'], color='#94a3b8', fontsize=9)
    
    ax.patch.set_facecolor('#020617')
    ax.spines['polar'].set_color('#334155')
    ax.spines['polar'].set_linewidth(3)
    
    formatted_time = local_dt.strftime('%Y-%b-%d %H:%M') + " IST"
    plt.title(f"Thiruppavai Vow Devotional Sky Canopy ── DAY {day_number:02d}\nSrivilliputhur Coordinates | {formatted_time}", color='black', fontsize=12, pad=20)
    
    filename = os.path.join(output_folder, f"day_{day_number:02d}_thiruppavai.png")
    plt.tight_layout()
    plt.savefig(filename, dpi=150, facecolor='white')
    plt.close(fig)

# ==========================================
# 3. CHRONOLOGICAL AUTOMATION CONTROLLER
# ==========================================
def run_30day_pipeline():
    output_dir = "thiruppavai_sky_sequence"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Chronological Starting Anchor: December 26, 862 AD (Julian)
    start_local_dt = datetime(862, 12, 26, 5, 15) # 05:15 AM IST (Brahma Muhurtham)
    
    print(f"\nLaunching simulation sequence script. Target output direct link path: ./{output_dir}/")
    print("-" * 65)
    
    for day_idx in range(1, 31):
        # Add days sequentially based on current loop index
        current_local_dt = start_local_dt + timedelta(days=(day_idx - 1))
        
        # Convert local Indian Standard Time calculation frame (UTC+5:30) to standard UTC
        current_utc_dt = current_local_dt - timedelta(hours=5, minutes=30)
        
        t_skyfield = ts.utc(current_utc_dt.year, current_utc_dt.month, current_utc_dt.day, current_utc_dt.hour, current_utc_dt.minute)
        
        print(f"Processing Sheet: Day {day_idx:02d} / 30 ── Local Target Date: {current_local_dt.strftime('%Y-%b-%d')}")
        render_single_day(t_skyfield, current_local_dt, day_idx, output_dir)
        
    print("-" * 65)
    print(f"Sequence Generation Complete. 30 sequential canopy frame states saved to: ./{output_dir}/")

if __name__ == "__main__":
    run_30day_pipeline()


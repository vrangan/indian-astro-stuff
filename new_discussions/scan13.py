import matplotlib.pyplot as plt
import numpy as np
from skyfield.api import load, wgs84
from skyfield.framelib import ecliptic_frame
from skyfield.almanac import find_discrete, sunrise_sunset
from datetime import timedelta
import re

# ==========================================
# 1. CONFIGURATION
# ==========================================
EPHEMERIS_FILE = 'de431_part-2.bsp' 
SRIVILLIPUTHUR = wgs84.latlon(9.5161, 77.6284)
START_YEAR = 1
END_YEAR = 1000

# ==========================================
# 2. SETUP & AYANAMSA
# ==========================================
def get_lahiri_ayanamsa(t):
    j2000 = 2451545.0
    days = t.tt - j2000
    return 23.85 + (days / 365.25) * (50.29 / 3600.0)

def get_sidereal_lon(observer, body, t):
    apparent = observer.at(t).observe(body).apparent()
    lat, lon, dist = apparent.frame_latlon(ecliptic_frame)
    return (lon.degrees - get_lahiri_ayanamsa(t)) % 360

# ==========================================
# 3. SCAN LOGIC
# ==========================================
def scan_for_thiruppavai_date(eph, ts):
    print(f"Scanning {START_YEAR}-{END_YEAR} AD using {EPHEMERIS_FILE}...")
    
    sun = eph['sun']
    jupiter = eph['jupiter barycenter'] 
    venus = eph['venus']
    earth = eph['earth']
    observer = earth + SRIVILLIPUTHUR
    
    candidates = []
    
    for year in range(START_YEAR, END_YEAR + 1):
        t_start = ts.utc(year, 12, 1)
        t_end = ts.utc(year + 1, 1, 30)
        
        t_phases, phases = find_discrete(t_start, t_end, load.moon_phases(eph))
        
        for t_moon, phase in zip(t_phases, phases):
            if phase == 2: # Full Moon
                sun_lon = get_sidereal_lon(observer, sun, t_moon)
                
                if 240 <= sun_lon < 270:
                    t_target = t_moon + timedelta(days=12)
                    t_rise_start = t_target - timedelta(hours=12)
                    t_rise_end = t_target + timedelta(hours=12)
                    t_sunrises, _ = find_discrete(t_rise_start, t_rise_end, sunrise_sunset(eph, SRIVILLIPUTHUR))
                    
                    if len(t_sunrises) == 0: continue
                    t_sunrise = t_sunrises
                    
                    t_check = t_sunrise - timedelta(minutes=30)
                    obs = observer.at(t_check)
                    alt_v, _, _ = obs.observe(venus).apparent().altaz()
                    alt_j, _, _ = obs.observe(jupiter).apparent().altaz()
                    
                    if alt_v.degrees > 0 and -5 < alt_j.degrees < 15:
                        candidates.append(t_sunrise)
                        print(f"Found Candidate: {t_sunrise.utc_jpl()} | V_Alt: {alt_v.degrees:.1f}, J_Alt: {alt_j.degrees:.1f}")

    return candidates

# ==========================================
# 4. PLOTTING FUNCTION (Saves PNG)
# ==========================================
def plot_brahma_muhurtham(t_sunrise, filename, eph):
    # Brahma Muhurtham starts 96 mins before sunrise
    t_brahma = t_sunrise - timedelta(minutes=96)
    
    earth = eph['earth']
    observer = earth + SRIVILLIPUTHUR
    
    bodies = {
        'Sun': eph['sun'],
        'Moon': eph['moon'],
        'Mercury': eph['mercury'],
        'Venus': eph['venus'],
        'Mars': eph['mars'],
        'Jupiter': eph['jupiter barycenter'],
        'Saturn': eph['saturn barycenter']
    }
    
    obs = observer.at(t_brahma)
    data = []
    
    for name, body in bodies.items():
        alt, az, _ = obs.observe(body).apparent().altaz()
        data.append({'name': name, 'alt': alt.degrees, 'az': az.degrees})

    # Clear plot state to prevent bleeding between multiple plots
    plt.clf()
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Visualizing Horizon limits (-90 to 0 is Ground, 0 to 90 is Sky)
    ax.axhspan(-25, 0, color='#1a252f', alpha=0.9, label='Below Horizon') 
    ax.axhspan(0, 90, color='#0f172a', alpha=0.9, label='Sky') 
    ax.axhline(0, color='#e2e8f0', linewidth=1.5, linestyle='--')
    
    for d in data:
        name = d['name']
        alt = d['alt']
        az = d['az']
        
        # Astrological Sign styling
        if name == 'Sun': color = '#f59e0b'
        elif name == 'Moon': color = '#94a3b8'
        elif name == 'Venus': color = '#38bdf8' # Dawn Morning Star
        elif name == 'Jupiter': color = '#f97316' # Setting Guru
        else: color = '#a78bfa'
        
        size = 220 if name in ['Sun', 'Moon'] else 110
        
        ax.scatter(az, alt, s=size, c=color, edgecolors='white', zorder=10)
        ax.text(az, alt + 3, name, ha='center', color='white', fontweight='bold', fontsize=10)
        ax.plot([az, az], [0, alt], color=color, linestyle=':', alpha=0.4)

    date_str = t_brahma.utc_jpl()
    plt.title(f"Brahma Muhurtham Sky (96 mins before Sunrise)\nDate: {date_str} | Srivilliputhur", color='black', fontsize=14, pad=15)
    plt.xlabel("Azimuth (Degrees)", fontsize=11)
    plt.ylabel("Altitude (Degrees)", fontsize=11)
    
    plt.xticks([0, 45, 90, 135, 180, 225, 270, 315, 360], 
               ['N (0°)', 'NE (45°)', 'E (90°)\n[Rising]', 'SE (135°)', 'S (180°)', 'SW (225°)', 'W (270°)\n[Setting]', 'NW (315°)', 'N (360°)'])
    
    plt.ylim(-25, 75) 
    plt.xlim(0, 360)
    plt.grid(True, linestyle=':', alpha=0.3, color='grey')
    
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close(fig)
    print(f"Saved sky visualization to: {filename}")

# ==========================================
# 5. EXECUTION BLOCK
# ==========================================
if __name__ == "__main__":
    try:
        eph = load(EPHEMERIS_FILE)
        ts = load.timescale()
        
        candidates = scan_for_thiruppavai_date(eph, ts)
        
        if candidates:
            print(f"\nProcessing {len(candidates)} candidate charts...")
            for idx, t_sunrise in enumerate(candidates):
                # Clean up the JPL time string into a safe file name structure
                # Example: "A.D. 0731-Dec-18 01:23:45 UT" -> "731-Dec-18"
                raw_date = t_sunrise.utc_jpl()
                clean_date = re.sub(r'[^a-zA-Z0-9\-]', '_', raw_date.replace("A.D. ", "").split()[0])
                
                output_filename = f"srivilliuputh_sky_on_{clean_date}.png"
                
                # Pass the filename directly into the plotting engine
                plot_brahma_muhurtham(t_sunrise, output_filename, eph)
        else:
            print("No candidates fell within the target astronomical constraints.")
            
    except FileNotFoundError:
        print(f"Error: Required file '{EPHEMERIS_FILE}' not found in the directory.")


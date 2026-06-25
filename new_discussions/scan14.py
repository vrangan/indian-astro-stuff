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

# Vedic Rasi Mapping (30 degrees each)
RASI_NAMES = [
    "Mesha (Aries)", "Vrishabha (Taurus)", "Mithuna (Gemini)", "Karka (Cancer)",
    "Simha (Leo)", "Kanya (Virgo)", "Tula (Libra)", "Vrischika (Scorpio)",
    "Dhanu (Sagittarius)", "Makara (Capricorn)", "Kumbha (Aquarius)", "Meena (Pisces)"
]

# ==========================================
# 2. SETUP, AYANAMSA & RASI CALCULATION
# ==========================================
def get_lahiri_ayanamsa(t):
    j2000 = 2451545.0
    days = t.tt - j2000
    return 23.85 + (days / 365.25) * (50.29 / 3600.0)

def get_sidereal_lon(observer, body, t):
    apparent = observer.at(t).observe(body).apparent()
    lat, lon, dist = apparent.frame_latlon(ecliptic_frame)
    return (lon.degrees - get_lahiri_ayanamsa(t)) % 360

def get_rasi_name(lon_degrees):
    rasi_index = int(lon_degrees // 30)
    return RASI_NAMES[rasi_index]

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
# 4. PLOTTING FUNCTION WITH VEDIC RASIS
# ==========================================
def plot_brahma_muhurtham(t_sunrise, filename, eph):
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
    
    # Calculate Alt, Az, Sidereal Longitude, and Rasi for each body
    for name, body in bodies.items():
        alt, az, _ = obs.observe(body).apparent().altaz()
        sid_lon = get_sidereal_lon(observer, body, t_brahma)
        rasi = get_rasi_name(sid_lon)
        data.append({'name': name, 'alt': alt.degrees, 'az': az.degrees, 'rasi': rasi, 'lon': sid_lon})

    plt.clf()
    fig, ax = plt.subplots(figsize=(15, 8))
    
    # Horizon Grid
    ax.axhspan(-25, 0, color='#1a252f', alpha=0.9, label='Below Horizon') 
    ax.axhspan(0, 90, color='#0f172a', alpha=0.9, label='Sky') 
    ax.axhline(0, color='#e2e8f0', linewidth=1.5, linestyle='--')
    
    # Text panel content to display a clear Vedic Chart Summary
    rasi_summary_text = "Vedic Rasi Summary:\n"
    
    for d in data:
        name = d['name']
        alt = d['alt']
        az = d['az']
        rasi = d['rasi']
        
        rasi_summary_text += f"• {name}: {rasi} ({d['lon']:.1f}°)\n"
        
        # Color coding
        if name == 'Sun': color = '#f59e0b'
        elif name == 'Moon': color = '#94a3b8'
        elif name == 'Venus': color = '#38bdf8' 
        elif name == 'Jupiter': color = '#f97316' 
        else: color = '#a78bfa'
        
        size = 220 if name in ['Sun', 'Moon'] else 110
        
        # Plot body
        ax.scatter(az, alt, s=size, c=color, edgecolors='white', zorder=10)
        
        # Text labeling directly onto the object map
        label_text = f"{name}\n({rasi.split()[0]})"
        ax.text(az, alt + 3, label_text, ha='center', color='white', fontweight='bold', fontsize=9)
        ax.plot([az, az], [0, alt], color=color, linestyle=':', alpha=0.4)

    # Title & Labels
    date_str = t_brahma.utc_jpl()
    plt.title(f"Brahma Muhurtham Sky & Vedic Rasis (96 mins before Sunrise)\nDate: {date_str} | Srivilliputhur", color='black', fontsize=14, pad=15)
    plt.xlabel("Azimuth (Degrees)", fontsize=11)
    plt.ylabel("Altitude (Degrees)", fontsize=11)
    
    plt.xticks(, 
               ['N (0°)', 'NE (45°)', 'E (90°)\n[Rising]', 'SE (135°)', 'S (180°)', 'SW (225°)', 'W (270°)\n[Setting]', 'NW (315°)', 'N (360°)'])
    
    plt.ylim(-25, 75) 
    plt.xlim(0, 360)
    plt.grid(True, linestyle=':', alpha=0.3, color='grey')
    
    # Place a clean structural legend of the Planetary positions on the right side
    plt.gcf().text(0.84, 0.4, rasi_summary_text, fontsize=10, color='black', 
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='#f8fafc', edgecolor='#cbd5e1'))
    
    plt.tight_layout()
    # Adjust tight layout window slightly to make space for the right text card
    plt.subplots_adjust(right=0.82)
    
    plt.savefig(filename, dpi=150)
    plt.close(fig)
    print(f"Saved sky & Rasi visualization to: {filename}")

# ==========================================
# 5. EXECUTION BLOCK
# ==========================================
if __name__ == "__main__":
    try:
        eph = load(EPHEMERIS_FILE)
        ts = load.timescale()
        
        candidates = scan_for_thiruppavai_date(eph, ts)
        
        if candidates:
            print(f"\nProcessing {len(candidates)} candidate charts with Rasis...")
            for idx, t_sunrise in enumerate(candidates):
                raw_date = t_sunrise.utc_jpl()
                clean_date = re.sub(r'[^a-zA-Z0-9\-]', '_', raw_date.replace("A.D. ", "").split())
                
                output_filename = f"srivilliuputh_sky_on_{clean_date}.png"
                plot_brahma_muhurtham(t_sunrise, output_filename, eph)
        else:
            print("No candidates fell within the target astronomical constraints.")
            
    except FileNotFoundError:
        print(f"Error: Required file '{EPHEMERIS_FILE}' not found.")


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

# 27 Vedic Nakshatras (13°20' or 13.3333° each)
NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", 
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", 
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", 
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", 
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# ==========================================
# 2. AYANAMSA, RASI & NAKSHATRA CALCULATION
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
    return RASI_NAMES[int(lon_degrees // 30)]

def get_nakshatra_name(lon_degrees):
    # 360 degrees / 27 = 13.333333 degrees per nakshatra
    nakshatra_index = int(lon_degrees // (360.0 / 27.0))
    return NAKSHATRA_NAMES[nakshatra_index]

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
# 4. PLOTTING ENGINE (With Nakshatras)
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
    
    for name, body in bodies.items():
        alt, az, _ = obs.observe(body).apparent().altaz()
        sid_lon = get_sidereal_lon(observer, body, t_brahma)
        rasi = get_rasi_name(sid_lon)
        nakshatra = get_nakshatra_name(sid_lon) if name == 'Moon' else None
        data.append({'name': name, 'alt': alt.degrees, 'az': az.degrees, 'rasi': rasi, 'nakshatra': nakshatra, 'lon': sid_lon})

    plt.clf()
    fig, ax = plt.subplots(figsize=(16, 8))
    
    # Horizon Elements
    ax.axhspan(-25, 0, color='#1a252f', alpha=0.9, label='Below Horizon') 
    ax.axhspan(0, 90, color='#0f172a', alpha=0.9, label='Sky') 
    ax.axhline(0, color='#e2e8f0', linewidth=1.5, linestyle='--')
    
    # Dynamic Vedic Panel Text Generation
    rasi_summary_text = "Vedic Ephemeris Card\n" + "─" * 22 + "\n"
    
    for d in data:
        name = d['name']
        alt = d['alt']
        az = d['az']
        rasi = d['rasi']
        nakshatra = d['nakshatra']
        
        # Build text description metrics
        if name == 'Moon':
            rasi_summary_text += f"• Moon: {rasi}\n   ↳ Star: {nakshatra}\n   ↳ Long: {d['lon']:.1f}°\n"
            label_text = f"{name}\n({rasi.split()})\n[{nakshatra}]"
        else:
            rasi_summary_text += f"• {name}: {rasi} ({d['lon']:.1f}°)\n"
            label_text = f"{name}\n({rasi.split()})"
        
        # Color palettes
        if name == 'Sun': color = '#f59e0b'
        elif name == 'Moon': color = '#e2e8f0' # Glowing Silver
        elif name == 'Venus': color = '#38bdf8' 
        elif name == 'Jupiter': color = '#f97316' 
        else: color = '#a78bfa'
        
        size = 240 if name in ['Sun', 'Moon'] else 110
        
        # Render scatter points onto horizon geometry map
        ax.scatter(az, alt, s=size, c=color, edgecolors='white', zorder=10)
        ax.text(az, alt + 3, label_text, ha='center', color='white', fontweight='bold', fontsize=8.5)
        ax.plot([az, az], [0, alt], color=color, linestyle=':', alpha=0.4)

    # Title Context
    date_str = t_brahma.utc_jpl()
    plt.title(f"Brahma Muhurtham Horizon Map with Lunar Nakshatras\nDate: {date_str} | Location: Srivilliputhur", color='black', fontsize=14, pad=15)
    plt.xlabel("Azimuth Horizon Angle (Degrees)", fontsize=11)
    plt.ylabel("Elevation Altitude (Degrees)", fontsize=11)
    
    plt.xticks(, 
               ['N (0°)', 'NE (45°)', 'E (90°)\n[Rising]', 'SE (135°)', 'S (180°)', 'SW (225°)', 'W (270°)\n[Setting]', 'NW (315°)', 'N (360°)'])
    
    plt.ylim(-25, 75) 
    plt.xlim(0, 360)
    plt.grid(True, linestyle=':', alpha=0.3, color='grey')
    
    # Overlay info metadata card panel to the right margin
    plt.gcf().text(0.83, 0.35, rasi_summary_text, fontsize=9.5, color='black', fontfamily='monospace',
                   bbox=dict(boxstyle='round,pad=0.6', facecolor='#f8fafc', edgecolor='#cbd5e1'))
    
    plt.tight_layout()
    plt.subplots_adjust(right=0.81)
    
    plt.savefig(filename, dpi=150)
    plt.close(fig)
    print(f"Saved sky chart with Nakshatras to: {filename}")

# ==========================================
# 5. RUNTIME CONTROLLER ENTRYPOINT
# ==========================================
if __name__ == "__main__":
    try:
        eph = load(EPHEMERIS_FILE)
        ts = load.timescale()
        
        candidates = scan_for_thiruppavai_date(eph, ts)
        
        if candidates:
            print(f"\nProcessing {len(candidates)} charts featuring Lunar Houses...")
            for idx, t_sunrise in enumerate(candidates):
                raw_date = t_sunrise.utc_jpl()
                clean_date = re.sub(r'[^a-zA-Z0-9\-]', '_', raw_date.replace("A.D. ", "").split())
                
                output_filename = f"srivilliuputh_sky_on_{clean_date}.png"
                plot_brahma_muhurtham(t_sunrise, output_filename, eph)
        else:
            print("No matching celestial models discovered inside this epoch.")
            
    except FileNotFoundError:
        print(f"Error: Target BSP segment '{EPHEMERIS_FILE}' could not be located.")


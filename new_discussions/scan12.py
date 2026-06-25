import matplotlib.pyplot as plt
import numpy as np
from skyfield import almanac
from skyfield.api import load, wgs84, Star
from skyfield.framelib import ecliptic_frame
from skyfield.almanac import find_discrete, risings_and_settings, sunrise_sunset
from datetime import timedelta

# ==========================================
# 1. CONFIGURATION
# ==========================================
# File name (Update this to match your specific split file name)
EPHEMERIS_FILE = 'de431_part-2.bsp' 

# Location: Srivilliputhur
SRIVILLIPUTHUR = wgs84.latlon(9.5161, 77.6284)

# Scan Range (AD 1 to 1000)
START_YEAR = 1
END_YEAR = 1000

# ==========================================
# 2. SETUP & AYANAMSA
# ==========================================
def get_lahiri_ayanamsa(t):
    # Standard Lahiri approx: 23.85 deg at J2000, rate 50.29 arcsec/yr
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
    # user requested jupiter barycenter specifically
    jupiter = eph['jupiter barycenter'] 
    venus = eph['venus']
    earth = eph['earth']
    observer = earth + SRIVILLIPUTHUR
    
    candidates = []
    
    for year in range(START_YEAR, END_YEAR + 1):
        # Broad window for Margazhi (mid-Dec to mid-Jan)
        t_start = ts.utc(year, 12, 1)
        t_end = ts.utc(year + 1, 1, 30)
        
        # 1. Find Full Moons
        #t_phases, phases = find_discrete(t_start, t_end, load.moon_phases(eph))
        t_phases, phases = find_discrete(t_start, t_end, almanac.moon_phases(eph))
        
        for t_moon, phase in zip(t_phases, phases):
            if phase == 2: # Full Moon
                # Check if Sun is in Sidereal Sagittarius (240-270)
                sun_lon = get_sidereal_lon(observer, sun, t_moon)
                
                if 240 <= sun_lon < 270:
                    # 2. Target Day: 13th day (approx +12 days from Full Moon)
                    t_target = t_moon + timedelta(days=12)
                    
                    # Find Sunrise on this 13th day
                    t_rise_start = t_target - timedelta(hours=12)
                    t_rise_end = t_target + timedelta(hours=12)
                    t_sunrises, _ = find_discrete(t_rise_start, t_rise_end, sunrise_sunset(eph, SRIVILLIPUTHUR))
                    
                    if len(t_sunrises) == 0: continue
                    t_sunrise = t_sunrises[0]
                    
                    # 3. Check Event Conditions at Dawn
                    # Venus Rising (East), Jupiter Setting (West)
                    # We check slightly before sunrise (Civil Twilight)
                    t_check = t_sunrise - timedelta(minutes=30)
                    
                    obs = observer.at(t_check)
                    alt_v, _, _ = obs.observe(venus).apparent().altaz()
                    alt_j, _, _ = obs.observe(jupiter).apparent().altaz()
                    
                    # Simple filter: Venus up (>0), Jupiter low (<15)
                    if alt_v.degrees > 0 and -5 < alt_j.degrees < 15:
                        candidates.append(t_sunrise)
                        print(f"Found Candidate: {t_sunrise.utc_jpl()} | V_Alt: {alt_v.degrees:.1f}, J_Alt: {alt_j.degrees:.1f}")

    return candidates

# ==========================================
# 4. VISUALIZATION (Matplotlib)
# ==========================================
def plot_brahma_muhurtham(t_sunrise, eph, ts):
    # Brahma Muhurtham starts 2 muhurthams (96 mins) before sunrise
    t_brahma = t_sunrise - timedelta(minutes=96)
    
    earth = eph['earth']
    observer = earth + SRIVILLIPUTHUR
    
    # Bodies to plot
    bodies = {
        'Sun': eph['sun'],
        'Moon': eph['moon'],
        'Mercury': eph['mercury'],
        'Venus': eph['venus'],
        'Mars': eph['mars barycenter'],
        'Jupiter': eph['jupiter barycenter'],
        'Saturn': eph['saturn barycenter']
    }
    
    # Calculate Alt/Az for all
    obs = observer.at(t_brahma)
    data = []
    
    for name, body in bodies.items():
        alt, az, _ = obs.observe(body).apparent().altaz()
        data.append({'name': name, 'alt': alt.degrees, 'az': az.degrees})

    # PLOTTING
    fig, ax = plt.subplots(figsize=(12, 6), subplot_kw={'projection': 'polar'})
    
    # Settings for Polar Plot (North up, East right usually, but standard polar is CCW)
    # Azimuth: 0=North, 90=East, 180=South, 270=West
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1) # Clockwise (N -> E -> S -> W)
    
    # We want to show "below horizon" too. 
    # Let's map Altitude -90 to +90 to Radius 0 to 1? 
    # Standard sky charts usually just show 0 to 90.
    # To show "behind horizon", we can extend radius but color differently.
    
    # Let's use a standard Cartesian Horizon Chart instead for clarity on "Rising/Setting"
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Background: Ground (Alt < 0) vs Sky (Alt > 0)
    ax.axhspan(-90, 0, color='#2c3e50', alpha=0.9, label='Below Horizon') # Ground
    ax.axhspan(0, 90, color='#87CEEB', alpha=0.3, label='Sky') # Sky
    ax.axhline(0, color='black', linewidth=2)
    
    # Plot Planets
    for d in data:
        name = d['name']
        alt = d['alt']
        az = d['az']
        
        # Color logic
        color = 'gold' if name == 'Sun' else 'silver'
        if name == 'Venus': color = '#e6ccb2' # bright white/beige
        if name == 'Jupiter': color = '#d4a373' # orange/brownish
        if name == 'Mars': color = '#e63946'
        
        # Marker size
        size = 200 if name in ['Sun', 'Moon'] else 100
        
        ax.scatter(az, alt, s=size, c=color, edgecolors='black', zorder=10)
        ax.text(az, alt + 3, name, ha='center', fontweight='bold', fontsize=9)
        
        # Draw "stick" to horizon to visualize height easily
        ax.plot([az, az], [0, alt], color=color, linestyle=':', alpha=0.6)

    # Annotations & Formatting
    date_str = t_brahma.utc_jpl()
    plt.title(f"Brahma Muhurtham Sky (96 mins before Sunrise)\nDate: {date_str} | Loc: Srivilliputhur", fontsize=14)
    plt.xlabel("Azimuth (Degrees: 90=East, 270=West)")
    plt.ylabel("Altitude (Degrees)")
    plt.xticks([0, 45, 90, 135, 180, 225, 270, 315, 360], 
               ['N', 'NE', 'E (Rising)', 'SE', 'S', 'SW', 'W (Setting)', 'NW', 'N'])
    plt.ylim(-20, 90) # Show 20 degrees below horizon
    plt.xlim(0, 360)
    plt.grid(True, linestyle='--', alpha=0.5)
    output_filename = "earth-visualization.png"
    plt.tight_layout()
    plt.savefig(output_filename, dpi=150)
    plt.close()

# ==========================================
# 5. EXECUTION BLOCK
# ==========================================
if __name__ == "__main__":
    try:
        print(f"Loading {EPHEMERIS_FILE}...")
        eph = load(EPHEMERIS_FILE)
        ts = load.timescale()
        
        # 1. RUN SCAN
        candidates = scan_for_thiruppavai_date(eph, ts)
        
        # 2. IF CANDIDATE FOUND, PLOT FIRST ONE
        if candidates:
            best_candidate = candidates[0] # Pick the first/best match
            print(f"\nVisualizing Brahma Muhurtham for: {best_candidate.utc_jpl()}")
            plot_brahma_muhurtham(best_candidate, eph, ts)
        else:
            print("No perfect candidates found in this range with these parameters.")
            
    except FileNotFoundError:
        print(f"Error: Could not find '{EPHEMERIS_FILE}'. Please check the file name.")


from skyfield.api import load, Topos, Star, wgs84
from skyfield.searchlib import find_discrete
from skyfield import almanac
from skyfield.framelib import ecliptic_frame
import numpy as np
from datetime import timedelta

# ==========================================
# 1. SETUP & CONFIGURATION
# ==========================================
# LOCATION: Srivilliputhur, birth place of Andal
SRIVILLIPUTHUR = wgs84.latlon(9.5161, 77.6284)

# TIME RANGE: -3101 (3102 BC) to 1000 AD
START_YEAR = 1
END_YEAR = 1000

# AYANAMSA: Lahiri (approximate function for historical sweep)
# Ayanamsa ~ 24 deg in 2000 AD, Rate ~ 50.29 arcsec/year
def get_lahiri_ayanamsa(t):
    # J2000 epoch
    j2000 = 2451545.0
    days_since_j2000 = t.tt - j2000
    # Lahiri value at J2000: ~23.85 degrees
    # Precession rate: ~0.013969 degrees/year
    return 23.85 + (days_since_j2000 / 365.25) * (50.29 / 3600.0)

# ==========================================
# 2. INITIALIZE SKYFIELD
# ==========================================
# NOTE: User must download 'de431.bsp' (2.5GB) from JPL and place in folder
# Download link: https://nasa.gov
print("Loading Ephemeris de431.bsp (this may take a moment)...")
try:
    eph = load('de431_part-2.bsp') 
except:
    print("Error: de431.bsp not found. Please download it from JPL.")
    print("Using de421.bsp as a fallback for demonstration (limited range).")
    eph = load('de421.bsp')

sun = eph['sun']
earth = eph['earth']
moon = eph['moon']
venus = eph['venus']
jupiter = eph['jupiter barycenter']
observer = earth + SRIVILLIPUTHUR

ts = load.timescale()

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================

def get_sidereal_sun_long(t):
    """Returns Sun's longitude in Sidereal Zodiac (Lahiri)"""
    apparent = observer.at(t).observe(sun).apparent()
    lat, lon, dist = apparent.frame_latlon(ecliptic_frame)
    
    # Apply Ayanamsa
    ayanamsa = get_lahiri_ayanamsa(t)
    sidereal_lon = (lon.degrees - ayanamsa) % 360
    return sidereal_lon

def is_margazhi(t):
    """Check if Sun is in Sidereal Sagittarius (240-270 deg)"""
    lon = get_sidereal_sun_long(t)
    return 240 <= lon < 270

def check_event_conditions(t_dawn):
    """
    Check Pasuram 13 conditions at dawn:
    1. Venus Rising (Altitude > 0 but low, or just risen)
    2. Jupiter Setting (Altitude < 5 deg and descending)
    """
    obs_dawn = observer.at(t_dawn)
    
    # Calculate Alt/Az
    alt_v, az_v, _ = obs_dawn.observe(venus).apparent().altaz()
    alt_j, az_j, _ = obs_dawn.observe(jupiter).apparent().altaz()
    
    # CONDITION: 
    # Venus should be in East (Az roughly 45-135) and Rising (Alt > -5 and < 30)
    # Jupiter should be in West (Az roughly 225-315) and Setting (Alt < 5 and > -10)
    # They should be on opposite sides (Opposition-like configuration)
    
    is_venus_rising = (alt_v.degrees > 0) and (alt_v.degrees < 25) # Visible in east
    is_jupiter_setting = (alt_j.degrees < 10) and (alt_j.degrees > -5) # Low in west
    
    return is_venus_rising and is_jupiter_setting

# ==========================================
# 4. MAIN SCAN LOOP
# ==========================================
print(f"Scanning years {START_YEAR} to {END_YEAR} for Thiruppavai date...")
print(f"{'Date (Julian/Greg)':<20} | {'Event':<20} | {'Details'}")
print("-" * 70)

candidates = []

# Step through years
for year in range(START_YEAR, END_YEAR + 1):
    
    # 1. Find Margazhi (Sun entering Sagittarius Sidereal)
    # Approx check: Margazhi usually starts mid-Dec (Gregorian)
    # We construct a coarse search window for the year
    t_start = ts.utc(year, 11, 15)
    t_end = ts.utc(year + 1, 1, 20)
    
    # Find exact Margazhi start (Sun passes 240 deg Sidereal)
    # This optimization skips fine-grain search if not needed, 
    # but for simplicity we'll check the Full Moons in this window.
    
    # Find Full Moons in this window
    t_phases, phases = almanac.find_discrete(t_start, t_end, almanac.moon_phases(eph))
    
    for t_phase, phase in zip(t_phases, phases):
        if phase == 2: # Full Moon (2 = Full Moon in Skyfield almanac)
            
            # Check if this Full Moon is inside Margazhi
            if is_margazhi(t_phase):
                
                # FOUND: Margazhi Full Moon (Pasuram 1)
                # Day 1 = Full Moon Day
                
                # TARGET: Day 13 (Pasuram 13)
                # "13th day from it" -> t_phase + 13 days (approx)
                # We check the dawn of the 13th day.
                
                t_13 = t_phase + timedelta(days=12) # 13th day (inclusive counting: 1,2..13 is +12 days)
                
                # Find Dawn on Day 13 (Sun ~ -6 degrees altitude)
                # We simply set time to roughly 6:00 AM local time for a quick check,
                # or use almanac.risings_and_settings for Sun.
                # Srivilliputhur is UTC+5:30 (approx, though local mean time varies).
                # We'll use almanac to find sunrise.
                
                t_sunrise_search_start = t_13 - timedelta(hours=12)
                t_sunrise_search_end = t_13 + timedelta(hours=12)
                t_sunrises, _ = almanac.find_discrete(
                    t_sunrise_search_start, t_sunrise_search_end, 
                    almanac.sunrise_sunset(eph, SRIVILLIPUTHUR)
                )
                
                if len(t_sunrises) > 0:
                    t_dawn = t_sunrises[0] # Sunrise time
                    
                    # Check Venus/Jupiter condition at this dawn
                    if check_event_conditions(t_dawn):
                        
                        # Calculate Rain Date (Day 4)
                        t_rain = t_phase + timedelta(days=3)
                        
                        date_str = t_dawn.utc_jpl() # Returns string with 'J' for Julian if needed
                        print(f"{date_str} | Candidate Found    | Venus Rising / Jupiter Setting")
                        
                        # Detailed output
                        alt_v, _, _ = observer.at(t_dawn).observe(venus).apparent().altaz()
                        alt_j, _, _ = observer.at(t_dawn).observe(jupiter).apparent().altaz()
                        print(f"   > Venus Alt: {alt_v.degrees:.1f}°, Jupiter Alt: {alt_j.degrees:.1f}°")
                        print(f"   > Margazhi Full Moon: {t_phase.utc_iso()}")
                        print(f"   > Day 4 (Rain): {t_rain.utc_iso()}")
                        candidates.append(date_str)

print("-" * 70)
print(f"Scan Complete. Found {len(candidates)} candidates.")


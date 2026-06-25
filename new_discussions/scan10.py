from skyfield.api import load, Topos, Star, wgs84
from skyfield.data import hipparcos
from skyfield.almanac import find_discrete, risings_and_settings
import numpy as np
from pytz import timezone
import datetime

# --- CONFIGURATION ---
EPHEMERIS_FILE = 'de431_part-2.bsp'  # MUST be downloaded manually (2.5GB)
#START_YEAR = -3101
START_YEAR = 1
END_YEAR = 1000
LOCATION_LAT = 9.5076  # Srivilliputhur Latitude
LOCATION_LON = 77.6293 # Srivilliputhur Longitude
AYANAMSA_DEG = 24.0    # Approximate Lahiri/Krishnamurti value for modern adjustment
                       # Note: Ayanamsa changes with time. For precise Vedic calc 
                       # across millennia, we use Skyfield's precessed positions 
                       # and subtract the fiducial point (Spica/Zeta Piscium).

def main():
    print(f"Loading {EPHEMERIS_FILE}... (this may take a moment)")
    try:
        ts = load.timescale()
        eph = load(EPHEMERIS_FILE)
    except Exception as e:
        print(f"Error loading ephemeris: {e}")
        print("Please ensure 'de431.bsp' is in the local directory.")
        return

    # Define celestial bodies
    sun = eph['sun']
    earth = eph['earth']
    moon = eph['moon']
    venus = eph['venus']
    jupiter = eph['jupiter barycenter']
    
    # Define Location (Srivilliputhur)
    srivilliputhur = wgs84.latlon(LOCATION_LAT, LOCATION_LON)
    
    # Timezone for local dawn calculation
    ist = timezone('Asia/Kolkata')

    print(f"Scanning years {START_YEAR} to {END_YEAR}...")
    print(f"{'Year':<6} | {'Margazhi Start':<12} | {'Full Moon':<12} | {'Day 13 Date':<12} | {'Venus Alt':<10} | {'Jup Alt':<10} | {'Match?'}")
    print("-" * 90)

    # We iterate year by year
    for year in range(START_YEAR, END_YEAR + 1):
        # 1. FIND MARGAZHI (Sun enters Sidereal Sagittarius)
        # Approximate: Sun moves ~1 deg/day. Sidereal Sgr is 240 deg.
        # We scan Dec 1 to Jan 15 to find the exact ingress.
        
        t0 = ts.utc(year, 12, 1)
        t1 = ts.utc(year + 1, 1, 15)
        
        # Determine Ayanamsa for this specific year (Precession adjustment)
        # Simplified logic: Tropical Longitude - Ayanamsa = Sidereal Longitude
        # Target: Sidereal 240.0 (Start of Dhanur/Margazhi)
        # We search for when Sun's Apparent Ecliptic Longitude == 240 + Ayanamsa(t)
        # Note: Handling dynamic Ayanamsa accurately for -3000 requires 
        # referencing Spica (Chitra) as 180.0 deg.
        
        # Let's find the tropical longitude of Spica to anchor our zodiac
        # Spica is the anchor for Lahiri Ayanamsa (opposite 0 deg Libra).
        # We find when Sun is 60 degrees past Spica (which is 0 deg Libra start -> 240 deg is Sgr start??)
        # Wait: Spica is 180.0 Sidereal. Sgr Start is 240.0 Sidereal.
        # So we look for Sun being 60 degrees AHEAD of Spica.
        
        def sun_minus_spica_minus_60(t):
            observer = earth.at(t)
            _, sun_lon, _ = observer.observe(sun).apparent().ecliptic_latlon()
            # We would need a Star object for Spica, but for speed in a loop,
            # we can approximate Margazhi starts near Dec 15-20 (Julian/Gregorian drift applies).
            # Let's use a simpler Tropical approximation:
            # Tropical Sgr starts ~Nov 22. Sidereal Sgr starts ~Dec 16 (Modern) or earlier in ancient times.
            # Due to precession, in -3000, Margazhi would be in a different month?
            # User requirement: "Sun in Sagittarius". 
            # We will search specifically for Sun Longitude relative to Spica.
            return sun_lon.degrees % 360 # Placeholder
        
        # Optimized Search: Just check dates around Dec/Jan for the alignment
        # Logic: We need Venus Rising (Morning Star) and Jupiter Setting (Opposition).
        # This occurs when Earth is directly between Sun and Jupiter (Jupiter Opposition),
        # AND Venus is West of the Sun.
        
        # Jupiter Opposition happens once every ~399 days.
        # Venus is Morning Star (West of Sun) for ~263 days every 584 days.
        # We intersect these two cycles within the month of Margazhi.
        
        # Step A: Check Jupiter Opposition (Sun-Jupiter ~ 180 deg) in Dec/Jan
        # Step B: Check if Venus is Morning Star (Sun-Venus > 0)
        
        # To save compute time, we check mid-Margazhi (approx Dec 25)
        t_check = ts.utc(year, 12, 25)
        obs = earth.at(t_check)
        s_lon = obs.observe(sun).apparent().ecliptic_latlon()[1].degrees
        j_lon = obs.observe(jupiter).apparent().ecliptic_latlon()[1].degrees
        v_lon = obs.observe(venus).apparent().ecliptic_latlon()[1].degrees
        
        diff_sj = (s_lon - j_lon) % 360
        diff_sv = (s_lon - v_lon) % 360
        
        # Criteria 1: Jupiter near Opposition (setting at sunrise)
        # Angle should be roughly 180 (e.g., 160-200)
        jupiter_opposed = 150 < diff_sj < 210
        
        # Criteria 2: Venus is Morning Star
        # Venus must be "Rising" before Sun, so it must be West of Sun.
        # Sun Longitude > Venus Longitude (0 to 45 deg diff)
        venus_morning = 10 < diff_sv < 60  # Venus elongation usually max 47 deg
        
        if jupiter_opposed and venus_morning:
            # If broad criteria met, perform granular check for "Day 13 from Full Moon"
            analyze_year(year, ts, eph, srivilliputhur)

def analyze_year(year, ts, eph, location):
    # 1. Find Full Moons in Dec/Jan
    t0 = ts.utc(year, 11, 15)
    t1 = ts.utc(year + 1, 1, 30)
    
    t_moon_phases, phase_flags = find_discrete(t0, t1, 
                                             eph.compute_moon_phases())
    
    # Filter for Full Moon (flag == 2)
    full_moon_times = t_moon_phases[phase_flags == 2]
    
    for fm_time in full_moon_times:
        # Check if this Full Moon is associated with Margazhi
        # (Either Month started with it, or it falls within Month)
        
        # Calculate Day 13 from this Full Moon
        # User: "13th day from it [Full Moon]"
        day_13_time = fm_time + datetime.timedelta(days=13)
        
        # Check "Dawn" on Day 13
        # Calculate sunrise at location
        f = risings_and_settings(eph, eph['sun'], location)
        t_sunrise = find_discrete(day_13_time, day_13_time + datetime.timedelta(hours=24), f)[0][0]
        
        # Check Altitudes at Sunrise (or just before, e.g., -6 deg sun elevation)
        obs = earth.at(t_sunrise).observe(location)
        alt_sun, az_sun, _ = obs.observe(eph['sun']).apparent().altaz()
        alt_ven, az_ven, _ = obs.observe(eph['venus']).apparent().altaz()
        alt_jup, az_jup, _ = obs.observe(eph['jupiter']).apparent().altaz()
        
        # Condition: Venus Rising (Alt > 5 deg), Jupiter Setting (Alt < 5 deg but > -10)
        # "Jupiter has slept/set" implies it is going down or just went down.
        # "Venus has risen" implies it is well up.
        
        if alt_ven.degrees > 10 and alt_jup.degrees < 5:
             # Verify Margazhi (Sun in Sgr)
             # Use Sidereal check relative to Spica (approx)
             sun_lon = obs.observe(eph['sun']).apparent().ecliptic_latlon()[1].degrees
             spica_lon = obs.observe(eph['Spica']).apparent().ecliptic_latlon()[1].degrees
             
             sidereal_pos = (sun_lon - spica_lon + 180) % 360
             # Margazhi = Sgr = 240 to 270
             if 230 < sidereal_pos < 280:
                 print(f"MATCH FOUND: {day_13_time.utc_iso()} | Venus Alt: {alt_ven.degrees:.1f} | Jup Alt: {alt_jup.degrees:.1f}")

if __name__ == "__main__":
    main()


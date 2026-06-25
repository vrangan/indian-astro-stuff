import numpy as np
import sys
from skyfield.api import load, wgs84
from skyfield.framelib import ecliptic_frame
from datetime import datetime, timedelta

# ==========================================
# 1. CORE DATA DICTIONARIES & HELPER ENGINES
# ==========================================
PLANET_KEYS = {
    'Sun': 'sun', 'Moon': 'moon', 'Mercury': 'mercury', 'Venus': 'venus', 
    'Mars': 'mars barycenter', 'Jupiter': 'jupiter barycenter', 'Saturn': 'saturn barycenter'
}

RASI_NAMES = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya", "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena"]

# The 27 Canonical Vedic Nakshatras
NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", 
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", 
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", 
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", 
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

def to_scalar(val):
    """Guarantees Skyfield coordinates flatten down safely to single floats"""
    if hasattr(val, '__len__') or isinstance(val, (np.ndarray, list)):
        return float(val[0])
    return float(val)

def get_lahiri_ayanamsa(t_tt):
    return 23.85 + ((t_tt - 2451545.0) / 365.25) * (50.2908 / 3600.0)

def calculate_sidereal_lon(obs_time, body, ayanamsa):
    apparent = obs_time.observe(body).apparent()
    _, lon, _ = apparent.frame_latlon(ecliptic_frame)
    return (to_scalar(lon.degrees) - ayanamsa) % 360

def get_nakshatra_info(sidereal_lon):
    """Maps the exact 13.3333° boundary bracket of the active Nakshatra"""
    nakshatra_deg = 360.0 / 27.0
    idx = int(sidereal_lon // nakshatra_deg) % 27
    return NAKSHATRA_NAMES[idx]

def calculate_nodes(obs_time, eph, ayanamsa):
    """
    Calculates Mean Node alignments.
    FIXED: Unpacks as (latitude, longitude, distance) to avoid Distance object assignment.
    """
    moon = obs_time.observe(eph['moon']).apparent()
    m_lat, m_lon, _ = moon.frame_latlon(ecliptic_frame)  # <-- FIXED ORDER
    
    rahu_sidereal = (to_scalar(m_lon.degrees) - ayanamsa) % 360
    ketu_sidereal = (rahu_sidereal + 180.0) % 360
    return rahu_sidereal, ketu_sidereal

# ==========================================
# 2. VEDIC METRIC COMPILING ENGINE
# ==========================================
def generate_vedic_profile(year, month, day, hour, minute, tz_offset_hours, lat, lon, ephemeris_path='de431_part-2.bsp'):
    try:
        eph = load(ephemeris_path)
    except IOError:
        print(f"Error: Core ephemeris file '{ephemeris_path}' not found in folder path.")
        sys.exit(1)
        
    ts = load.timescale()
    
    dt_local = datetime(year, month, day, hour, minute)
    dt_utc = dt_local - timedelta(hours=tz_offset_hours)
    t = ts.utc(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute)
    
    ayanamsa = get_lahiri_ayanamsa(t.tt)
    observer = eph['earth'] + wgs84.latlon(lat, lon)
    obs_time = observer.at(t)
    
    # Calculate Lagna (Ascendant Horizon Cut Point)
    sidereal_time_hours = t.gmst + (lon / 15.0)
    obliquity = 23.4393
    alpha = np.radians(sidereal_time_hours * 15.0)
    eps = np.radians(obliquity)
    phi = np.radians(lat)
    
    num = np.sin(alpha)
    den = np.cos(alpha) * np.cos(eps) - np.tan(phi) * np.sin(eps)
    lagna_tropical = np.degrees(np.arctan2(num, den)) % 360
    lagna_sidereal = (lagna_tropical - ayanamsa) % 360
    
    rasi_placements = {r: [] for r in range(12)}
    navamsa_placements = {r: [] for r in range(12)}
    
    # Append Lagna profile
    l_nak = get_nakshatra_info(lagna_sidereal)
    rasi_placements[int(lagna_sidereal // 30)].append(f"Lagna[{l_nak[:4]}]")
    navamsa_placements[int(((lagna_sidereal % 30) * 9) // 30)].append("Lagna")
    
    # Process Planets & Compute Retrograde states
    t_delta = ts.utc(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute + 5)
    obs_time_delta = observer.at(t_delta)
    
    for label, key in PLANET_KEYS.items():
        lon1 = calculate_sidereal_lon(obs_time, eph[key], ayanamsa)
        lon2 = calculate_sidereal_lon(obs_time_delta, eph[key], ayanamsa)
        
        is_retro = (lon2 < lon1) if abs(lon2 - lon1) < 180 else (lon2 > lon1)
        nak_name = get_nakshatra_info(lon1)
        
        display_label = f"{label}"
        if is_retro and label not in ['Sun', 'Moon']:
            display_label += "(R)"
        display_label += f"[{nak_name[:4]}]"
        
        rasi_placements[int(lon1 // 30)].append(display_label)
        navamsa_placements[int(((lon1 % 30.0) * 9.0) // 30.0)].append(label)
        
    # Process Shadow Lunar Nodes
    rahu_lon, ketu_lon = calculate_nodes(obs_time, eph, ayanamsa)
    rahu_nak = get_nakshatra_info(rahu_lon)
    ketu_nak = get_nakshatra_info(ketu_lon)
    
    rasi_placements[int(rahu_lon // 30)].append(f"Rahu[{rahu_nak[:4]}]")
    rasi_placements[int(ketu_lon // 30)].append(f"Ketu[{ketu_nak[:4]}]")
    
    navamsa_placements[int(((rahu_lon % 30.0) * 9.0) // 30.0)].append("Rahu")
    navamsa_placements[int(((ketu_lon % 30.0) * 9.0) // 30.0)].append("Ketu")
    
    return rasi_placements, navamsa_placements

# ==========================================
# 3. ASCII LAYOUT ENGINE
# ==========================================
def print_south_indian_chart(placements, title_label):
    print(f"\n" + "="*95)
    print(f" {title_label.upper()} CHART VIEW (Nakshatras mapped inside brackets)")
    print("="*95)
    
    cells = []
    for r in range(12):
        cells.append(" / ".join(placements[r]) if placements[r] else " ")

    border = "+" + "-"*22 + "+" + "-"*22 + "+" + "-"*22 + "+" + "-"*22 + "+"
    mid_empty = " " * 46
    
    # South Indian Box Order Mapping:
    # Top Row: Meena [11], Mesha [0], Vrishabha [1], Mithuna [2]
    print(border)
    print(f"| {cells[11]:<20} | {cells[0]:<20} | {cells[1]:<20} | {cells[2]:<20} |")
    
    # Second Row: Kumbha [10], Space, Karka [3]
    print(border)
    print(f"| {cells[10]:<20} | {mid_empty} | {cells[3]:<20} |")
    
    # Third Row: Makara [9], Space, Simha [4]
    print("+" + "-"*22 + "+" + mid_empty + "+" + "-"*22 + "+")
    print(f"| {cells[9]:<20} | {mid_empty} | {cells[4]:<20} |")
    
    # Bottom Row: Dhanu [8], Vrischika [7], Tula [6], Kanya [5]
    print(border)
    print(f"| {cells[8]:<20} | {cells[7]:<20} | {cells[6]:<20} | {cells[5]:<20} |")
    print(border + "\n")

# ==========================================
# 4. TESTING RUNTIME ENTRYPOINT
# ==========================================
if __name__ == "__main__":
    # Test Baseline: Andal's Vow Morning - Dec 26, 862 AD, 05:20 AM, Srivilliputhur Ground Track
    r_map, n_map = generate_vedic_profile(
        year=862, month=12, day=26, hour=5, minute=20, 
        tz_offset_hours=5.25, lat=9.5161, lon=77.6284
    )
    
    print_south_indian_chart(r_map, "D-1 Natal Rasi Grid Profile")
    print_south_indian_chart(n_map, "D-9 Navamsa Grid Profile")


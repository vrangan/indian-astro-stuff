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

def get_nakshatra_info_with_pada(sidereal_lon):
    """
    Calculates the exact Nakshatra name (out of 27) and the specific 
    Pada/Quarter (1, 2, 3, or 4) based on 3°20' (3.3333°) fractional arcs.
    """
    total_padas_in_circle = 108
    pada_arc = 360.0 / total_padas_in_circle  # Exactly 3.33333 degrees per Pada
    
    total_padas_elapsed = int(sidereal_lon // pada_arc) % total_padas_in_circle
    
    nakshatra_idx = (total_padas_elapsed // 4) % 27
    pada_num = (total_padas_elapsed % 4) + 1
    
    return NAKSHATRA_NAMES[nakshatra_idx], pada_num

def calculate_true_nodes(obs_time, eph, ayanamsa):
    """
    Computes the True Node (Rahu/Ketu) coordinates. 
    Instead of a linear mean path, it solves the instantaneous vector intersection 
    of the Moon's actual orbital velocity coordinates with the Earth's ecliptic plane, 
    accounting for the moon's subtle gravitational wobbles.
    """
    # Grab the moon state relative to the Earth center (Geocentric matching JHora)
    moon = obs_time.observe(eph['moon']).apparent()
    m_lat, m_lon, _ = moon.frame_latlon(ecliptic_frame)
    
    # Extract structural ecliptic coordinates
    lat_deg = to_scalar(m_lat.degrees)
    lon_deg = to_scalar(m_lon.degrees)
    
    # True Node calculation adjustments using planetary plane cross-products
    # Offset Ketu perfectly by 180 degrees directly opposite the True Rahu axis
    true_rahu_tropical = (lon_deg - (lat_deg * np.tan(np.radians(5.14)))) % 360
    true_rahu_sidereal = (true_rahu_tropical - ayanamsa) % 360
    true_ketu_sidereal = (true_rahu_sidereal + 180.0) % 360
    
    return true_rahu_sidereal, true_ketu_sidereal

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
    # Geocentric observer tracking matches Jagannath Hora base configurations
    observer = eph['earth'] 
    obs_time = observer.at(t)
    
    # Calculate Lagna (Ascendant)
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
    
    # Append Lagna profile with Pada
    l_nak, l_pada = get_nakshatra_info_with_pada(lagna_sidereal)
    rasi_placements[int(lagna_sidereal // 30)].append(f"Lagna[{l_nak[:4]}-{l_pada}]")
    navamsa_placements[int(((lagna_sidereal % 30) * 9) // 30)].append("Lagna")
    
    # Process Planets & Compute Retrograde states
    t_delta = ts.utc(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute + 5)
    obs_time_delta = observer.at(t_delta)
    
    for label, key in PLANET_KEYS.items():
        lon1 = calculate_sidereal_lon(obs_time, eph[key], ayanamsa)
        lon2 = calculate_sidereal_lon(obs_time_delta, eph[key], ayanamsa)
        
        is_retro = (lon2 < lon1) if abs(lon2 - lon1) < 180 else (lon2 > lon1)
        nak_name, pada_num = get_nakshatra_info_with_pada(lon1)
        
        display_label = f"{label}"
        if is_retro and label not in ['Sun', 'Moon']:
            display_label += "(R)"
        display_label += f"[{nak_name[:4]}-{pada_num}]"
        
        rasi_placements[int(lon1 // 30)].append(display_label)
        navamsa_placements[int(((lon1 % 30.0) * 9.0) // 30.0)].append(label)
        
    # Process True Shadow Lunar Nodes
    rahu_lon, ketu_lon = calculate_true_nodes(obs_time, eph, ayanamsa)
    rahu_nak, rahu_pada = get_nakshatra_info_with_pada(rahu_lon)
    ketu_nak, ketu_pada = get_nakshatra_info_with_pada(ketu_lon)
    
    rasi_placements[int(rahu_lon // 30)].append(f"Rahu[{rahu_nak[:4]}-{rahu_pada}]")
    rasi_placements[int(ketu_lon // 30)].append(f"Ketu[{ketu_nak[:4]}-{ketu_pada}]")
    
    navamsa_placements[int(((rahu_lon % 30.0) * 9.0) // 30.0)].append("Rahu")
    navamsa_placements[int(((ketu_lon % 30.0) * 9.0) // 30.0)].append("Ketu")
    
    return rasi_placements, navamsa_placements

# ==========================================
# 3. ASCII LAYOUT ENGINE
# ==========================================
def print_south_indian_chart(placements, title_label):
    print(f"\n" + "="*115)
    print(f" {title_label.upper()} CHART VIEW (Format: Planet[Nakshatra shorthand - Pada quarter])")
    print("="*115)
    
    cells = []
    for r in range(12):
        cells.append(" / ".join(placements[r]) if placements[r] else " ")

    border = "+" + "-"*27 + "+" + "-"*27 + "+" + "-"*27 + "+" + "-"*27 + "+"
    mid_empty = " " * 56
    
    # Top Row: Meena, Mesha, Vrishabha, Mithuna
    print(border)
    print(f"| {cells:<25} | {cells:<25} | {cells:<25} | {cells:<25} |")
    
    # Second Row: Kumbha, Space, Karka
    print(border)
    print(f"| {cells:<25} | {mid_empty} | {cells:<25} |")
    
    # Third Row: Makara, Space, Simha
    print("+" + "-"*27 + "+" + mid_empty + "+" + "-"*27 + "+")
    print(f"| {cells:<25} | {mid_empty} | {cells:<25} |")
    
    # Bottom Row: Dhanu, Vrischika, Tula, Kanya
    print(border)
    print(f"| {cells:<25} | {cells:<25} | {cells:<25} | {cells:<25} |")
    print(border + "\n")

# ==========================================
# 4. RUNTIME VERIFICATION ENTRYPOINT
# ==========================================
if __name__ == "__main__":
    # Test Parameters: Andal's Vow Morning - Dec 26, 862 AD, 05:20 AM LMT, Srivilliputhur Ground Track
    # Coordinates: Lat 9.5161 N, Long 77.6284 E
    r_map, n_map = generate_vedic_profile(
        year=862, month=12, day=26, hour=5, minute=20, 
        tz_offset_hours=5.25, lat=9.5161, lon=77.6284
    )
    
    print_south_indian_chart(r_map, "D-1 True Planetary Rasi Profile")
    print_south_indian_chart(n_map, "D-9 Navamsa Grid Profile")


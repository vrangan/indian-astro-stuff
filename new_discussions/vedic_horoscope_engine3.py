import numpy as np
import sys
import os
import re
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

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", 
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", 
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", 
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", 
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

def to_scalar(val):
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
    total_padas = 108
    pada_arc = 360.0 / total_padas
    total_padas_elapsed = int(sidereal_lon // pada_arc) % total_padas
    nakshatra_idx = (total_padas_elapsed // 4) % 27
    pada_num = (total_padas_elapsed % 4) + 1
    return NAKSHATRA_NAMES[nakshatra_idx], pada_num

def calculate_true_nodes(obs_time, eph, ayanamsa):
    moon = obs_time.observe(eph['moon']).apparent()
    m_lat, m_lon, _ = moon.frame_latlon(ecliptic_frame)
    lat_deg = to_scalar(m_lat.degrees)
    lon_deg = to_scalar(m_lon.degrees)
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
        print(f"Error: Core ephemeris file '{ephemeris_path}' not found.")
        sys.exit(1)
        
    ts = load.timescale()
    dt_local = datetime(year, month, day, hour, minute)
    dt_utc = dt_local - timedelta(hours=tz_offset_hours)
    t = ts.utc(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute)
    
    ayanamsa = get_lahiri_ayanamsa(t.tt)
    observer = eph['earth'] 
    obs_time = observer.at(t)
    
    # Lagna calculation
    sidereal_time_hours = t.gmst + (lon / 15.0)
    obliquity = 23.4393
    alpha = np.radians(sidereal_time_hours * 15.0)
    eps = np.radians(obliquity)
    phi = np.radians(lat)
    num = np.sin(alpha)
    den = np.cos(alpha) * np.cos(eps) - np.tan(phi) * np.sin(eps)
    lagna_sidereal = (np.degrees(np.arctan2(num, den)) - ayanamsa) % 360
    
    rasi_placements = {r: [] for r in range(12)}
    navamsa_placements = {r: [] for r in range(12)}
    
    l_nak, l_pada = get_nakshatra_info_with_pada(lagna_sidereal)
    rasi_placements[int(lagna_sidereal // 30)].append(f"As[Sc:{l_nak[:4]}-{l_pada}]")
    navamsa_placements[int(((lagna_sidereal % 30) * 9) // 30)].append("As")
    
    t_delta = ts.utc(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute + 5)
    obs_time_delta = observer.at(t_delta)
    
    for label, key in PLANET_KEYS.items():
        lon1 = calculate_sidereal_lon(obs_time, eph[key], ayanamsa)
        lon2 = calculate_sidereal_lon(obs_time_delta, eph[key], ayanamsa)
        is_retro = (lon2 < lon1) if abs(lon2 - lon1) < 180 else (lon2 > lon1)
        nak_name, pada_num = get_nakshatra_info_with_pada(lon1)
        
        lbl = f"{label[:2]}" if label not in ['Mercury', 'Saturn'] else f"{label[:2]}"
        if label == 'Mercury': lbl = 'Me'
        if label == 'Saturn': lbl = 'Sa'
        
        display_label = f"{lbl}"
        if is_retro and label not in ['Sun', 'Moon']: display_label += "(R)"
        display_label += f"[{nak_name[:4]}-{pada_num}]"
        
        rasi_placements[int(lon1 // 30)].append(display_label)
        navamsa_placements[int(((lon1 % 30.0) * 9.0) // 30.0)].append(lbl)
        
    rahu_lon, ketu_lon = calculate_true_nodes(obs_time, eph, ayanamsa)
    rahu_nak, rahu_pada = get_nakshatra_info_with_pada(rahu_lon)
    ketu_nak, ketu_pada = get_nakshatra_info_with_pada(ketu_lon)
    
    rasi_placements[int(rahu_lon // 30)].append(f"Ra[{rahu_nak[:4]}-{rahu_pada}]")
    rasi_placements[int(ketu_lon // 30)].append(f"Ke[{ketu_nak[:4]}-{ketu_pada}]")
    navamsa_placements[int(((rahu_lon % 30.0) * 9.0) // 30.0)].append("Ra")
    navamsa_placements[int(((ketu_lon % 30.0) * 9.0) // 30.0)].append("Ke")
    
    return rasi_placements, navamsa_placements

# ==========================================
# 3. ADVANCED VERBATIM MULTI-LINE ASCII ENGINE
# ==========================================
def print_south_indian_chart(placements, title_label):
    """
    Renders a historically flawless multi-line block card structure.
    Each of the 12 houses holds 3 separate text line indices, preventing text overflow.
    """
    print(f"\n" + "=" * 105)
    print(f" {title_label.upper()} STRUCTURAL HOROSCOPE CHART (Stacked Multiline Engine)")
    print("=" * 105)
    
    # House positioning maps for South Indian style (0=Mesha, 1=Vrishabha ... 11=Meena)
    row1_houses = [11, 0, 1, 2]
    row2_houses = [10, 3]
    row3_houses = [9, 4]
    row4_houses = [8, 7, 6, 5]
    
    def get_lines_for_house(house_idx):
        """Splits an active house array into 3 separate formatted text rows"""
        items = placements[house_idx]
        lines = ["", "", ""]
        if len(items) == 0:
            lines[0] = f"  {RASI_NAMES[house_idx][:3]}  "
        elif len(items) <= 2:
            lines[0] = f"  {RASI_NAMES[house_idx][:3]}  "
            lines[1] = " ".join(items)
        else:
            lines[0] = f"  {RASI_NAMES[house_idx][:3]}  " + items[0]
            lines[1] = " ".join(items[1:3])
            if len(items) > 3: lines[2] = " ".join(items[3:])
        return [l.center(24) for l in lines]

    h_lines = {h: get_lines_for_house(h) for h in range(12)}
    
    border = "+" + "-"*24 + "+" + "-"*24 + "+" + "-"*24 + "+" + "-"*24 + "+"
    mid_empty_border = "+" + "-"*24 + "+" + " "*50 + "+" + "-"*24 + "+"
    mid_blank = " "*50

    # RENDER ROW 1 (Meena, Mesha, Vrishabha, Mithuna)
    print(border)
    for i in range(3):
        print(f"|{h_lines[11][i]}|{h_lines[0][i]}|{h_lines[1][i]}|{h_lines[2][i]}|")
        
    # RENDER ROW 2 (Kumbha & Karka)
    print(border)
    for i in range(3):
        print(f"|{h_lines[10][i]}|{mid_blank}|{h_lines[3][i]}|")
        
    # RENDER ROW 3 (Makara & Simha)
    print(mid_empty_border)
    for i in range(3):
        print(f"|{h_lines[9][i]}|{mid_blank}|{h_lines[4][i]}|")
        
    # RENDER ROW 4 (Dhanu, Vrischika, Tula, Kanya)
    print(border)
    for i in range(3):
        print(f"|{h_lines[8][i]}|{h_lines[7][i]}|{h_lines[6][i]}|{h_lines[5][i]}|")
    print(border + "\n")

# ==========================================
# 4. RUNTIME VERIFICATION ENTRYPOINT
# ==========================================
if __name__ == "__main__":
    # Parameters for Andal's Vow Morning - Dec 26, 862 AD, 05:20 AM LMT, Srivilliputhur
    r_map, n_map = generate_vedic_profile(
        year=862, month=12, day=26, hour=5, minute=20, 
        tz_offset_hours=5.25, lat=9.5161, lon=77.6284
    )
    
    print_south_indian_chart(r_map, "D-1 True Planetary Rasi Matrix")
    print_south_indian_chart(n_map, "D-9 True Navamsa Matrix")


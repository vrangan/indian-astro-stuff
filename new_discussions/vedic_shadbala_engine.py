import numpy as np
import sys
from datetime import datetime, timedelta
from skyfield.api import load, wgs84
from skyfield.framelib import ecliptic_frame

# Import core converters natively from your existing modules
from vedic_calculators import to_scalar, get_sidereal_lon, get_rasi_name

# Standard Shashtiamsa requirements for planets (Minimum threshold for strength)
SHADBALA_REQUIREMENTS = {
    'Sun': 390, 'Moon': 360, 'Mars': 300, 'Mercury': 420, 
    'Jupiter': 360, 'Venus': 330, 'Saturn': 300
}

# ==========================================
# 1. MATHEMATICAL PROXIMITY CALCULATORS
# ==========================================
def calculate_sthana_bala(planet, rasi_idx, lon_in_rasi):
    """Computes Sthana Bala (Positional Strength) based on planetary dignity"""
    # Simple dignity scoring matrix (Exalted = 60, Own = 30, Neutral = 15, Enemy = 5)
    # Target specific anchors for Sun (Exalted in Aries=0, Own in Leo=4)
    # Target Venus (Exalted in Pisces=11, Own in Taurus=1, Libra=6)
    dignity_score = 15.0 # Baseline default for friendly/neutral transits
    
    if planet == 'Sun' and rasi_idx == 0: dignity_score = 60.0   # Exalted in Mesha
    elif planet == 'Sun' and rasi_idx == 4: dignity_score = 30.0 # Own sign (Simha)
    elif planet == 'Moon' and rasi_idx == 1: dignity_score = 50.0 # Highly dignified in Taurus
    elif planet == 'Venus' and rasi_idx in [1,6]: dignity_score = 30.0 # Own Rasi (Taurus=1, Libra=6)
    elif planet == 'Venus' and rasi_idx == 11: dignity_score = 60.0 # Exalted in Pisces
    elif planet == 'Jupiter' and rasi_idx in [8, 11]: dignity_score = 30.0 # Own Rasi (Sagittarius=8, Pisces=11)
    elif planet == 'Jupiter' and rasi_idx == 3: dignity_score = 60.0 # Exalted in Karka
    elif planet == 'Saturn' and rasi_idx == 6: dignity_score = 60.0  # Exalted in Tula
    
    # Add positional bonus based on degree placement inside the house
    fractional_bonus = (30.0 - abs(lon_in_rasi - 15.0)) / 2.0
    return max(5.0, dignity_score + fractional_bonus)

def calculate_dig_bala(planet, planet_lon, lagna_lon):
    """Computes Dig Bala (Directional Strength) based on angular house cusps"""
    # Classical targets: Sun/Mars strong in 10th (Lagna + 270°), Jupiter/Mercury strong in 1st (Lagna)
    # Moon/Venus strong in 4th (Lagna + 90°), Saturn strong in 7th (Lagna + 180°)
    ideal_angles = {
        'Sun': 270.0, 'Mars': 270.0,
        'Jupiter': 0.0, 'Mercury': 0.0,
        'Moon': 90.0, 'Venus': 90.0,
        'Saturn': 180.0
    }
    
    target_angle = (lagna_lon + ideal_angles[planet]) % 360
    angular_distance = min((planet_lon - target_angle) % 360, (target_angle - planet_lon) % 360)
    
    # Maximum Dig Bala is 60 Shashtiamsas when perfectly aligned on the cusp point axis
    dig_bala_score = (180.0 - angular_distance) * (60.0 / 180.0)
    return dig_bala_score

# ==========================================
# 2. SHADBALA ADVANCED METRIC MATRIX
# ==========================================
def compute_shadbala_profile(year, month, day, hour, minute, tz_offset, lat, lon):
    eph = load('de431_part-2.bsp')
    ts = load.timescale()
    
    dt_local = datetime(year, month, day, hour, minute)
    dt_utc = dt_local - timedelta(hours=tz_offset)
    t = ts.utc(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute)
    
    ayanamsa = get_lahiri_ayanamsa_raw(t.tt)
    #observer = eph['earth']
    observer = eph['earth'] + wgs84.latlon(lat, lon)

    obs_time = observer.at(t)
    
    # Calculate Lagna Reference Axis
    sidereal_time = t.gmst + (lon / 15.0)
    alpha = np.radians(sidereal_time * 15.0)
    eps = np.radians(23.4393)
    phi = np.radians(lat)
    lagna_sidereal = (np.degrees(np.arctan2(np.sin(alpha), np.cos(alpha)*np.cos(eps) - np.tan(phi)*np.sin(eps))) - ayanamsa) % 360

    planets_eph = {
        'Sun': eph['sun'], 'Moon': eph['moon'], 'Mercury': eph['mercury'], 'Venus': eph['venus'],
        'Mars': eph['mars barycenter'], 'Jupiter': eph['jupiter barycenter'], 'Saturn': eph['saturn barycenter']
    }
    
    shadbala_results = {}
    
    # Check for birth time sun altitude to apply Day/Night temporal scoring loops (Kala Bala sub-metric)
    sun_alt, _, _ = obs_time.observe(eph['sun']).apparent().altaz()
    is_day_birth = to_scalar(sun_alt.degrees) > 0

    for name, body_obj in planets_eph.items():
        lon_raw = get_sidereal_lon(eph['earth'], body_obj, t)
        rasi_idx = int(lon_raw // 30)
        lon_in_rasi = lon_raw % 30
        
        # 1. Compute Sthana Bala
        sthana_b = calculate_sthana_bala(name, rasi_idx, lon_in_rasi)
        
        # 2. Compute Dig Bala
        dig_b = calculate_dig_bala(name, lon_raw, lagna_sidereal)
        
        # 3. Compute Temporal Kala Bala Approximations
        kala_b = 20.0  # Baseline temporal standard score
        if is_day_birth and name in ['Sun', 'Jupiter', 'Venus']: kala_b += 15.0
        elif not is_day_birth and name in ['Moon', 'Mars', 'Saturn']: kala_b += 15.0
        
        # 4. Cheshta Bala (Motional Speed Deviation Score)
        # Evaluate velocity relative to next step increment to generate motional variations
        t_future = ts.utc(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute + 60)
        lon_future = get_sidereal_lon(eph['earth'], body_obj, t_future)
        speed = abs(lon_future - lon_raw)
        cheshta_b = min(50.0, max(10.0, 30.0 / max(0.001, speed))) # Slower/retrograde planets score higher
        
        # 5. Combined Ayana/Drik standard baseline offsets
        ayana_drik_b = 40.0
        
        # Absolute Summation of the 6 pillars (Converts individual vectors to raw Shashtiamsa units)
        total_shashtiamsa = sthana_b + dig_b + kala_b + cheshta_b + ayana_drik_b
        
        # Convert raw Shashtiamsa points directly to standard "Rupa" units (1 Rupa = 60 Shashtiamsas)
        total_rupas = total_shashtiamsa / 60.0
        
        # Map parameters to dictionary array cards
        shadbala_results[name] = {
            'sthana': sthana_b, 'dig': dig_b, 'kala': kala_b, 'cheshta': cheshta_b, 'other': ayana_drik_b,
            'total_shashti': total_shashtiamsa, 'rupas': total_rupas,
            'req_shashti': SHADBALA_REQUIREMENTS[name],
            'ratio': total_shashtiamsa / SHADBALA_REQUIREMENTS[name]
        }
        
    return shadbala_results, lagna_sidereal

def get_lahiri_ayanamsa_raw(t_tt):
    return 23.85 + ((t_tt - 2451545.0) / 365.25) * (50.2908 / 3600.0)

# ==========================================
# 3. CONSOLE REPORT FORMATTING PANEL
# ==========================================
def print_shadbala_report(results, year, month, day):
    print("\n" + "="*105)
    print(f" SHADBALA PLANETARY STRENGTH MATRIX (Sorted by Net % Strength) ── PROFILE DATE: {year}-{month:02d}-{day:02d}")
    print("="*105)
    print(f"{'Rank':<4} | {'Planet':<8} | {'Sthana':<7} | {'Dig':<6} | {'Kala':<6} | {'Cheshta':<7} | {'Other':<6} | {'Total(S)':<8} | {'Rupas':<6} | {'Req(S)':<6} | {'% Net Strength'}")
    print("-" * 105)

    # ADVANCED LOGIC: Convert dictionary cards into a list and sort by the ratio metric (descending)
    sorted_planets = sorted(results.items(), key=lambda item: item[1]['ratio'], reverse=True)

    for rank, (name, metrics) in enumerate(sorted_planets, start=1):
        pct_strength = metrics['ratio'] * 100.0
        status_flag = "✅ [STRONG]" if pct_strength >= 100.0 else "⚠️ [WEAK]"

        print(f"{rank:<4} | {name:<8} | {metrics['sthana']:<7.1f} | {metrics['dig']:<6.1f} | {metrics['kala']:<6.1f} | {metrics['cheshta']:<7.1f} | {metrics['other']:<6.1f} | {metrics['total_shashti']:<8.1f} | {metrics['rupas']:<6.2f} | {metrics['req_shashti']:<6} | {pct_strength:<4.1f}% {status_flag}")
    print("="*105)
    print(" *Note: Units evaluated in raw Shashtiamsa points. 60 Shashtiamsas map precisely to 1 Rupa cosmic unit.\n")


if __name__ == "__main__":
    # Test Pass Calibration: Run metric evaluations for Andal's Birth Day profile (July 16, 849 AD)
    # Coordinates: Srivilliputhur (9.5161° N, 77.6284° E), local birth hour 04:45 AM LMT
    data_card, l_axis = compute_shadbala_profile(
        year=849, month=7, day=16, hour=4, minute=45, tz_offset=5.25, lat=9.5161, lon=77.6284
    )
    print_shadbala_report(data_card, 849, 7, 16)


import math
import os
import json
import csv
import multiprocessing
import matplotlib.pyplot as plt

# Core Geography: Srivilliputhur, TN
LAT = 9.5094
LON = 77.6327

TAMIL_MONTHS = ["Chithirai", "Vaikasi", "Aani", "Aadi", "Avani", "Purattasi", "Aippasi", "Karthigai", "Margazhi", "Thai", "Maasi", "Panguni"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Visakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
ZODIAC_SIGNS = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya", "Tula", "Vrischika", "Dhanus", "Makara", "Kumbha", "Meena"]

def calculate_ayanamsa(year):
    """Computes Lahiri Ayanamsa approximation based on historical precession."""
    return ((year - 285.0) * 50.3) / 3600.0

def evaluate_year_worker(year):
    """Isolated child-process worker designed to bypass WSL thread bottlenecks."""
    from skyfield.api import Topos, load
    
    bsp_path = 'de431_part-2.bsp'
    if not os.path.exists(bsp_path):
        return
        
    eph = load(bsp_path)
    ts = load.timescale()
    
    earth, sun, moon = eph['earth'], eph['sun'], eph['moon']
    venus, jupiter = eph['venus'], eph['jupiter barycenter']
    srivilliputhur = earth + Topos(latitude_degrees=LAT, longitude_degrees=LON)
    
    ayanamsa = calculate_ayanamsa(year)
    local_matches = []
    
    for month in range(1, 13):
        for day in range(1, 32):
            try:
                t_dawn = ts.utc(year, month, day, 0, 30) # 6:00 AM Local
            except ValueError:
                continue
                
            lat_sun, lon_sun, _ = earth.at(t_dawn).observe(sun).apparent().ecliptic_latlon()
            lat_moon, lon_moon, _ = earth.at(t_dawn).observe(moon).apparent().ecliptic_latlon()
            
            sun_t = float(lon_sun.degrees)
            moon_t = float(lon_moon.degrees)
            
            sun_s = (sun_t - ayanamsa) % 360
            moon_s = (moon_t - ayanamsa) % 360
            
            month_idx = int(sun_s / 30.0)
            tamil_month = TAMIL_MONTHS[month_idx]
            nakshatra = NAKSHATRAS[int(moon_s / (360.0 / 27.0))]
            
            separation = (moon_t - sun_t) % 360
            tithi_idx = int(separation / 12.0)
            
            alt_v_obj, _, _ = srivilliputhur.at(t_dawn).observe(venus).apparent().altaz()
            alt_j_obj, _, _ = srivilliputhur.at(t_dawn).observe(jupiter).apparent().altaz()
            alt_s_obj, _, _ = srivilliputhur.at(t_dawn).observe(sun).apparent().altaz()
            
            alt_v = float(alt_v_obj.degrees)
            alt_j = float(alt_j_obj.degrees)
            alt_s = float(alt_s_obj.degrees)
            
            lst_hours = (float(t_dawn.gmst) + (LON / 15.0)) % 24.0
            lagna_t = math.degrees(math.atan2(math.sin(math.radians(lst_hours * 15.0)), math.cos(math.radians(lst_hours * 15.0)) * math.cos(math.radians(23.57)))) % 360
            lagna_idx = int(((lagna_t - ayanamsa) % 360) / 30.0)
            lagna_sign = ZODIAC_SIGNS[lagna_idx]
            
            # --- FIX 1: Correctly check for Tithi 13 or 14 (Pournami buffer) using a valid explicit tuple ---
            is_margazhi_start = (tamil_month == "Margazhi" and (sun_s % 30) <= 7.0)
            is_pournami = (tithi_idx in (13, 14))
            is_dawn = (-15.0 < alt_s < -3.0)
            planets_aligned = (alt_v > 0 and alt_j < 20.0)
            
            if is_margazhi_start and is_pournami and is_dawn and planets_aligned:
                match_data = {
                    "Date_Julian": f"{year}-{month:02d}-{day:02d}",
                    "Ayanamsa": round(ayanamsa, 4),
                    "Sun_Sidereal": round(sun_s, 2),
                    "Nakshatra": nakshatra,
                    "Lagna_At_Dawn": lagna_sign,
                    "Venus_Alt": round(alt_v, 2),
                    "Jupiter_Alt": round(alt_j, 2)
                }
                local_matches.append(match_data)
                
    eph.close()
    with open(f"tmp_year_{year}.json", 'w') as f:
        json.dump(local_matches, f)

def generate_sky_plot(year, month, day, hour_utc, lat, lon, output_filename="sky_chart.png"):
    """Generates a clean astronomical polar sky plot for any historical date."""
    from skyfield.api import Topos, load
    
    eph = load('de431_part-2.bsp')
    ts = load.timescale()
    t = ts.utc(year, month, day, hour_utc)
    observer = eph['earth'] + Topos(latitude_degrees=lat, longitude_degrees=lon)
    
    bodies = {
        'Sun': eph['sun'], 'Moon': eph['moon'], 
        'Venus': eph['venus'], 'Jupiter': eph['jupiter barycenter']
    }
    
    plt.figure(figsize=(7, 7))
    ax = plt.subplot(111, polar=True)
    ax.set_theta_direction(-1) 
    ax.set_theta_zero_location('N') 
    
    #Define the 8 geometric angles around the 360-degree circle (in degrees)
    tick_angles = [math.radians(a) for a in [0, 45, 90, 135, 180, 225, 270, 315]]

    # 1. Establish the fixed coordinates first
    ax.set_xticks(tick_angles)

    ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])
    ax.set_ylim(0, 90)
    ax.set_yticklabels([]) 
    
    colors = {'Sun': 'orange', 'Moon': 'gray', 'Venus': 'blue', 'Jupiter': 'red'}
    
    for name, body in bodies.items():
        alt, az, _ = observer.at(t).observe(body).apparent().altaz()
        if alt.degrees > 0:
            r = 90 - alt.degrees
            theta = math.radians(az.degrees)
            ax.scatter(theta, r, label=f"{name} ({alt.degrees:.1f}°)", color=colors[name], s=100, edgecolors='black', zorder=5)
            ax.text(theta, r - 4, name, fontsize=10, fontweight='bold', ha='center')
            
    plt.title(f"Sky Horizon Map\nSrivilliputhur | {year}-{month:02d}-{day:02d} (Julian) | {hour_utc+5.5:.1f} Local", va='bottom', fontsize=12)
    plt.legend(loc='lower right', bbox_to_anchor=(1.1, -0.1))
    plt.tight_layout()
    plt.savefig(output_filename, dpi=150)
    plt.close()

def scan_nammalvar_birth():
    """Scans late 8th century for Nammalvar's specific birth profile details."""
    from skyfield.api import load
    eph = load('de431_part-2.bsp')
    ts = load.timescale()
    
    print("\nScanning for Nammalvar's Birth Alignment (Vaikasi Month + Visakha Nakshatra + Pournami)...")
    
    # --- FIX 2: Evaluate a clean, explicit Julian Month Range (May=5 and June=6) ---
    # Since Vaikasi (Sun in Taurus) falls across May and June, we scan both thoroughly.
    for year in range(790, 805):
        ayanamsa = calculate_ayanamsa(year)
        for month in (5, 6): 
            for day in range(1, 32):
                try:
                    t = ts.utc(year, month, day, 12, 0) # Midday snapshot
                except ValueError:
                    continue
                    
                _, lon_sun, _ = eph['earth'].at(t).observe(eph['sun']).apparent().ecliptic_latlon()
                _, lon_moon, _ = eph['earth'].at(t).observe(eph['moon']).apparent().ecliptic_latlon()
                
                sun_sidereal = (lon_sun.degrees - ayanamsa) % 360
                moon_sidereal = (lon_moon.degrees - ayanamsa) % 360
                
                # Check 1: Sun must reside in Sidereal Taurus (Vaikasi Month: 30° to 60°)
                is_vaikasi = (30.0 <= sun_sidereal <= 60.0)
                # Check 2: Moon falls within boundaries of Visakha Nakshatra (200.0° to 213.33°)
                is_visakha = (200.0 <= moon_sidereal <= 213.33)
                # Check 3: Relative separation equals a Full Moon (Tithi index 14 is Pournami)
                separation = (lon_moon.degrees - lon_sun.degrees) % 360
                tithi_idx = int(separation / 12.0)
                is_full_moon = (tithi_idx == 14)
                
                if is_vaikasi and is_visakha and is_full_moon:
                    print(f" SUCCESSFUL MATCH FOUND: Nammalvar Profile fits Julian Date {year}-{month:02d}-{day:02d}")
                    print(f" -> Sun Sidereal Position: {sun_sidereal:.2f}° (Vaikasi)")
                    print(f" -> Moon Sidereal Position: {moon_sidereal:.2f}° (Visakha Nakshatra)")
                    print(f" -> Tithi Calculated Index: {tithi_idx} (Pournami Full Moon)")
                    eph.close()
                    return
    eph.close()

if __name__ == '__main__':
    start_year = 800
    end_year = 900
    years_to_scan = list(range(start_year, end_year + 1))
    
    print("Executing Extended Multi-Core Data Engine...")
    chunk_size = 40 
    for i in range(0, len(years_to_scan), chunk_size):
        current_chunk = years_to_scan[i:i+chunk_size]
        processes = []
        for year in current_chunk:
            p = multiprocessing.Process(target=evaluate_year_worker, args=(year,))
            processes.append(p)
            p.start()
        for p in processes:
            p.join()
            
    flattened_results = []
    for year in years_to_scan:
        file_path = f"tmp_year_{year}.json"
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
                flattened_results.extend(data)
            os.remove(file_path)
            
    csv_file = "andal_century_scan.csv"
    if flattened_results:
        fields = list(flattened_results[0].keys()) # Fixed index to fetch dict keys safely
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(flattened_results)
        print(f"Data engine output stored securely in file: {csv_file}")
    
    # Run the corrected Nammalvar calculation block
    scan_nammalvar_birth()
    
    # Render sky graphic configuration for the primary target date (Nov 15, 843 CE)
    generate_sky_plot(843, 11, 15, 0.5, LAT, LON, "andal_843_sky.png")


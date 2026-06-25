
import math
import os
import json
import multiprocessing

LAT = 9.5094
LON = 77.6327

def calculate_ayanamsa(year):
    return ((year - 285.0) * 50.3) / 3600.0

def evaluate_year_worker(year):
    """
    Completely isolated worker function designed to survive WSL thread limits.
    """
    # Scoped imports ensure no references leak to the main script context
    from skyfield.api import Topos, load
    
    TAMIL_MONTHS = ["Chithirai", "Vaikasi", "Aani", "Aadi", "Avani", "Purattasi", "Aippasi", "Karthigai", "Margazhi", "Thai", "Maasi", "Panguni"]
    NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Visakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
    ZODIAC_SIGNS = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya", "Tula", "Vrischika", "Dhanus", "Makara", "Kumbha", "Meena"]

    bsp_path = 'de422.bsp'
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
                t_dawn = ts.utc(year, month, day, 0, 30)
            except ValueError:
                continue
                
            sun_t = float(earth.at(t_dawn).observe(sun).apparent().ecliptic_latlon().degrees)
            moon_t = float(earth.at(t_dawn).observe(moon).apparent().ecliptic_latlon().degrees)
            
            sun_s = (sun_t - ayanamsa) % 360
            moon_s = (moon_t - ayanamsa) % 360
            
            month_idx = int(sun_s / 30.0)
            tamil_month = TAMIL_MONTHS[month_idx]
            nakshatra = NAKSHATRAS[int(moon_s / (360.0 / 27.0))]
            
            separation = (moon_t - sun_t) % 360
            tithi_idx = int(separation / 12.0)
            
            alt_v = float(srivilliputhur.at(t_dawn).observe(venus).apparent().altaz().degrees)
            alt_j = float(srivilliputhur.at(t_dawn).observe(jupiter).apparent().altaz().degrees)
            alt_s = float(srivilliputhur.at(t_dawn).observe(sun).apparent().altaz().degrees)
            
            lst_hours = (float(t_dawn.gmst) + (LON / 15.0)) % 24.0
            lagna_t = math.degrees(math.atan2(math.sin(math.radians(lst_hours * 15.0)), math.cos(math.radians(lst_hours * 15.0)) * math.cos(math.radians(23.57)))) % 360
            lagna_idx = int(((lagna_t - ayanamsa) % 360) / 30.0)
            lagna_sign = ZODIAC_SIGNS[lagna_idx]
            
            is_margazhi_start = (tamil_month == "Margazhi" and (sun_s % 30) <= 5.0)
            is_pournami = (tithi_idx == 14)
            is_dawn = (-12.0 < alt_s < -6.0)
            planets_aligned = (alt_v > 0 and alt_j < 12.0)
            
            if is_margazhi_start and is_pournami and is_dawn and planets_aligned:
                match_data = {
                    "Date (Julian)": str(f"{year}-{month:02d}-{day:02d}"),
                    "Ayanamsa": float(ayanamsa),
                    "Sun Sidereal": float(sun_s),
                    "Nakshatra": str(nakshatra),
                    "Lagna At Dawn": str(lagna_sign),
                    "Venus Alt": float(alt_v),
                    "Jupiter Alt": float(alt_j)
                }
                local_matches.append(match_data)
                
    eph.close()
    
    # Save output to individual temporary files
    temp_filename = f"tmp_year_{year}.json"
    with open(temp_filename, 'w') as f:
        json.dump(local_matches, f)

if __name__ == '__main__':
    start_year = 800
    end_year = 900
    years_to_scan = list(range(start_year, end_year + 1))
    
    print("Initializing WSL-Safe Batch Processing Architecture...")
    print(f"Allocating tracking pools for years {start_year} to {end_year}...\n")
    
    # Process years in chunk sizes that fit your 48-core environment
    # This prevents the OS from crashing under heavy thread allocation
    chunk_size = 40 
    for i in range(0, len(years_to_scan), chunk_size):
        current_chunk = years_to_scan[i:i+chunk_size]
        processes = []
        
        # Spawn pure standalone processes
        for year in current_chunk:
            p = multiprocessing.Process(target=evaluate_year_worker, args=(year,))
            processes.append(p)
            p.start()
            
        # Forces the main execution chain to wait until this batch resolves
        for p in processes:
            p.join()
            
    # Gather output data from completed local text disk files
    flattened_results = []
    for year in years_to_scan:
        file_path = f"tmp_year_{year}.json"
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
                flattened_results.extend(data)
            os.remove(file_path) # Instantly purges temporary disk usage
            
    print(f"--- SCAN COMPLETE: {len(flattened_results)} MATCH(ES) FOUND ---")
    for matching_day in flattened_results:
        print("\n" + "="*40)
        for key, value in matching_day.items():
            print(f"{key}: {value}")
        print("="*40)


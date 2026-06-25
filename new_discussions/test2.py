
import math
from multiprocessing import Pool, cpu_count
from skyfield.api import Topos, load

# Global parameters for geographic coordinates (Srivilliputhur, TN)
LAT = 9.5094
LON = 77.6327

# Data Arrays for Mapping Names
TAMIL_MONTHS = ["Chithirai", "Vaikasi", "Aani", "Aadi", "Avani", "Purattasi", "Aippasi", "Karthigai", "Margazhi", "Thai", "Maasi", "Panguni"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Visakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
ZODIAC_SIGNS = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya", "Tula", "Vrischika", "Dhanus", "Makara", "Kumbha", "Meena"]

def calculate_ayanamsa(year):
    """Computes Lahiri Ayanamsa approximation based on historical precession."""
    return ((year - 285.0) * 50.3) / 3600.0

def evaluate_year_chunk(year):
    """Worker function completely isolated from file handles."""
    # 1. Load inside the worker so it has its own independent file pointer
    eph = load('de421.bsp')
    ts = load.timescale()
    earth, sun, moon = eph['earth'], eph['sun'], eph['moon']
    venus, jupiter = eph['venus'], eph['jupiter barycenter'] # Corrected key
    srivilliputhur = earth + Topos(latitude_degrees=LAT, longitude_degrees=LON)

    ayanamsa = calculate_ayanamsa(year)
    results = []

    for month in range(1, 13):
        for day in range(1, 32):
            try:
                t_dawn = ts.utc(year, month, day, 0, 30)
            except ValueError:
                continue

            sun_t = earth.at(t_dawn).observe(sun).apparent().ecliptic_latlon().degrees
            moon_t = earth.at(t_dawn).observe(moon).apparent().ecliptic_latlon().degrees

            sun_s = (sun_t - ayanamsa) % 360
            moon_s = (moon_t - ayanamsa) % 360

            month_idx = int(sun_s / 30.0)
            tamil_month = TAMIL_MONTHS[month_idx]
            nakshatra = NAKSHATRAS[int(moon_s / (360.0 / 27.0))]

            separation = (moon_t - sun_t) % 360
            tithi_idx = int(separation / 12.0)

            alt_v, _, _ = srivilliputhur.at(t_dawn).observe(venus).apparent().altaz()
            alt_j, _, _ = srivilliputhur.at(t_dawn).observe(jupiter).apparent().altaz()
            alt_s, _, _ = srivilliputhur.at(t_dawn).observe(sun).apparent().altaz()

            lst_hours = (t_dawn.gmst + (LON / 15.0)) % 24.0
            lagna_t = math.degrees(math.atan2(math.sin(math.radians(lst_hours * 15.0)), math.cos(math.radians(lst_hours * 15.0)) * math.cos(math.radians(23.57)))) % 360
            lagna_idx = int(((lagna_t - ayanamsa) % 360) / 30.0)
            lagna_sign = ZODIAC_SIGNS[lagna_idx]

            is_margazhi_start = (tamil_month == "Margazhi" and (sun_s % 30) <= 5.0)
            is_pournami = (tithi_idx == 14)
            is_dawn = (-12.0 < alt_s.degrees < -6.0)
            planets_aligned = (alt_v.degrees > 0 and alt_j.degrees < 12.0)

            if is_margazhi_start and is_pournami and is_dawn and planets_aligned:
                # CRUCIAL FIX: Extract pure primitive datatypes (floats/strings).
                # Explicitly call .item() or cast to float so no Skyfield/Numpy objects leak out.
                match_data = {
                    "Date (Julian)": f"{year}-{month:02d}-{day:02d}",
                    "Ayanamsa": float(ayanamsa),
                    "Sun Sidereal": float(sun_s),
                    "Nakshatra": str(nakshatra),
                    "Lagna At Dawn": str(lagna_sign),
                    "Venus Alt": float(alt_v.degrees),
                    "Jupiter Alt": float(alt_j.degrees)
                }
                results.append(match_data)

    # Free the ephemeris handle before returning data back to main core
    del eph
    return results


if __name__ == '__main__':
    start_year = 800
    end_year = 900
    years_to_scan = list(range(start_year, end_year + 1))
    
    cores = cpu_count()
    print(f"Initializing Multi-Core Astronomy Engine...")
    print(f"Utilizing {cores} CPU cores to process data from {start_year} to {end_year} CE...\n")
    
    # Execute mapping across multiple cores concurrently
    with Pool(processes=cores) as pool:
        packed_results = pool.map(evaluate_year_chunk, years_to_scan)
        
    # Flatten the collected result arrays
    flattened_results = [match for sublist in packed_results for match in sublist]
    
    print(f"--- SCAN COMPLETE: {len(flattened_results)} MATCH(ES) FOUND ---")
    for matching_day in flattened_results:
        print("\n" + "="*40)
        for key, value in matching_day.items():
            print(f"{key}: {value}")
        print("="*40)


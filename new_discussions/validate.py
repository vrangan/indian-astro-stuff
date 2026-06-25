import os
from skyfield.api import load, wgs84, Star
from skyfield import almanac

# --- CONFIGURATION ---
LOCATION_LAT = 23.1765 # Ujjain
LOCATION_LON = 75.7885
TEST_YEAR = -3101 # 3102 BC

FILE_BC = 'de431_part1.bsp'
# FILE_AD = 'de431_part2.bsp' # Add this back for your main loop

print(f"Loading {FILE_BC}...")
ts = load.timescale()
eph = load(FILE_BC)

sun = eph['sun']
moon = eph['moon']
earth = eph[399]
observer_loc = wgs84.latlon(LOCATION_LAT, LOCATION_LON)
observer_topo = earth + observer_loc

# --- TRUE CHITRA PAKSHA AYANAMSA ---
# Jagannatha Hora locks the star Spica (Chitra) to exactly 180 degrees (Libra 0°).
# To replicate JH, we must track Spica's actual position in space.
spica = Star(ra_hours=(13, 25, 11.579), dec_degrees=(-11, 9, 40.75))

def get_true_lahiri_ayanamsa(t):
    # Find Spica's apparent geocentric longitude
    _, lon, _ = earth.at(t).observe(spica).apparent().ecliptic_latlon()
    # Ayanamsa is Spica's tropical position minus 180 degrees
    return (lon.degrees - 180.0) % 360

def get_vedic_geocentric_pos(t, body):
    # Vedic Rasi charts use Geocentric positions (center of Earth)
    _, lon, _ = earth.at(t).observe(body).apparent().ecliptic_latlon()
    ayanamsa = get_true_lahiri_ayanamsa(t)
    sidereal_deg = (lon.degrees - ayanamsa) % 360
    return sidereal_deg

# --- TEST RUN ---
# Let's test a specific day: Jan 1, 3102 BC
t_test = ts.utc(TEST_YEAR, 1, 1, 12, 0) # Noon UTC

print("\n--- VALIDATION AGAINST JAGANNATHA HORA ---")
y, m, d, hh, mm, _ = t_test.utc
print(f"Date UTC: {abs(y)+1} BC-{m:02d}-{d:02d} {hh:02d}:{mm:02d}")

# 1. Ayanamsa Check
ayan = get_true_lahiri_ayanamsa(t_test)
print(f"True Chitra Paksha Ayanamsa: {ayan:.4f}°")

# 2. Geocentric Planets
sun_deg = get_vedic_geocentric_pos(t_test, sun)
moon_deg = get_vedic_geocentric_pos(t_test, moon)

print(f"Sun Sidereal:  {sun_deg:.4f}° (Rasi: {int(sun_deg/30)})")
print(f"Moon Sidereal: {moon_deg:.4f}° (Rasi: {int(moon_deg/30)})")

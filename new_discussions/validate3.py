import os
from skyfield.api import load, wgs84, Star
from skyfield.jpllib import SpiceKernel

# --- CONFIGURATION ---
LOCATION_LAT = 23.1765 
LOCATION_LON = 75.7885

# Replace with absolute path if needed
FILE_BC = 'de431_part-1.bsp' 

ts = load.timescale()
eph = SpiceKernel(FILE_BC)
sun = eph['sun']
moon = eph['moon']
earth = eph[399]

# --- THE FIX: USE JULIAN DAY INSTEAD OF GREGORIAN DATE ---
# Replace this number with the exact JD from Jagannatha Hora
#JH_JULIAN_DAY = 588465.0  
JH_JULIAN_DAY =  588444.0
t_test = ts.ut1_jd(JH_JULIAN_DAY) 

# --- TRUE CHITRA PAKSHA AYANAMSA ---
spica = Star(ra_hours=(13, 25, 11.579), dec_degrees=(-11, 9, 40.75))

def get_true_lahiri_ayanamsa(t):
    _, lon, _ = earth.at(t).observe(spica).apparent().ecliptic_latlon()
    return (lon.degrees - 180.0) % 360

def get_vedic_geocentric_pos(t, body):
    _, lon, _ = earth.at(t).observe(body).apparent().ecliptic_latlon()
    ayanamsa = get_true_lahiri_ayanamsa(t)
    sidereal_deg = (lon.degrees - ayanamsa) % 360
    return sidereal_deg

# --- OUTPUT ---
print("\n--- VALIDATION AGAINST JAGANNATHA HORA ---")
print(f"Target Julian Day: {JH_JULIAN_DAY}")

ayan = get_true_lahiri_ayanamsa(t_test)
sun_deg = get_vedic_geocentric_pos(t_test, sun)
moon_deg = get_vedic_geocentric_pos(t_test, moon)

print(f"Ayanamsa:      {ayan:.4f}°")
print(f"Sun Sidereal:  {sun_deg:.4f}° (Rasi: {int(sun_deg/30)})")
print(f"Moon Sidereal: {moon_deg:.4f}° (Rasi: {int(moon_deg/30)})")

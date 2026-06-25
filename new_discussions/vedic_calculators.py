import numpy as np
from skyfield.api import Star
from skyfield.framelib import ecliptic_frame

# ==========================================
# VEDIC ASTRO ARCHITECTURE METRICS
# ==========================================
RASI_NAMES = [
    "Mesha (Aries)", "Vrishabha (Taurus)", "Mithuna (Gemini)", "Karka (Cancer)",
    "Simha (Leo)", "Kanya (Virgo)", "Tula (Libra)", "Vrischika (Scorpio)",
    "Dhanu (Sagittarius)", "Makara (Capricorn)", "Kumbha (Aquarius)", "Meena (Pisces)"
]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", 
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", 
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", 
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", 
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

VEDIC_STARS = {
    "Rohini (Aldebaran)": Star(ra_hours=(4, 35, 55.2), dec_degrees=(16, 30, 33)),
    "Chitra (Spica)": Star(ra_hours=(13, 25, 11.5), dec_degrees=(-11, 9, 41)),
    "Swati (Arcturus)": Star(ra_hours=(14, 15, 39.6), dec_degrees=(19, 10, 56)),
    "Krittika (Pleiades)": Star(ra_hours=(3, 47, 24.0), dec_degrees=(24, 7, 0)),
    "Ardra (Betelgeuse)": Star(ra_hours=(5, 55, 10.3), dec_degrees=(7, 24, 25)),
    "Agastya (Canopus)": Star(ra_hours=(6, 23, 57.1), dec_degrees=(-52, 41, 44)),
    "SaptaRishi-Kratu (Dubhe)": Star(ra_hours=(11, 3, 43.6), dec_degrees=(61, 45, 3)),
    "SaptaRishi-Marichi (Alkaid)": Star(ra_hours=(13, 47, 32.4), dec_degrees=(49, 18, 47))
}

def to_scalar(val):
    """Permanently squashes ValueError arrays into pure standalone floats"""
    if hasattr(val, '__len__') or isinstance(val, (np.ndarray, list)):
        return float(val[0])
    return float(val)

def get_lahiri_ayanamsa(t):
    j2000 = 2451545.0
    days = t.tt - j2000
    return 23.85 + (days / 365.25) * (50.29 / 3600.0)

def get_sidereal_lon(observer, body, t):
    apparent = observer.at(t).observe(body).apparent()
    lat, lon, dist = apparent.frame_latlon(ecliptic_frame)
    return (to_scalar(lon.degrees) - get_lahiri_ayanamsa(t)) % 360

def get_rasi_name(lon_degrees):
    return RASI_NAMES[int(lon_degrees // 30)]

def get_nakshatra_name(lon_degrees):
    nakshatra_index = int(lon_degrees // (360.0 / 27.0))
    return NAKSHATRA_NAMES[nakshatra_index]


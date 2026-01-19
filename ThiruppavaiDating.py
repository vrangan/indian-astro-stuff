#!/usr/bin/env python3
"""
Thiruppavai Dating System - Astronomical Event Detector
========================================================
Uses Vedic/Jyotish astronomy to identify celestial events described in ancient Indian texts.
Implements precise sidereal calculations with Lahiri Ayanamsa, Nakshatra positioning, and Tithi calculations.

Usage:
    python ThiruppavaiDating.py [OPTIONS]
    
Examples:
    python ThiruppavaiDating.py --help
    python ThiruppavaiDating.py --year-range -6000 -5990 --location Ujjain
    python ThiruppavaiDating.py --visualize --chart-style south_indian
    python ThiruppavaiDating.py --location Srirangam --tithi 14 --vj-only
"""

import time
from multiprocessing import Pool, cpu_count, freeze_support
from skyfield.api import load, wgs84, Star, Angle
from skyfield import almanac
from skyfield.elementslib import osculating_elements_of
from skyfield.framelib import ecliptic_frame
from skyfield.jpllib import SpiceKernel
import numpy as np
import os
import sys
import json
import argparse
import csv
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Tuple, Optional

# Optional geocoding support
try:
    from geopy.geocoders import Nominatim
    HAS_GEOPY = True
except ImportError:
    HAS_GEOPY = False

# --- EPHEMERIS FILES ---
FILE_BC = 'de441_part-1.bsp'
FILE_AD = 'de441_part-2.bsp'

# --- LOCATION DATABASE ---
LOCATIONS_CSV = 'locations.csv'

# --- OBSERVER LOCATION CONFIGURATIONS ---
LOCATIONS = {
    'Ujjain': {'lat': 23.1765, 'lon': 75.0, 'name': 'Ujjain (Ancient Astronomical Center)'},
    'Srivilliputur': {'lat': 9.5236, 'lon': 77.9572, 'name': 'Srivilliputur, Tamil Nadu'},
    'Srirangam': {'lat': 10.8665, 'lon': 78.6867, 'name': 'Srirangam, Tamil Nadu'},
    'Cuddalore': {'lat': 11.7445, 'lon': 79.7645, 'name': 'Cuddalore, Tamil Nadu'},
    'Chennai': {'lat': 13.0827, 'lon': 80.2707, 'name': 'Chennai, Tamil Nadu'}
}

# Active location (can be changed)
ACTIVE_LOCATION = 'Srivilliputur'
LOCATION_LAT = LOCATIONS[ACTIVE_LOCATION]['lat']
LOCATION_LON = LOCATIONS[ACTIVE_LOCATION]['lon']

# --- PROCESSING CONFIGURATION ---
START_YEAR = -6000 
END_YEAR = 2100
CHUNK_SIZE_YEARS = 20

# --- VEDIC CONSTANTS ---

# 27 Lunar Mansions (Nakshatras) - starting from Ashwini at 0°
# Each nakshatra spans 13°20' (40/3 degrees)
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashirsha", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# Nakshatra rulers (Adhipati) in Vedic astrology
NAKSHATRA_RULERS = {
    'Ashwini': 'Ketu', 'Bharani': 'Venus', 'Krittika': 'Sun',
    'Rohini': 'Moon', 'Mrigashirsha': 'Mars', 'Ardra': 'Rahu',
    'Punarvasu': 'Jupiter', 'Pushya': 'Saturn', 'Ashlesha': 'Mercury',
    'Magha': 'Ketu', 'Purva Phalguni': 'Venus', 'Uttara Phalguni': 'Sun',
    'Hasta': 'Moon', 'Chitra': 'Mars', 'Swati': 'Rahu',
    'Vishakha': 'Jupiter', 'Anuradha': 'Saturn', 'Jyeshtha': 'Mercury',
    'Mula': 'Ketu', 'Purva Ashadha': 'Venus', 'Uttara Ashadha': 'Sun',
    'Shravana': 'Moon', 'Dhanishta': 'Mars', 'Shatabhisha': 'Rahu',
    'Purva Bhadrapada': 'Jupiter', 'Uttara Bhadrapada': 'Saturn', 'Revati': 'Mercury'
}

# 12 Zodiacal Signs (Rasis) - 30° each
RASIS = [
    "Mesha (Ar)", "Vrishabha (Ta)", "Mithuna (Ge)", "Karka (Cn)",
    "Simha (Le)", "Kanya (Vi)", "Tula (Li)", "Vrishchika (Sc)",
    "Dhanu (Sg)", "Makara (Cp)", "Kumbha (Aq)", "Meena (Pi)"
]

# Tithi (Lunar Day) thresholds - 30 tithis in a lunar month
# Tithi = (Moon Longitude - Sun Longitude) / 12
# 0-12° = Shukla Paksha 1, 12-24° = Shukla Paksha 2, etc.
TITHIS = [
    "Shukla Paksha Pratipadha", "Shukla Paksha Dwitiya", "Shukla Paksha Tritiya",
    "Shukla Paksha Chaturthi", "Shukla Paksha Panchami", "Shukla Paksha Shashthi",
    "Shukla Paksha Saptami", "Shukla Paksha Ashtami", "Shukla Paksha Navami",
    "Shukla Paksha Dashami", "Shukla Paksha Ekadashi", "Shukla Paksha Dwadashi",
    "Shukla Paksha Trayodashi", "Shukla Paksha Chaturdashi", "Purnima (Full Moon)",
    "Krishna Paksha Pratipadha", "Krishna Paksha Dwitiya", "Krishna Paksha Tritiya",
    "Krishna Paksha Chaturthi", "Krishna Paksha Panchami", "Krishna Paksha Shashthi",
    "Krishna Paksha Saptami", "Krishna Paksha Ashtami", "Krishna Paksha Navami",
    "Krishna Paksha Dashami", "Krishna Paksha Ekadashi", "Krishna Paksha Dwadashi",
    "Krishna Paksha Trayodashi", "Krishna Paksha Chaturdashi", "Amavasya (New Moon)"
]

# Planetary aspects (Graha Drishti) - degrees from planet
PLANETARY_ASPECTS = {
    'Sun': [30, 60, 90, 120, 150, 180],      # Sun aspects 30, 60, 90, 120, 150, 180
    'Moon': [30, 60, 90, 120, 150, 180],     # Moon aspects 30, 60, 90, 120, 150, 180
    'Mars': [30, 60, 90, 120, 150, 180],     # Mars special aspects 4, 7, 8
    'Mercury': [30, 60, 90, 120, 150, 180],  
    'Jupiter': [30, 60, 90, 120, 150, 180],  # Jupiter special aspects 5, 7, 9
    'Venus': [30, 60, 90, 120, 150, 180],    
    'Saturn': [30, 60, 90, 120, 150, 180]    # Saturn special aspects 3, 7, 10
}

# --- SEARCH CONFIGURATION ---
@dataclass
class SearchConfig:
    """
    Configurable search criteria for astronomical events.
    Allows flexible event definition without code changes.
    """
    # Sun position constraints
    sun_rasi: Optional[int] = None  # 0-11 (Mesha to Meena), None = any
    sun_rasi_range: Tuple[float, float] = (270.0, 300.0)  # Degree range for Makara
    
    # Moon phase constraints
    target_tithi: Optional[int] = None  # 14 = Purnima (Full Moon), 29 = Amavasya (New Moon), None = any
    tithi_window: int = 1  # +/- tithis to consider
    
    # Nakshatra constraints
    target_nakshatras: List[int] = field(default_factory=list)  # Indices into NAKSHATRAS, empty = any
    
    # Planetary aspect constraints
    require_vj_alignment: bool = True  # Venus-Jupiter proximity
    vj_tolerance_degrees: float = 5.0  # Degrees between Venus and Jupiter
    vj_altitude_above_horizon: float = 0.0  # Minimum altitude for both planets
    include_rahu_ketu: bool = True  # Include lunar nodes (Rahu/Ketu)
    
    # Rahu/Ketu constraints
    target_rahu_nakshatras: List[int] = field(default_factory=list)  # Indices for Rahu nakshatra
    target_ketu_nakshatras: List[int] = field(default_factory=list)  # Indices for Ketu nakshatra
    
    # Individual planet constraints (rasi filtering)
    target_mars_rasi: Optional[int] = None  # 0-11, None = any
    target_mercury_rasi: Optional[int] = None
    target_jupiter_rasi: Optional[int] = None
    target_venus_rasi: Optional[int] = None
    target_saturn_rasi: Optional[int] = None
    
    # Additional planetary constraints
    required_aspects: Dict[str, List[str]] = field(default_factory=dict)  # e.g., {'Jupiter': ['Sun', 'Venus']}
    excluded_aspects: Dict[str, List[str]] = field(default_factory=dict)
    
    # Search window
    offset_window_days: int = 15  # Skip N days after finding a match to avoid duplicates
    
    def to_dict(self) -> Dict:
        """Convert config to dictionary for logging"""
        return {
            'sun_rasi_range': self.sun_rasi_range,
            'target_tithi': self.target_tithi,
            'tithi_window': self.tithi_window,
            'target_nakshatras': [NAKSHATRAS[i] if i < len(NAKSHATRAS) else f'Index {i}' 
                                   for i in self.target_nakshatras],
            'require_vj_alignment': self.require_vj_alignment,
            'vj_tolerance_degrees': self.vj_tolerance_degrees,
            'vj_altitude_above_horizon': self.vj_altitude_above_horizon,
            'offset_window_days': self.offset_window_days
        }


# Default search configuration for Thiruppavai events
DEFAULT_CONFIG = SearchConfig(
    sun_rasi_range=(270.0, 300.0),  # Sun in Makara
    target_tithi=14,  # Full Moon (Purnima)
    tithi_window=1,  # +/- 1 tithi
    require_vj_alignment=True,
    vj_tolerance_degrees=5.0,
    vj_altitude_above_horizon=0.0,
    offset_window_days=15
)

# --- CALCULATION HELPER FUNCTIONS ---

def get_lahiri_ayanamsa(t) -> float:
    """
    Calculate Lahiri Ayanamsa (precession correction) at given time.
    Converts tropical zodiac to sidereal zodiac as used in Vedic astrology.
    
    The Lahiri Ayanamsa places Aries at 0° aligned with Ashwini nakshatra start.
    Formula uses rate of 50.27 arcseconds per year from 2000.0 (JD 2451545.0)
    
    Args:
        t: Skyfield Time object
    Returns:
        float: Ayanamsa in degrees (to be subtracted from tropical coordinates)
    """
    days_since_j2000 = t.tt - 2451545.0
    ayanamsa_arcsec = 23857.0 + (days_since_j2000 * 50.27)  # Lahiri formula
    return ayanamsa_arcsec / 3600.0  # Convert arcseconds to degrees


def get_nakshatra_info(longitude_deg: float) -> Tuple[str, int, float, float]:
    """
    Determine nakshatra from ecliptic longitude.
    
    Nakshatras are 27 equal divisions of the zodiac, each 13°20' (13.333°)
    Ashwini starts at 0°, Revati ends at 360°
    
    Args:
        longitude_deg: Sidereal ecliptic longitude (0-360)
    Returns:
        Tuple of (nakshatra_name, nakshatra_index, start_degree, end_degree)
    """
    normalized_lon = longitude_deg % 360.0
    nakshatra_size = 360.0 / 27  # 13.333° per nakshatra
    nakshatra_idx = int(normalized_lon / nakshatra_size)
    
    start_deg = nakshatra_idx * nakshatra_size
    end_deg = start_deg + nakshatra_size
    
    return NAKSHATRAS[nakshatra_idx], nakshatra_idx, start_deg, end_deg


def get_tithi_info(moon_lon: float, sun_lon: float) -> Tuple[str, int, float, float]:
    """
    Calculate Tithi (lunar day) from Moon-Sun angular separation.
    
    Tithi is the angular separation between Moon and Sun divided into 30 equal parts.
    - 0°-12° = Tithi 1 (Shukla Pratipadha / Waxing 1st)
    - 12°-24° = Tithi 2, etc.
    - 348°-360° = Tithi 30 (Amavasya / New Moon)
    
    Args:
        moon_lon: Sidereal Moon longitude (0-360)
        sun_lon: Sidereal Sun longitude (0-360)
    Returns:
        Tuple of (tithi_name, tithi_index, separation_angle, tithi_progress_percent)
    """
    # Calculate angular separation (Moon ahead of Sun)
    separation = (moon_lon - sun_lon) % 360.0
    
    tithi_size = 360.0 / 30  # 12° per tithi
    tithi_idx = int(separation / tithi_size)
    
    tithi_start = tithi_idx * tithi_size
    tithi_end = tithi_start + tithi_size
    
    # Progress within current tithi (0-100%)
    progress = ((separation - tithi_start) / tithi_size) * 100
    
    return TITHIS[tithi_idx], tithi_idx, separation, progress


# --- LOCATION MANAGEMENT FUNCTIONS ---

def load_locations_from_csv() -> Dict[str, Dict]:
    """Load locations from CSV file and merge with predefined locations."""
    locations = LOCATIONS.copy()
    
    if os.path.exists(LOCATIONS_CSV):
        try:
            with open(LOCATIONS_CSV, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['name']:
                        locations[row['name']] = {
                            'lat': float(row['latitude']),
                            'lon': float(row['longitude']),
                            'name': row.get('full_name', row['name'])
                        }
        except Exception as e:
            print(f"Warning: Could not read locations.csv: {e}", file=sys.stderr)
    
    return locations


def save_location_to_csv(name: str, latitude: float, longitude: float, full_name: str = None):
    """Save a new location to the CSV database."""
    if full_name is None:
        full_name = name
    
    # Check if location already exists
    locations = {}
    if os.path.exists(LOCATIONS_CSV):
        try:
            with open(LOCATIONS_CSV, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    locations[row['name']] = row
        except Exception as e:
            print(f"Warning: Could not read existing locations.csv: {e}", file=sys.stderr)
    
    # Update or add location
    locations[name] = {
        'name': name,
        'latitude': latitude,
        'longitude': longitude,
        'full_name': full_name
    }
    
    # Write back to CSV
    try:
        with open(LOCATIONS_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'latitude', 'longitude', 'full_name'])
            writer.writeheader()
            for loc_name, loc_data in sorted(locations.items()):
                writer.writerow(loc_data)
        print(f"✓ Location '{name}' saved to {LOCATIONS_CSV}")
    except Exception as e:
        print(f"✗ Error writing to {LOCATIONS_CSV}: {e}", file=sys.stderr)
        sys.exit(1)


def geocode_location(location_name: str) -> Optional[Tuple[float, float]]:
    """
    Attempt to geocode a location name to (latitude, longitude) coordinates.
    Uses geopy if available, otherwise requires manual entry.
    """
    if HAS_GEOPY:
        try:
            print(f"Geocoding '{location_name}'...", file=sys.stderr)
            geolocator = Nominatim(user_agent="thiruppavai_dating")
            location = geolocator.geocode(location_name)
            if location:
                print(f"✓ Found: {location.address}", file=sys.stderr)
                return location.latitude, location.longitude
            else:
                print(f"✗ Location not found: {location_name}", file=sys.stderr)
                return None
        except Exception as e:
            print(f"✗ Geocoding error: {e}", file=sys.stderr)
            return None
    else:
        print("\nGeopy not installed. To auto-geocode, install: pip install geopy", file=sys.stderr)
        print("For now, please provide coordinates manually:", file=sys.stderr)
        try:
            lat = float(input("  Latitude (degrees): "))
            lon = float(input("  Longitude (degrees): "))
            return lat, lon
        except ValueError:
            print("✗ Invalid coordinates", file=sys.stderr)
            return None


def mean_lunar_ascending_node_longitude_deg(t) -> float:
        """
        Compute mean longitude of the Moon's ascending node (Ω) in tropical degrees.
        Formula per Meeus (Astronomical Algorithms), high-level approximation:
            Ω = 125.04452° - 1934.136261°·T + 0.0020708°·T^2 + T^3/450000
        where T is Julian centuries since J2000.0 in TT.
        """
        T = (t.tt - 2451545.0) / 36525.0
        omega = 125.04452 - 1934.136261 * T + 0.0020708 * (T ** 2) + (T ** 3) / 450000.0
        return omega % 360.0


def calculate_lagna(t, latitude: float, longitude: float) -> Tuple[float, str, int]:
    """
    Calculate Lagna (Ascendant) - the zodiacal sign rising on the eastern horizon.
    
    This is a simplified calculation using local sidereal time.
    For precise Lagna calculation, use more sophisticated methods considering
    obliquity of ecliptic, latitude corrections, and house systems.
    
    Args:
        t: Skyfield Time object
        latitude: Observer latitude in degrees
        longitude: Observer longitude in degrees
    
    Returns:
        Tuple of (lagna_longitude_sidereal, lagna_rasi_name, lagna_rasi_index)
    """
    # Get Greenwich Sidereal Time (GST) in degrees
    # Skyfield's gmst returns hour angle; convert to degrees
    gst_hours = t.gast  # Greenwich Apparent Sidereal Time
    gst_deg = (gst_hours * 15.0) % 360.0  # Convert hours to degrees
    
    # Calculate Local Sidereal Time (LST)
    lst_deg = (gst_deg + longitude) % 360.0
    
    # Apply ayanamsa to get sidereal Lagna
    ayan = get_lahiri_ayanamsa(t)
    lagna_lon_sid = (lst_deg - ayan) % 360.0
    
    # Determine Lagna rasi
    lagna_rasi_name, lagna_rasi_idx, _, _ = get_rasi_info(lagna_lon_sid)
    
    return lagna_lon_sid, lagna_rasi_name, lagna_rasi_idx


def get_rasi_info(longitude_deg: float) -> Tuple[str, int, float, float]:
    """
    Convert a sidereal longitude to rasi (zodiac sign) information.
    
    Args:
        longitude_deg: Sidereal longitude in degrees (0-360)
    
    Returns:
        Tuple of (rasi_name, rasi_index, start_degree, end_degree)
    """
    normalized_lon = longitude_deg % 360.0
    rasi_idx = int(normalized_lon / 30.0)
    
    start_deg = rasi_idx * 30.0
    end_deg = start_deg + 30.0
    
    degree_in_rasi = normalized_lon - start_deg
    
    return RASIS[rasi_idx], rasi_idx, start_deg, degree_in_rasi


def calculate_planetary_aspects(planet_lon: float, other_planets: Dict[str, float], 
                               tolerance_deg: float = 3.0) -> Dict[str, List[str]]:
    """
    Check planetary aspects (Drishti) - when planets influence each other.
    
    Vedic aspects follow specific angular relationships:
    - Conjunction (0 deg), Opposition (180 deg), Trine (120 deg), Square (90 deg), etc.
    
    Args:
        planet_lon: Longitude of the observing planet
        other_planets: Dict of other planets and their longitudes
        tolerance_deg: Aspect orb (allowable deviation in degrees)
    Returns:
        Dict with aspect types as keys and list of aspected planets as values
    """
    aspects = {
        'conjunction': [],
        'opposition': [],
        'trine': [],
        'square': [],
        'sextile': []
    }
    
    for other_name, other_lon in other_planets.items():
        diff = (other_lon - planet_lon) % 360.0
        if diff > 180.0:
            diff = 360.0 - diff
        
        # Check aspect types
        if abs(diff - 0.0) <= tolerance_deg or abs(diff - 360.0) <= tolerance_deg:
            aspects['conjunction'].append(other_name)
        elif abs(diff - 180.0) <= tolerance_deg:
            aspects['opposition'].append(other_name)
        elif abs(diff - 120.0) <= tolerance_deg:
            aspects['trine'].append(other_name)
        elif abs(diff - 90.0) <= tolerance_deg:
            aspects['square'].append(other_name)
        elif abs(diff - 60.0) <= tolerance_deg:
            aspects['sextile'].append(other_name)
    
    return aspects


def calculate_yogas(planets_data: Dict[str, Dict]) -> List[str]:
    """
    Identify significant Yogas (auspicious or notable planetary combinations).
    
    Yogas are specific configurations with special significance in Jyotish.
    This is a simplified implementation of common yogas.
    
    Args:
        planets_data: Dict with planet names and their position data
    Returns:
        List of identified yogas
    """
    yogas = []
    
    # Raja Yoga: Conjunction of Jupiter and Venus
    if 'Venus' in planets_data and 'Jupiter' in planets_data:
        diff = abs(planets_data['Venus']['longitude'] - planets_data['Jupiter']['longitude'])
        if diff < 10.0 or diff > 350.0:
            yogas.append('Mahalakshmi Yoga (Jupiter-Venus conjunction)')
    
    # Neecha Bhanga: Planet in debilitation but aspect by friendly planet
    # (Simplified - would need full dignity calculation)
    
    # Parivartana: Two planets exchange Rasis
    for p1_name in planets_data:
        for p2_name in planets_data:
            if p1_name != p2_name:
                p1_rasi = get_rasi_info(planets_data[p1_name]['longitude'])[1]
                p2_rasi = get_rasi_info(planets_data[p2_name]['longitude'])[1]
                # Check if planets are in each other's rulership (simplified)
    
    return yogas


# --- THE SCANNER LOGIC ---
def process_chunk_jyotish(args):
    """
    Scan a time range for astronomical events matching the search configuration.
    
    This is the main scanning engine. It:
    1. Loads ephemeris data (DE441 SPICE kernels for precise positions)
    2. Iterates through each day in the range
    3. Calculates sidereal positions for all planets using Lahiri Ayanamsa
    4. Evaluates search criteria (nakshatras, tithis, aspects, etc.)
    5. Accumulates matching events
    
    Args:
        args: Tuple of (year_start, year_end, search_config)
    Returns:
        List of matching event dictionaries
    """
    year_start, year_end, config = args
    
    try:
        # --- LOAD EPHEMERIS ---
        # DE441 is split into two files for BC and AD dates
        current_eph_file = None
        if year_end <= 0:
            current_eph_file = FILE_BC
        elif year_start >= 0:
            current_eph_file = FILE_AD
        else:
            # Span crosses year 0 - need both ephemerides
            if os.path.exists(FILE_BC) and os.path.exists(FILE_AD):
                eph_bc = load(FILE_BC)
                eph_ad = load(FILE_AD)
                eph_bc.segments.extend(eph_ad.segments)
                eph = eph_bc
                current_eph_file = "MERGED"
            else:
                return [("ERROR", "Missing ephemeris files")]

        if current_eph_file != "MERGED":
            if not os.path.exists(current_eph_file):
                return [("ERROR", f"Missing {current_eph_file}")]
            eph = load(current_eph_file)
        
        local_results = []
        if year_start >= year_end:
            return []

        ts = load.timescale()
        
        # --- LOAD SOLAR SYSTEM BODIES ---
        sun = eph['sun']
        moon = eph['moon']
        venus = eph['venus']
        jupiter = eph['jupiter barycenter']
        mars = eph['mars barycenter']
        mercury = eph['mercury barycenter']
        saturn = eph['saturn barycenter']
        earth = eph[399]
        
        # --- DEFINE OBSERVER LOCATION ---
        observer_loc = wgs84.latlon(LOCATION_LAT, LOCATION_LON)

        def get_sidereal_positions(t):
            """
            Calculate sidereal positions for all planets at time t.
            
            Sidereal = Tropical - Ayanamsa (precession correction)
            Uses Lahiri Ayanamsa which aligns Aries with Ashwini nakshatra.
            
            Args:
                t: Skyfield Time object
            Returns:
                Dict with planet names and their sidereal longitudes (0-360)
            """
            ayan = get_lahiri_ayanamsa(t)
            
            # Calculate tropical longitudes using geocentric (earth-centered) observations
            def tropical_lon(body):
                _, lon, _ = earth.at(t).observe(body).apparent().ecliptic_latlon()
                return lon.degrees
            
            positions = {
                'Sun': (tropical_lon(sun) - ayan) % 360.0,
                'Moon': (tropical_lon(moon) - ayan) % 360.0,
                'Venus': (tropical_lon(venus) - ayan) % 360.0,
                'Jupiter': (tropical_lon(jupiter) - ayan) % 360.0,
                'Mars': (tropical_lon(mars) - ayan) % 360.0,
                'Mercury': (tropical_lon(mercury) - ayan) % 360.0,
                'Saturn': (tropical_lon(saturn) - ayan) % 360.0
            }

            # Add lunar nodes (Rahu/Ketu) using mean node model
            if config.include_rahu_ketu:
                omega = mean_lunar_ascending_node_longitude_deg(t)  # tropical
                rahu = (omega - ayan) % 360.0
                ketu = (rahu + 180.0) % 360.0
                positions['Rahu'] = rahu
                positions['Ketu'] = ketu

            return positions

        # --- MAIN SCAN LOOP ---
        curr_t = ts.utc(year_start, 1, 1)
        end_t_val = ts.utc(year_end, 1, 1).tt
        
        while curr_t.tt < end_t_val:
            try:
                # Get planetary positions
                positions = get_sidereal_positions(curr_t)
                
                # Check Sun constraint
                if not (config.sun_rasi_range[0] <= positions['Sun'] <= config.sun_rasi_range[1]):
                    curr_t = ts.tt_jd(curr_t.tt + 1)
                    continue
                
                # Check Tithi constraint
                tithi_name, tithi_idx, separation, tithi_progress = get_tithi_info(
                    positions['Moon'], positions['Sun']
                )
                
                if config.target_tithi is not None:
                    tithi_diff = abs(tithi_idx - config.target_tithi)
                    if tithi_diff > config.tithi_window and abs(tithi_diff - 30) > config.tithi_window:
                        curr_t = ts.tt_jd(curr_t.tt + 1)
                        continue
                
                # Check Nakshatra constraint
                moon_nak_name, moon_nak_idx, _, _ = get_nakshatra_info(positions['Moon'])
                
                if config.target_nakshatras:
                    if moon_nak_idx not in config.target_nakshatras:
                        curr_t = ts.tt_jd(curr_t.tt + 1)
                        continue
                
                # Check Rahu/Ketu Nakshatra constraints if specified
                if config.include_rahu_ketu:
                    if config.target_rahu_nakshatras:
                        rahu_nak_name, rahu_nak_idx, _, _ = get_nakshatra_info(positions['Rahu'])
                        if rahu_nak_idx not in config.target_rahu_nakshatras:
                            curr_t = ts.tt_jd(curr_t.tt + 1)
                            continue
                    
                    if config.target_ketu_nakshatras:
                        ketu_nak_name, ketu_nak_idx, _, _ = get_nakshatra_info(positions['Ketu'])
                        if ketu_nak_idx not in config.target_ketu_nakshatras:
                            curr_t = ts.tt_jd(curr_t.tt + 1)
                            continue
                
                # Check individual planet rasi constraints
                if config.target_mars_rasi is not None:
                    mars_rasi_idx = int(positions['Mars'] / 30.0)
                    if mars_rasi_idx != config.target_mars_rasi:
                        curr_t = ts.tt_jd(curr_t.tt + 1)
                        continue
                
                if config.target_mercury_rasi is not None:
                    mercury_rasi_idx = int(positions['Mercury'] / 30.0)
                    if mercury_rasi_idx != config.target_mercury_rasi:
                        curr_t = ts.tt_jd(curr_t.tt + 1)
                        continue
                
                if config.target_jupiter_rasi is not None:
                    jupiter_rasi_idx = int(positions['Jupiter'] / 30.0)
                    if jupiter_rasi_idx != config.target_jupiter_rasi:
                        curr_t = ts.tt_jd(curr_t.tt + 1)
                        continue
                
                if config.target_venus_rasi is not None:
                    venus_rasi_idx = int(positions['Venus'] / 30.0)
                    if venus_rasi_idx != config.target_venus_rasi:
                        curr_t = ts.tt_jd(curr_t.tt + 1)
                        continue
                
                if config.target_saturn_rasi is not None:
                    saturn_rasi_idx = int(positions['Saturn'] / 30.0)
                    if saturn_rasi_idx != config.target_saturn_rasi:
                        curr_t = ts.tt_jd(curr_t.tt + 1)
                        continue
                
                # Check Venus-Jupiter alignment if required
                if config.require_vj_alignment:
                    vj_diff = abs(positions['Venus'] - positions['Jupiter'])
                    vj_diff = min(vj_diff, 360.0 - vj_diff)
                    
                    if vj_diff > config.vj_tolerance_degrees:
                        curr_t = ts.tt_jd(curr_t.tt + 1)
                        continue
                    
                    # Check altitude if required
                    if config.vj_altitude_above_horizon > 0:
                        observer_topo = earth.at(curr_t) + observer_loc
                        
                        v_astrometric = observer_topo.observe(venus).apparent()
                        j_astrometric = observer_topo.observe(jupiter).apparent()
                        
                        v_alt = v_astrometric.apparent_latlon(observer_topo)[0].degrees
                        j_alt = j_astrometric.apparent_latlon(observer_topo)[0].degrees
                        
                        if v_alt < config.vj_altitude_above_horizon or j_alt < config.vj_altitude_above_horizon:
                            curr_t = ts.tt_jd(curr_t.tt + 1)
                            continue
                
                # If all criteria met, record the event
                y, m, d, _, _, _ = curr_t.utc
                
                # Format date
                if y < 0:
                    fmt_date = f"{abs(y)+1} BC-{m:02d}-{d:02d}"
                else:
                    fmt_date = f"{y} AD-{m:02d}-{d:02d}"
                
                # Get all positional data
                sun_nak, sun_nak_idx, _, _ = get_nakshatra_info(positions['Sun'])
                sun_rasi, sun_rasi_idx, _, sun_rasi_deg = get_rasi_info(positions['Sun'])
                moon_rasi, moon_rasi_idx, _, moon_rasi_deg = get_rasi_info(positions['Moon'])
                mars_rasi, mars_rasi_idx, _, _ = get_rasi_info(positions['Mars'])
                mercury_rasi, mercury_rasi_idx, _, _ = get_rasi_info(positions['Mercury'])
                venus_rasi, venus_rasi_idx, _, venus_rasi_deg = get_rasi_info(positions['Venus'])
                jupiter_rasi, jupiter_rasi_idx, _, jupiter_rasi_deg = get_rasi_info(positions['Jupiter'])
                saturn_rasi, saturn_rasi_idx, _, _ = get_rasi_info(positions['Saturn'])
                
                # Calculate Lagna (Ascendant)
                lagna_lon, lagna_rasi, lagna_rasi_idx = calculate_lagna(curr_t, LOCATION_LAT, LOCATION_LON)
                
                event_record = {
                    'Date': fmt_date,
                    'JD': round(curr_t.tt, 2),
                    'Lagna_Longitude': round(lagna_lon, 2),
                    'Lagna_Rasi': lagna_rasi,
                    'Sun_Longitude': round(positions['Sun'], 2),
                    'Sun_Rasi': sun_rasi,
                    'Sun_Nakshatra': sun_nak,
                    'Moon_Longitude': round(positions['Moon'], 2),
                    'Moon_Rasi': moon_rasi,
                    'Moon_Nakshatra': moon_nak_name,
                    'Tithi': tithi_name,
                    'Tithi_Index': tithi_idx,
                    'Tithi_Progress': round(tithi_progress, 1),
                    'Venus_Longitude': round(positions['Venus'], 2),
                    'Venus_Rasi': venus_rasi,
                    'Jupiter_Longitude': round(positions['Jupiter'], 2),
                    'Jupiter_Rasi': jupiter_rasi,
                    'VJ_Separation': round(vj_diff if config.require_vj_alignment else 0, 2),
                    'Mars_Longitude': round(positions['Mars'], 2),
                    'Mars_Rasi': mars_rasi,
                    'Mercury_Longitude': round(positions['Mercury'], 2),
                    'Mercury_Rasi': mercury_rasi,
                    'Saturn_Longitude': round(positions['Saturn'], 2),
                    'Saturn_Rasi': saturn_rasi
                }

                # Optional Rahu/Ketu columns
                if 'Rahu' in positions and 'Ketu' in positions:
                    rahu_rasi, _, _, _ = get_rasi_info(positions['Rahu'])
                    ketu_rasi, _, _, _ = get_rasi_info(positions['Ketu'])
                    event_record['Rahu_Longitude'] = round(positions['Rahu'], 2)
                    event_record['Rahu_Rasi'] = rahu_rasi
                    event_record['Ketu_Longitude'] = round(positions['Ketu'], 2)
                    event_record['Ketu_Rasi'] = ketu_rasi
                
                local_results.append(event_record)
                
                # Skip ahead to avoid duplicate matches
                curr_t = ts.tt_jd(curr_t.tt + config.offset_window_days)
                
            except Exception as e:
                # Continue on individual day errors
                curr_t = ts.tt_jd(curr_t.tt + 1)
                continue
        
        return local_results
        
    except Exception as e:
        return [("ERROR", str(e))]



def deduplicate(events):
    """
    Remove duplicate events that occur on same date.
    
    Args:
        events: List of event dictionaries
    Returns:
        List of unique events by date
    """
    if not events:
        return []
    events.sort(key=lambda x: x.get("Date", ""))
    unique = {e['Date']: e for e in events if isinstance(e, dict)}
    return list(unique.values())


# --- COMMAND-LINE INTERFACE ---

def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create comprehensive command-line argument parser.
    
    Returns:
        ArgumentParser with all supported options
    """
    parser = argparse.ArgumentParser(
        description="Thiruppavai Dating System - Astronomical Event Detector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ThiruppavaiDating.py
                          # Run with default settings
  python ThiruppavaiDating.py --year-range -6000 -5990 --location Ujjain
                          # Scan 10 years from Ujjain
  python ThiruppavaiDating.py --visualize --chart-style south_indian
                          # Generate visualizations and horoscopes
  python ThiruppavaiDating.py --tithi 14 --vj-only
                          # Full Moon only, Venus-Jupiter required
  python ThiruppavaiDating.py --list-locations
                          # Show available observer locations
        """
    )
    
    # Date range arguments
    date_group = parser.add_argument_group('Date Range')
    date_group.add_argument('--year-range', type=int, nargs=2, metavar=('START', 'END'),
                           default=[START_YEAR, START_YEAR + 10],
                           help=f"Year range to scan (default: {START_YEAR} to {START_YEAR+10})")
    date_group.add_argument('--chunk-size', type=int, default=CHUNK_SIZE_YEARS,
                           help=f"Process chunk size in years (default: {CHUNK_SIZE_YEARS})")
    
    # Location arguments
    location_group = parser.add_argument_group('Observer Location')
    # Dynamically load locations from CSV
    available_locations = load_locations_from_csv()
    location_group.add_argument('--location', type=str, default=ACTIVE_LOCATION,
                               choices=list(available_locations.keys()),
                               help=f"Observer location (default: {ACTIVE_LOCATION})")
    location_group.add_argument('--latitude', type=float, metavar='LAT',
                               help="Custom latitude (overrides --location)")
    location_group.add_argument('--longitude', type=float, metavar='LON',
                               help="Custom longitude (overrides --location)")
    location_group.add_argument('--list-locations', action='store_true',
                               help="List available locations and exit")
    location_group.add_argument('--add-location', type=str, metavar='NAME',
                               help="Add a new location (will prompt for latitude/longitude or geocode automatically)")
    location_group.add_argument('--add-lat', type=float, metavar='LAT',
                               help="Latitude for new location (used with --add-location)")
    location_group.add_argument('--add-lon', type=float, metavar='LON',
                               help="Longitude for new location (used with --add-location)")
    
    # Sun position arguments
    sun_group = parser.add_argument_group('Sun Position Criteria')
    sun_group.add_argument('--sun-rasi-range', type=float, nargs=2, metavar=('START', 'END'),
                          default=[270.0, 300.0],
                          help="Sun longitude range in degrees (default: 270-300 = Makara)")
    sun_group.add_argument('--any-sun-rasi', action='store_true',
                          help="Match any Sun position (ignore rasi range)")
    
    # Moon phase arguments
    moon_group = parser.add_argument_group('Moon Phase Criteria')
    moon_group.add_argument('--tithi', type=int, metavar='TITHI',
                           default=14,
                           help="Target lunar day 0-29 (14=Full Moon, 29=New Moon, default: 14)")
    moon_group.add_argument('--tithi-window', type=int, default=1,
                           help="Tithi tolerance +/- days (default: 1)")
    moon_group.add_argument('--any-tithi', action='store_true',
                           help="Match any lunar day")
    
    # Nakshatra arguments
    nak_group = parser.add_argument_group('Nakshatra Criteria')
    nak_group.add_argument('--nakshatras', type=int, nargs='+', metavar='INDEX',
                          help="Nakshatra indices (0-26), e.g. 0 1 2 for Ashwini, Bharani, Krittika")
    nak_group.add_argument('--any-nakshatra', action='store_true',
                          help="Match any nakshatra")
    nak_group.add_argument('--rahu-nakshatras', type=int, nargs='+', metavar='INDEX',
                          help="Rahu nakshatra indices (0-26)")
    nak_group.add_argument('--ketu-nakshatras', type=int, nargs='+', metavar='INDEX',
                          help="Ketu nakshatra indices (0-26)")
    
    # Planetary aspect arguments
    aspect_group = parser.add_argument_group('Planetary Aspects')
    aspect_group.add_argument('--vj-only', action='store_true', default=True,
                             help="Require Venus-Jupiter alignment (default: True)")
    aspect_group.add_argument('--no-vj', action='store_true',
                             help="Disable Venus-Jupiter requirement")
    aspect_group.add_argument('--vj-tolerance', type=float, default=5.0,
                             help="Venus-Jupiter max separation in degrees (default: 5.0)")
    aspect_group.add_argument('--vj-altitude', type=float, default=0.0,
                             help="Minimum altitude above horizon for both planets (default: 0.0)")
    
    # Individual planet position arguments
    planet_group = parser.add_argument_group('Individual Planet Positions')
    planet_group.add_argument('--mars-rasi', type=int, metavar='RASI_IDX',
                             help="Require Mars in specific rasi (0-11, e.g. 0=Aries)")
    planet_group.add_argument('--mercury-rasi', type=int, metavar='RASI_IDX',
                             help="Require Mercury in specific rasi (0-11)")
    planet_group.add_argument('--jupiter-rasi', type=int, metavar='RASI_IDX',
                             help="Require Jupiter in specific rasi (0-11)")
    planet_group.add_argument('--venus-rasi', type=int, metavar='RASI_IDX',
                             help="Require Venus in specific rasi (0-11)")
    planet_group.add_argument('--saturn-rasi', type=int, metavar='RASI_IDX',
                             help="Require Saturn in specific rasi (0-11)")
    
    # Output arguments
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument('--output', type=str, metavar='FILE',
                             help="Output CSV filename (default: results_<range>_enhanced.csv)")
    output_group.add_argument('--visualize', action='store_true',
                             help="Generate zodiacal wheel visualizations")
    output_group.add_argument('--num-visualizations', type=int, default=5,
                             help="Number of events to visualize (default: 5)")
    output_group.add_argument('--chart-style', type=str, choices=['south_indian', 'north_indian'],
                             default='south_indian',
                             help="Horoscope chart style (default: south_indian)")
    output_group.add_argument('--generate-horoscopes', action='store_true',
                             help="Generate horoscope charts for events")
    
    # Processing arguments
    proc_group = parser.add_argument_group('Processing Options')
    proc_group.add_argument('--offset-window', type=int, default=15,
                           help="Days to skip after finding a match (default: 15)")
    proc_group.add_argument('--cores', type=int, default=cpu_count(),
                           help=f"Number of CPU cores to use (default: {cpu_count()})")
    proc_group.add_argument('--verbose', '-v', action='store_true',
                           help="Verbose output")
    proc_group.add_argument('--quiet', '-q', action='store_true',
                           help="Minimal output")
    
    # Utility arguments
    util_group = parser.add_argument_group('Utility Options')
    util_group.add_argument('--save-config', type=str, metavar='FILE',
                           help="Save current configuration to JSON file")
    util_group.add_argument('--load-config', type=str, metavar='FILE',
                           help="Load configuration from JSON file")

    # Horoscope reading arguments
    reading_group = parser.add_argument_group('Horoscope Reading')
    reading_group.add_argument('--read-horoscope', action='store_true',
                               help="Generate an introductory horoscope reading and exit")
    reading_group.add_argument('--birth-dt', type=str, metavar='ISO_DATETIME',
                               help="Birth date/time, e.g. 1990-01-01T12:34:00 (local time)")
    reading_group.add_argument('--birth-lat', type=float, metavar='LAT',
                               help="Birth latitude in decimal degrees")
    reading_group.add_argument('--birth-lon', type=float, metavar='LON',
                               help="Birth longitude in decimal degrees")
    reading_group.add_argument('--birth-tz', type=str, default='UTC', metavar='IANA_TZ',
                               help="Timezone for birth datetime (default: UTC), e.g. Asia/Kolkata")
    reading_group.add_argument('--birth-chart', action='store_true',
                               help="Generate birth chart visualization along with reading")
    
    return parser


def parse_arguments(argv: Optional[List[str]] = None):
    """
    Parse and process command-line arguments.

    Args:
        argv: Optional list of argument strings to parse instead of sys.argv.
              When None, parses from sys.argv[1:].

    Returns:
        Tuple: (args, config, settings, location_lat, location_lon, location_name)
    """
    parser = create_argument_parser()
    provided_args = argv if argv is not None else sys.argv[1:]
    args = parser.parse_args(provided_args)
    
    # Handle --add-location
    if args.add_location:
        location_name = args.add_location
        
        # Check if location already exists
        available_locations = load_locations_from_csv()
        if location_name in available_locations:
            print(f"✗ Location '{location_name}' already exists", file=sys.stderr)
            sys.exit(1)
        
        # Get coordinates
        if args.add_lat is not None and args.add_lon is not None:
            latitude, longitude = args.add_lat, args.add_lon
        else:
            # Try geocoding
            coords = geocode_location(location_name)
            if coords is None:
                print(f"✗ Could not determine coordinates for '{location_name}'", file=sys.stderr)
                sys.exit(1)
            latitude, longitude = coords
        
        # Save to CSV
        save_location_to_csv(location_name, latitude, longitude, location_name)
        sys.exit(0)
    
    # Handle --list-locations
    if args.list_locations:
        available_locations = load_locations_from_csv()
        print("\nAvailable Observer Locations:")
        print("=" * 75)
        print(f"{'Name':<20} {'Description':<30} {'Latitude':<12} {'Longitude':<12}")
        print("-" * 75)
        for key, loc in sorted(available_locations.items()):
            print(f"  {key:<18} {loc['name']:<28} {loc['lat']:<11.4f}° {loc['lon']:<11.4f}°")
        print("=" * 75)
        print(f"\nTo add a new location: --add-location NAME [--add-lat LAT --add-lon LON]")
        print(f"CSV database location: {LOCATIONS_CSV}")
        sys.exit(0)
    
    # Determine location
    available_locations = load_locations_from_csv()
    if args.latitude is not None and args.longitude is not None:
        location_lat = args.latitude
        location_lon = args.longitude
        location_name = f"Custom ({args.latitude:.4f}°, {args.longitude:.4f}°)"
    else:
        if args.location not in available_locations:
            print(f"✗ Location '{args.location}' not found. Use --list-locations to see available options.", file=sys.stderr)
            sys.exit(1)
        location_lat = available_locations[args.location]['lat']
        location_lon = available_locations[args.location]['lon']
        location_name = available_locations[args.location]['name']
    
    # Determine sun rasi range
    if args.any_sun_rasi:
        sun_rasi_range = (0.0, 360.0)
    else:
        sun_rasi_range = tuple(args.sun_rasi_range)
    
    # Determine tithi
    target_tithi = None if args.any_tithi else args.tithi
    
    # Determine nakshatras
    target_nakshatras = args.nakshatras if args.nakshatras else []
    target_rahu_nakshatras = args.rahu_nakshatras if hasattr(args, 'rahu_nakshatras') and args.rahu_nakshatras else []
    target_ketu_nakshatras = args.ketu_nakshatras if hasattr(args, 'ketu_nakshatras') and args.ketu_nakshatras else []
    
    # Determine Venus-Jupiter requirement
    require_vj = args.vj_only and not args.no_vj
    
    # Create SearchConfig
    config = SearchConfig(
        sun_rasi_range=sun_rasi_range,
        target_tithi=target_tithi,
        tithi_window=args.tithi_window,
        target_nakshatras=target_nakshatras,
        target_rahu_nakshatras=target_rahu_nakshatras,
        target_ketu_nakshatras=target_ketu_nakshatras,
        target_mars_rasi=getattr(args, 'mars_rasi', None),
        target_mercury_rasi=getattr(args, 'mercury_rasi', None),
        target_jupiter_rasi=getattr(args, 'jupiter_rasi', None),
        target_venus_rasi=getattr(args, 'venus_rasi', None),
        target_saturn_rasi=getattr(args, 'saturn_rasi', None),
        require_vj_alignment=require_vj,
        vj_tolerance_degrees=args.vj_tolerance,
        vj_altitude_above_horizon=args.vj_altitude,
        offset_window_days=args.offset_window
    )
    
    # Prepare output dictionary with all settings
    settings = {
        'year_range': args.year_range,
        'location': location_name,
        'location_lat': location_lat,
        'location_lon': location_lon,
        'config': config.to_dict(),
        'visualize': args.visualize,
        'generate_horoscopes': args.generate_horoscopes,
        'chart_style': args.chart_style,
        'num_visualizations': args.num_visualizations,
        'offset_window_days': args.offset_window,
        'cores': args.cores,
        'verbose': args.verbose,
        'quiet': args.quiet
    }
    
    # Handle save config
    if args.save_config:
        with open(args.save_config, 'w') as f:
            json.dump(settings, f, indent=2, default=str)
        print(f"✓ Configuration saved to: {args.save_config}")
    
    return args, config, settings, location_lat, location_lon, location_name


if __name__ == '__main__':
    freeze_support()
    
    # If invoked without arguments, show help and exit
    if len(sys.argv) <= 1:
        create_argument_parser().print_help()
        sys.exit(0)
    
    # Parse command-line arguments
    args, config, settings, location_lat, location_lon, location_name = parse_arguments()

    # Horoscope reading mode
    if getattr(args, 'read_horoscope', False):
        if args.birth_dt is None or args.birth_lat is None or args.birth_lon is None:
            print("ERROR: --read-horoscope requires --birth-dt, --birth-lat, and --birth-lon")
            print()
            create_argument_parser().print_help()
            sys.exit(2)
        try:
            from horoscope import basic_horoscope_reading
            reading, data = basic_horoscope_reading(
                birth_dt=args.birth_dt,
                latitude=args.birth_lat,
                longitude=args.birth_lon,
                timezone=args.birth_tz,
                generate_chart=getattr(args, 'birth_chart', False),
                chart_style=getattr(args, 'chart_style', 'south_indian'),
            )
            print(reading)
            if 'chart_file' in data:
                print(f"\n✓ Birth chart saved to: {data['chart_file']}")
            sys.exit(0)
        except Exception as e:
            print(f"ERROR generating horoscope reading: {e}")
            sys.exit(1)
    
    # --- VALIDATE EPHEMERIS FILES ---
    if not (os.path.exists(FILE_BC) and os.path.exists(FILE_AD)):
        print(f"ERROR: Ephemeris files not found!")
        print(f"  Expected: {FILE_BC} and {FILE_AD}")
        sys.exit(1)
    
    if not args.quiet:
        print("=" * 70)
        print("THIRUPPAVAI DATING SYSTEM - Astronomical Event Scanner")
        print("=" * 70)
        print(f"\nLocation: {location_name}")
        print(f"  Latitude:  {location_lat}°")
        print(f"  Longitude: {location_lon}°")
        print(f"\nDate Range: {settings['year_range'][0]} to {settings['year_range'][1]}")
        
        print(f"\nSearch Configuration:")
        for key, value in config.to_dict().items():
            if isinstance(value, list) and len(value) > 3:
                print(f"  {key}: [{len(value)} items]")
            else:
                print(f"  {key}: {value}")
    
    print("\nStarting scan...")
    start_time = time.time()
    
    # --- CREATE PROCESSING CHUNKS ---
    year_start, year_end = settings['year_range']
    chunks = [(y, y + args.chunk_size, config) 
              for y in range(year_start, year_end, args.chunk_size)]
    
    raw = []
    match_count = 0
    
    # --- PARALLEL PROCESSING ---
    with Pool(processes=args.cores) as pool:
        for res in pool.imap_unordered(process_chunk_jyotish, chunks):
            if isinstance(res, list) and len(res) > 0:
                # Filter out error messages
                valid_results = [r for r in res if isinstance(r, dict)]
                if valid_results:
                    raw.extend(valid_results)
                    match_count += len(valid_results)
                    if not args.quiet:
                        print(".", end="", flush=True)
    
    if not args.quiet:
        print(f"\n\nFound {match_count} raw events. Deduplicating...")
    
    final = deduplicate(raw)
    final.sort(key=lambda x: x.get("JD", 0))
    
    if not args.quiet:
        print(f"After deduplication: {len(final)} unique events")
    
    # --- EXPORT RESULTS ---
    if args.output:
        csv_name = args.output
    else:
        csv_name = f"results_{year_start}_{year_end}_enhanced.csv"
    
    try:
        with open(csv_name, "w") as f:
            # Write header
            if final:
                header = ",".join(final[0].keys())
                f.write(header + "\n")
                
                # Write events
                for event in final:
                    values = [str(v) for v in event.values()]
                    f.write(",".join(values) + "\n")
        
        if not args.quiet:
            print(f"\n✓ Results saved to: {csv_name}")
    except Exception as e:
        print(f"\nERROR writing CSV: {e}")
    
    # --- GENERATE VISUALIZATIONS ---
    if args.visualize and final:
        if not args.quiet:
            print(f"\nGenerating visualizations for {min(args.num_visualizations, len(final))} events...")
        
        from visualize_event import visualize_event
        
        for idx, event in enumerate(final[:args.num_visualizations], 1):
            try:
                date_str = event.get('Date', 'event').replace(' ', '_').replace('/', '-')
                output_file = f"visualization_{date_str}.png"
                visualize_event(event, location=location_name, output_file=output_file)
                if args.verbose:
                    print(f"  [{idx}] {event['Date']}: {output_file}")
            except Exception as e:
                if args.verbose:
                    print(f"  ERROR visualizing event {idx}: {e}")
    
    # --- GENERATE HOROSCOPES ---
    if args.generate_horoscopes and final:
        if not args.quiet:
            print(f"\nGenerating {args.chart_style} horoscope charts for {min(args.num_visualizations, len(final))} events...")
        
        from horoscope import generate_horoscope
        
        for idx, event in enumerate(final[:args.num_visualizations], 1):
            try:
                date_str = event.get('Date', 'event').replace(' ', '_').replace('/', '-')
                chart_file = f"horoscope_{args.chart_style}_{date_str}.png"
                text_chart, _ = generate_horoscope(event, chart_style=args.chart_style,
                                                  output_file=chart_file, text_output=False)
                
                if args.verbose:
                    print(f"  [{idx}] {event['Date']}")
                    print(text_chart)
            except Exception as e:
                if args.verbose:
                    print(f"  ERROR generating horoscope for event {idx}: {e}")
    
    # --- DISPLAY RESULTS ---
    if final and not args.quiet:
        print("\n" + "=" * 70)
        print(f"RESULTS - First {min(5, len(final))} Matches")
        print("=" * 70)
        
        for i, event in enumerate(final[:5], 1):
            print(f"\n[{i}] {event['Date']}")
            print(f"    Sun:      {event['Sun_Rasi']:<20} ({event['Sun_Nakshatra']})")
            print(f"    Moon:     {event['Moon_Rasi']:<20} ({event['Moon_Nakshatra']})")
            print(f"    Tithi:    {event['Tithi']} ({event['Tithi_Progress']:.1f}% progress)")
            if event['VJ_Separation'] > 0:
                print(f"    V-J Gap:  {event['VJ_Separation']:.2f}°")
    elif not final and not args.quiet:
        print("\nNo events found matching the criteria.")
    
    elapsed = time.time() - start_time
    if not args.quiet:
        print(f"\n{'=' * 70}")
        print(f"Scan completed in {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        print(f"{'=' * 70}")
        print(f"\nTo visualize results:")
        print(f"  python visualize_event.py {csv_name} 5")
        print(f"\nTo generate horoscopes:")
        print(f"  python ThiruppavaiDating.py --load-config <config.json> --generate-horoscopes")

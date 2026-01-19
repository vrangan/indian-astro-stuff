"""
Horoscope Chart Generation Module
==================================
Generates birth charts in both South Indian (Square) and North Indian (Diamond) styles.
Includes house calculations, planetary placements, and chart visualization.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Polygon, Rectangle, Circle, FancyBboxPatch
import numpy as np
from typing import Dict, Tuple, Optional, List, Union
from datetime import datetime
import pytz
from skyfield.api import load
from ThiruppavaiDating import (
    get_lahiri_ayanamsa,
    get_rasi_info,
    get_nakshatra_info,
    mean_lunar_ascending_node_longitude_deg,
    calculate_lagna,
    FILE_BC,
    FILE_AD,
)
from dataclasses import dataclass

# --- CONSTANTS ---

# House names (Bhavas in Sanskrit)
HOUSE_NAMES = {
    1: "Lagna (Ascendant)", 2: "Wealth", 3: "Siblings", 4: "Home/Mother",
    5: "Children/Creativity", 6: "Health/Enemies", 7: "Spouse/Marriage",
    8: "Longevity/Inheritance", 9: "Dharma/Fortune", 10: "Career/Father",
    11: "Gains/Friendship", 12: "Loss/Moksha"
}

# Rasi abbreviations
RASI_ABBREV = {
    "Mesha": "AR", "Vrishabha": "TA", "Mithuna": "GE", "Karka": "CN",
    "Simha": "LE", "Kanya": "VI", "Tula": "LI", "Vrishchika": "SC",
    "Dhanu": "SG", "Makara": "CP", "Kumbha": "AQ", "Meena": "PI"
}

# Planet symbols and abbreviations
PLANET_ABBREV = {
    'Sun': '☉', 'Moon': '☽', 'Mars': '♂', 'Mercury': '☿',
    'Jupiter': '♃', 'Venus': '♀', 'Saturn': '♄', 'Rahu': 'R', 'Ketu': 'K'
}

PLANET_SHORT = {
    'Sun': 'Su', 'Moon': 'Mo', 'Mars': 'Ma', 'Mercury': 'Me',
    'Jupiter': 'Ju', 'Venus': 'Ve', 'Saturn': 'Sa', 'Rahu': 'Ra', 'Ketu': 'Ke'
}

# Chart style constants
SOUTH_INDIAN_STYLE = 'south_indian'
NORTH_INDIAN_STYLE = 'north_indian'


@dataclass
class HouseData:
    """Data for a single house in the chart."""
    number: int           # House number (1-12)
    rasi: str            # Zodiacal sign
    rasi_lord: int       # Sign ruler (0-11)
    longitude: float     # Starting degree
    planets: List[Dict]  # Planets in this house


class HoroscopeChart:
    """
    Base class for horoscope chart generation.
    Handles chart structure and planetary placement.
    """
    
    def __init__(self, event_data: Dict, lagna_longitude: float, style: str = SOUTH_INDIAN_STYLE):
        """
        Initialize horoscope chart.
        
        Args:
            event_data: Dictionary with planetary positions and information
            lagna_longitude: Ascending sign longitude (birth time specific)
            style: 'south_indian' or 'north_indian'
        """
        self.event_data = event_data
        self.lagna_longitude = lagna_longitude
        self.style = style
        self.houses: List[HouseData] = []
        self.fig = None
        self.ax = None
        
        # Calculate houses based on lagna
        self._calculate_houses()
        self._place_planets()
    
    def _calculate_houses(self):
        """
        Calculate 12 houses starting from Lagna (Ascendant).
        
        In Vedic astrology, houses are calculated from the Lagna.
        Each house starts at a Rasi boundary approximately 30° apart.
        (Note: This is simplified. Real calculation uses Bhava Chalita with
        more complex mathematics based on latitude and time)
        """
        for house_num in range(1, 13):
            # Calculate house starting degree
            # In simplified system: each house = 30° (one Rasi)
            house_start_lon = (self.lagna_longitude + (house_num - 1) * 30.0) % 360.0
            
            # Determine which Rasi this house starts in
            rasi_idx = int(house_start_lon / 30.0)
            rasi_name = self._get_rasi_name(rasi_idx)
            
            house = HouseData(
                number=house_num,
                rasi=rasi_name,
                rasi_lord=rasi_idx,
                longitude=house_start_lon,
                planets=[]
            )
            self.houses.append(house)
    
    def _place_planets(self):
        """
        Place planets in their respective houses.
        
        A planet is in a house if its longitude falls between the house start
        and the next house start.
        """
        planets = {
            'Sun': self.event_data.get('Sun_Longitude', 0),
            'Moon': self.event_data.get('Moon_Longitude', 0),
            'Mars': self.event_data.get('Mars_Longitude', 0),
            'Mercury': self.event_data.get('Mercury_Longitude', 0),
            'Jupiter': self.event_data.get('Jupiter_Longitude', 0),
            'Venus': self.event_data.get('Venus_Longitude', 0),
            'Saturn': self.event_data.get('Saturn_Longitude', 0),
        }
        
        for planet_name, longitude in planets.items():
            # Find which house this planet is in
            house_idx = int((longitude - self.lagna_longitude) % 360.0 / 30.0)
            if house_idx >= 12:
                house_idx = 11
            
            planet_info = {
                'name': planet_name,
                'longitude': longitude,
                'abbreviation': PLANET_SHORT.get(planet_name, planet_name[:2])
            }
            self.houses[house_idx].planets.append(planet_info)
    
    def _get_rasi_name(self, rasi_idx: int) -> str:
        """Get Rasi name from index."""
        rasi_names = [
            "Mesha", "Vrishabha", "Mithuna", "Karka",
            "Simha", "Kanya", "Tula", "Vrishchika",
            "Dhanu", "Makara", "Kumbha", "Meena"
        ]
        return rasi_names[rasi_idx % 12]
    
    def _get_rasi_color(self, rasi_name: str) -> str:
        """Get color for a Rasi based on element."""
        elements = {
            'Fire': ['Mesha', 'Simha', 'Dhanu'],
            'Earth': ['Vrishabha', 'Kanya', 'Makara'],
            'Air': ['Mithuna', 'Tula', 'Kumbha'],
            'Water': ['Karka', 'Vrishchika', 'Meena']
        }
        
        colors = {
            'Fire': '#FF6347',
            'Earth': '#8B4513',
            'Air': '#87CEEB',
            'Water': '#4169E1'
        }
        
        for element, rasis in elements.items():
            if rasi_name in rasis:
                return colors[element]
        return '#CCCCCC'
    
    def generate_text_chart(self) -> str:
        """
        Generate ASCII representation of the chart.
        
        Returns:
            String representation of the chart
        """
        output = "\n" + "="*80 + "\n"
        output += f"HOROSCOPE CHART - {self.style.upper()}\n"
        output += "="*80 + "\n\n"
        
        if self.style == SOUTH_INDIAN_STYLE:
            output += self._generate_south_indian_text()
        else:
            output += self._generate_north_indian_text()
        
        return output
    
    def _generate_south_indian_text(self) -> str:
        """Generate South Indian chart in text format."""
        output = ""
        
        # South Indian: 3x4 grid
        # 12  1  2  3
        # 11  X  X  4
        # 10  X  X  5
        #  9  8  7  6
        
        house_positions = [
            [12, 1, 2, 3],
            [11, 0, 0, 4],
            [10, 0, 0, 5],
            [9, 8, 7, 6]
        ]
        
        for row in house_positions:
            for house_num in row:
                if house_num == 0:
                    output += "   |    |   "
                else:
                    house = self.houses[house_num - 1]
                    output += f"[H{house_num:2d}]"
            output += "\n"
            
            # Add house details
            for house_num in row:
                if house_num > 0:
                    house = self.houses[house_num - 1]
                    rasi_abbr = RASI_ABBREV.get(house.rasi, house.rasi[:2])
                    planet_str = ""
                    for planet in house.planets:
                        planet_str += planet['abbreviation'] + " "
                    if not planet_str:
                        planet_str = "---"
                    output += f" {rasi_abbr}:{planet_str:<6}"
                else:
                    output += "        "
            output += "\n\n"
        
        return output
    
    def _generate_north_indian_text(self) -> str:
        """Generate North Indian chart in text format."""
        output = ""
        
        # North Indian: Diamond shape
        #         1
        #      12   2
        #   11         3
        #  10           4
        #   9           5
        #      8    6
        #         7
        
        output += "        [H 1]\n"
        output += "    [H 12]  [H 2]\n"
        output += "[H 11]         [H 3]\n"
        output += "[H 10]           [H 4]\n"
        output += "[H  9]           [H 5]\n"
        output += "    [H 8]   [H 6]\n"
        output += "        [H 7]\n\n"
        
        # Add details for each house
        for house_num in range(1, 13):
            house = self.houses[house_num - 1]
            rasi_abbr = RASI_ABBREV.get(house.rasi, house.rasi[:2])
            planet_str = ""
            for planet in house.planets:
                planet_str += planet['abbreviation'] + " "
            if not planet_str:
                planet_str = "---"
            
            output += f"House {house_num:2d}: {rasi_abbr} - {HOUSE_NAMES[house_num]:<25} Planets: {planet_str}\n"
        
        return output


class SouthIndianChart(HoroscopeChart):
    """
    South Indian (Square) style horoscope chart.
    Arranged in a 3x4 grid with 12 houses.
    """
    
    def __init__(self, event_data: Dict, lagna_longitude: float):
        """Initialize South Indian style chart."""
        super().__init__(event_data, lagna_longitude, style=SOUTH_INDIAN_STYLE)
    
    def visualize(self, filename: str = "horoscope_south_indian.png", show: bool = False):
        """
        Create visual representation of South Indian chart.
        
        Args:
            filename: Output PNG filename
            show: Whether to display the chart
        """
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # Grid parameters
        cell_width = 1.0
        cell_height = 1.0
        grid_x, grid_y = 4, 4  # 3x4 grid plus margins
        
        # House positions in grid: [row, col]
        house_grid = [
            (0, 3),   # House 1
            (0, 2),   # House 2
            (0, 1),   # House 3
            (0, 0),   # House 4
            (1, 0),   # House 5
            (2, 0),   # House 6
            (3, 0),   # House 7
            (3, 1),   # House 8
            (3, 2),   # House 9
            (3, 3),   # House 10
            (2, 3),   # House 11
            (1, 3),   # House 12
        ]
        
        # Actually, South Indian is:
        # 12  1  2  3
        # 11  X  X  4
        # 10  X  X  5
        #  9  8  7  6
        
        house_grid = [
            (0, 1),   # House 1
            (0, 2),   # House 2
            (0, 3),   # House 3
            (1, 3),   # House 4
            (2, 3),   # House 5
            (3, 3),   # House 6
            (3, 2),   # House 7
            (3, 1),   # House 8
            (3, 0),   # House 9
            (2, 0),   # House 10
            (1, 0),   # House 11
            (0, 0),   # House 12
        ]
        
        ax.set_xlim(-0.5, 4)
        ax.set_ylim(-0.5, 4)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Draw houses
        for house_num, (row, col) in enumerate(house_grid, 1):
            x = col
            y = 3 - row  # Flip y-axis
            
            # Get house data
            house = self.houses[house_num - 1]
            color = self._get_rasi_color(house.rasi)
            
            # Draw house box
            rect = Rectangle((x, y), cell_width, cell_height,
                            linewidth=2, edgecolor='black', facecolor=color, alpha=0.3)
            ax.add_patch(rect)
            
            # Add house number and Rasi
            rasi_abbr = RASI_ABBREV.get(house.rasi, house.rasi[:2])
            ax.text(x + 0.5, y + 0.8, f"H{house_num}", ha='center', va='top',
                   fontsize=10, fontweight='bold')
            ax.text(x + 0.5, y + 0.5, rasi_abbr, ha='center', va='center',
                   fontsize=9)
            
            # Add planets
            planets_text = " ".join([p['abbreviation'] for p in house.planets])
            if planets_text:
                ax.text(x + 0.5, y + 0.2, planets_text, ha='center', va='bottom',
                       fontsize=8, color='red')
        
        plt.title("South Indian Horoscope Chart", fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"✓ South Indian chart saved to: {filename}")
        
        if show:
            plt.show()
        else:
            plt.close()


class NorthIndianChart(HoroscopeChart):
    """
    North Indian (Diamond) style horoscope chart.
    Arranged in a diamond/rhombus shape with 12 houses.
    """
    
    def __init__(self, event_data: Dict, lagna_longitude: float):
        """Initialize North Indian style chart."""
        super().__init__(event_data, lagna_longitude, style=NORTH_INDIAN_STYLE)
    
    def visualize(self, filename: str = "horoscope_north_indian.png", show: bool = False):
        """
        Create visual representation of North Indian chart.
        
        Diamond shape:
                    1
                 12   2
              11         3
            10             4
             9             5
                8    6
                    7
        
        Args:
            filename: Output PNG filename
            show: Whether to display the chart
        """
        fig, ax = plt.subplots(figsize=(12, 12))
        
        # House positions as (x, y) coordinates
        house_positions = {
            1: (5, 10),
            2: (7, 8),
            3: (9, 6),
            4: (10, 4),
            5: (9, 2),
            6: (7, 1),
            7: (5, 0),
            8: (3, 1),
            9: (1, 2),
            10: (0, 4),
            11: (1, 6),
            12: (3, 8),
        }
        
        # Draw houses as diamonds
        size = 0.8
        for house_num in range(1, 13):
            x, y = house_positions[house_num]
            house = self.houses[house_num - 1]
            color = self._get_rasi_color(house.rasi)
            
            # Create diamond/square
            diamond = Polygon([
                (x - size/2, y),
                (x, y + size/2),
                (x + size/2, y),
                (x, y - size/2)
            ], facecolor=color, edgecolor='black', linewidth=2, alpha=0.3)
            ax.add_patch(diamond)
            
            # Add house number
            ax.text(x, y + 0.3, f"H{house_num}", ha='center', va='center',
                   fontsize=9, fontweight='bold')
            
            # Add Rasi
            rasi_abbr = RASI_ABBREV.get(house.rasi, house.rasi[:2])
            ax.text(x, y, rasi_abbr, ha='center', va='center',
                   fontsize=8)
            
            # Add planets
            planets_text = " ".join([p['abbreviation'] for p in house.planets])
            if planets_text:
                ax.text(x, y - 0.3, planets_text, ha='center', va='center',
                       fontsize=7, color='red')
        
        ax.set_xlim(-2, 12)
        ax.set_ylim(-1, 11)
        ax.set_aspect('equal')
        ax.axis('off')
        
        plt.title("North Indian Horoscope Chart", fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"✓ North Indian chart saved to: {filename}")
        
        if show:
            plt.show()
        else:
            plt.close()


def generate_horoscope(event_data: Dict, chart_style: str = SOUTH_INDIAN_STYLE,
                      output_file: Optional[str] = None,
                      text_output: bool = True,
                      lagna_longitude: Optional[float] = None) -> Tuple[str, Optional[str]]:
    """
    Generate horoscope in specified style.
    
    Args:
        event_data: Dictionary with event planetary positions
        chart_style: 'south_indian' or 'north_indian'
        output_file: Optional filename for PNG export
        text_output: Whether to generate and return text representation
        lagna_longitude: Lagna (Ascendant) longitude; if None, uses Sun position
    
    Returns:
        Tuple of (text_representation, output_filename)
    """
    # Use Lagna if provided, otherwise fall back to Sun position (simplified)
    if lagna_longitude is None:
        lagna_longitude = event_data.get('Sun_Longitude', 0)
    
    if chart_style == SOUTH_INDIAN_STYLE:
        chart = SouthIndianChart(event_data, lagna_longitude)
    else:
        chart = NorthIndianChart(event_data, lagna_longitude)
    
    # Generate text chart
    text_chart = chart.generate_text_chart()
    
    # Generate visualization
    if output_file:
        if chart_style == SOUTH_INDIAN_STYLE:
            chart.visualize(output_file, show=False)
        else:
            chart.visualize(output_file, show=False)
        return text_chart, output_file
    
    return text_chart, None


def basic_horoscope_reading(
    birth_dt: Union[str, datetime],
    latitude: float,
    longitude: float,
    timezone: str = "UTC",
    generate_chart: bool = False,
    chart_style: str = SOUTH_INDIAN_STYLE,
) -> Tuple[str, Dict[str, float]]:
    """
    Generate an introductory horoscope reading for a birth datetime and place.

    Args:
        birth_dt: Datetime (aware or naive) or ISO string (e.g., '1990-01-01T12:34:00').
        latitude: Birth latitude in decimal degrees.
        longitude: Birth longitude in decimal degrees.
        timezone: IANA timezone name for birth time if birth_dt is naive or string.
        generate_chart: If True, also generate a chart file and return its filename.
        chart_style: 'south_indian' or 'north_indian' (default: south_indian).

    Returns:
        Tuple of (reading_text, data) where data includes key longitudes and labels.
    """
    # Normalize input datetime
    if isinstance(birth_dt, str):
        # Parse ISO string; if no timezone info, localize to provided timezone
        from datetime import datetime as dt_class
        try:
            dt = dt_class.fromisoformat(birth_dt)
        except Exception:
            # Fallback for common formats
            dt = dt_class.strptime(birth_dt, "%Y-%m-%d %H:%M:%S")
    else:
        dt = birth_dt

    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        tz = pytz.timezone(timezone)
        dt = tz.localize(dt)
    # Convert to UTC
    dt_utc = dt.astimezone(pytz.utc)

    # Load ephemeris based on era
    eph_file = FILE_AD if dt_utc.year >= 1 else FILE_BC
    eph = load(eph_file)
    ts = load.timescale()
    t = ts.utc(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute, dt_utc.second)

    earth = eph[399]
    sun = eph['sun']
    moon = eph['moon']
    mars = eph['mars barycenter']
    mercury = eph['mercury barycenter']
    jupiter = eph['jupiter barycenter']
    venus = eph['venus']
    saturn = eph['saturn barycenter']

    # Compute ayanamsa and positions (sidereal)
    ayan = get_lahiri_ayanamsa(t)

    def tropical_lon(body):
        _, lon, _ = earth.at(t).observe(body).apparent().ecliptic_latlon()
        return lon.degrees

    sun_lon_sid = (tropical_lon(sun) - ayan) % 360.0
    moon_lon_sid = (tropical_lon(moon) - ayan) % 360.0
    mars_lon_sid = (tropical_lon(mars) - ayan) % 360.0
    mercury_lon_sid = (tropical_lon(mercury) - ayan) % 360.0
    jupiter_lon_sid = (tropical_lon(jupiter) - ayan) % 360.0
    venus_lon_sid = (tropical_lon(venus) - ayan) % 360.0
    saturn_lon_sid = (tropical_lon(saturn) - ayan) % 360.0

    # Rahu/Ketu (mean node)
    omega = mean_lunar_ascending_node_longitude_deg(t)
    rahu_lon_sid = (omega - ayan) % 360.0
    ketu_lon_sid = (rahu_lon_sid + 180.0) % 360.0
    
    # Calculate Lagna (Ascendant)
    lagna_lon_sid, lagna_rasi, lagna_rasi_idx = calculate_lagna(t, latitude, longitude)

    # Labels
    sun_rasi, sun_rasi_idx, _, _ = get_rasi_info(sun_lon_sid)
    moon_rasi, moon_rasi_idx, _, _ = get_rasi_info(moon_lon_sid)
    moon_nak_name, moon_nak_idx, _, _ = get_nakshatra_info(moon_lon_sid)
    mars_rasi, _, _, _ = get_rasi_info(mars_lon_sid)
    mercury_rasi, _, _, _ = get_rasi_info(mercury_lon_sid)
    jupiter_rasi, _, _, _ = get_rasi_info(jupiter_lon_sid)
    venus_rasi, _, _, _ = get_rasi_info(venus_lon_sid)
    saturn_rasi, _, _, _ = get_rasi_info(saturn_lon_sid)
    rahu_rasi, _, _, _ = get_rasi_info(rahu_lon_sid)
    ketu_rasi, _, _, _ = get_rasi_info(ketu_lon_sid)
    rahu_nak_name, _, _, _ = get_nakshatra_info(rahu_lon_sid)
    ketu_nak_name, _, _, _ = get_nakshatra_info(ketu_lon_sid)

    # Simple interpretive text (intro-level)
    lines = []
    lines.append("Introductory Horoscope Reading")
    lines.append("-" * 32)
    lines.append(f"Birth (UTC): {dt_utc.strftime('%Y-%m-%d %H:%M:%S')} @ ({latitude:.4f}°, {longitude:.4f}°)")
    lines.append("")
    lines.append(f"Lagna (Ascendant): {lagna_rasi} ({lagna_lon_sid:.2f}°)")
    lines.append("")
    lines.append("Planetary Positions (Sidereal):")
    lines.append(f"  Sun:     {sun_rasi} ({sun_lon_sid:.2f}°)")
    lines.append(f"  Moon:    {moon_rasi} ({moon_lon_sid:.2f}°), Nakshatra: {moon_nak_name}")
    lines.append(f"  Mars:    {mars_rasi} ({mars_lon_sid:.2f}°)")
    lines.append(f"  Mercury: {mercury_rasi} ({mercury_lon_sid:.2f}°)")
    lines.append(f"  Jupiter: {jupiter_rasi} ({jupiter_lon_sid:.2f}°)")
    lines.append(f"  Venus:   {venus_rasi} ({venus_lon_sid:.2f}°)")
    lines.append(f"  Saturn:  {saturn_rasi} ({saturn_lon_sid:.2f}°)")
    lines.append(f"  Rahu:    {rahu_rasi} ({rahu_lon_sid:.2f}°), Nakshatra: {rahu_nak_name}")
    lines.append(f"  Ketu:    {ketu_rasi} ({ketu_lon_sid:.2f}°), Nakshatra: {ketu_nak_name}")

    # Basic character notes based on Moon Nakshatra (very high-level placeholders)
    nak_traits = {
        'Ashwini': 'Quick, pioneering, healing tendencies.',
        'Bharani': 'Strong will, transformative, passionate.',
        'Krittika': 'Sharp, determined, protective.',
        'Rohini': 'Attractive, artistic, fertile.',
        'Mrigashirsha': 'Curious, adaptable, seeking.',
        'Ardra': 'Intense, insightful, resilient.',
        'Punarvasu': 'Nurturing, renewing, optimistic.',
        'Pushya': 'Supportive, disciplined, traditional.',
        'Ashlesha': 'Perceptive, magnetic, strategic.',
        'Magha': 'Regal, ancestral pride, leadership.',
        'Purva Phalguni': 'Creative, sociable, enjoyment.',
        'Uttara Phalguni': 'Responsible, reliable, generous.',
        'Hasta': 'Skillful, dexterous, service-oriented.',
        'Chitra': 'Aesthetic, refined, independent.',
        'Swati': 'Flexible, independent, trade-oriented.',
        'Vishakha': 'Goal-focused, determined, devotional.',
        'Anuradha': 'Loyal, friendly, disciplined.',
        'Jyeshtha': 'Ambitious, protective, strategic.',
        'Mula': 'Root-seeking, transformative, philosophical.',
        'Purva Ashadha': 'Victorious, persuasive, spirited.',
        'Uttara Ashadha': 'Enduring, principled, leadership.',
        'Shravana': 'Learning, listening, travel.',
        'Dhanishta': 'Rhythmic, communal, prosperous.',
        'Shatabhisha': 'Healing, scientific, protective.',
        'Purva Bhadrapada': 'Deep, mystical, idealistic.',
        'Uttara Bhadrapada': 'Stable, compassionate, wise.',
        'Revati': 'Kind, guiding, prosperous.',
    }
    trait = nak_traits.get(moon_nak_name, "Balanced qualities depending on aspects and house placement.")
    lines.append("")
    lines.append(f"Moon Nakshatra Insight: {trait}")

    reading = "\n".join(lines)
    data = {
        'lagna_lon_sid': lagna_lon_sid,
        'lagna_rasi': lagna_rasi,
        'lagna_rasi_idx': lagna_rasi_idx,
        'sun_lon_sid': sun_lon_sid,
        'moon_lon_sid': moon_lon_sid,
        'mars_lon_sid': mars_lon_sid,
        'mercury_lon_sid': mercury_lon_sid,
        'jupiter_lon_sid': jupiter_lon_sid,
        'venus_lon_sid': venus_lon_sid,
        'saturn_lon_sid': saturn_lon_sid,
        'rahu_lon_sid': rahu_lon_sid,
        'ketu_lon_sid': ketu_lon_sid,
        'sun_rasi': sun_rasi,
        'moon_rasi': moon_rasi,
        'moon_nakshatra': moon_nak_name,
        'mars_rasi': mars_rasi,
        'mercury_rasi': mercury_rasi,
        'jupiter_rasi': jupiter_rasi,
        'venus_rasi': venus_rasi,
        'saturn_rasi': saturn_rasi,
        'rahu_rasi': rahu_rasi,
        'ketu_rasi': ketu_rasi,
        'rahu_nakshatra': rahu_nak_name,
        'ketu_nakshatra': ketu_nak_name,
    }

    # Optional chart generation
    if generate_chart:
        event_data = {
            'Sun_Longitude': sun_lon_sid,
            'Moon_Longitude': moon_lon_sid,
            'Mars_Longitude': mars_lon_sid,
            'Mercury_Longitude': mercury_lon_sid,
            'Jupiter_Longitude': jupiter_lon_sid,
            'Venus_Longitude': venus_lon_sid,
            'Saturn_Longitude': saturn_lon_sid,
        }
        from datetime import datetime as dt_class
        dt_str = dt_utc.strftime('%Y%m%d_%H%M%S')
        chart_file = f"birth_chart_{chart_style}_{dt_str}.png"
        # Use calculated Lagna for proper house placement
        _, _ = generate_horoscope(event_data, chart_style, chart_file, text_output=False, lagna_longitude=lagna_lon_sid)
        data['chart_file'] = chart_file

    return reading, data


if __name__ == '__main__':
    # Example usage
    sample_event = {
        'Sun_Longitude': 285.0,
        'Moon_Longitude': 287.0,
        'Mars_Longitude': 120.0,
        'Mercury_Longitude': 290.0,
        'Jupiter_Longitude': 283.0,
        'Venus_Longitude': 282.0,
        'Saturn_Longitude': 200.0,
    }
    
    # Generate both styles
    print("South Indian Chart:")
    text_si, file_si = generate_horoscope(sample_event, SOUTH_INDIAN_STYLE,
                                          "horoscope_si.png", text_output=True)
    print(text_si)
    
    print("\n\nNorth Indian Chart:")
    text_ni, file_ni = generate_horoscope(sample_event, NORTH_INDIAN_STYLE,
                                          "horoscope_ni.png", text_output=True)
    print(text_ni)

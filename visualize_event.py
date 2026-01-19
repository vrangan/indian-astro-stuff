"""
Sky Visualization Module for Thiruppavai Dating System
========================================================
Creates visual representations of planetary positions and zodiacal alignments
at specific astronomical events described in Indian texts.

This module generates:
- Zodiacal wheel showing all planetary positions
- Nakshatra (lunar mansion) positions
- Aspect relationships between planets
- Tithi (lunar day) progression
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Wedge, FancyBboxPatch, Circle
import numpy as np
from typing import Dict, List, Tuple, Optional
import pandas as pd

# --- CONSTANTS (same as main module) ---
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashirsha", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

RASIS = [
    "Mesha", "Vrishabha", "Mithuna", "Karka",
    "Simha", "Kanya", "Tula", "Vrishchika",
    "Dhanu", "Makara", "Kumbha", "Meena"
]

# Color scheme for planets (Vedic tradition)
PLANET_COLORS = {
    'Sun': '#FDB813',           # Gold/Yellow
    'Moon': '#E0E0E0',          # Silver/White
    'Mars': '#E27B58',          # Red/Copper
    'Mercury': '#90EE90',       # Green
    'Jupiter': '#DAA520',       # Orange/Saffron
    'Venus': '#87CEEB',         # Light Blue
    'Saturn': '#696969'         # Dark Gray
}

# Vedic element and quality associations
RASI_ELEMENTS = {
    'Mesha': 'Fire', 'Vrishabha': 'Earth', 'Mithuna': 'Air', 'Karka': 'Water',
    'Simha': 'Fire', 'Kanya': 'Earth', 'Tula': 'Air', 'Vrishchika': 'Water',
    'Dhanu': 'Fire', 'Makara': 'Earth', 'Kumbha': 'Air', 'Meena': 'Water'
}

RASI_COLORS = {
    'Fire': '#FF6347', 'Earth': '#8B4513', 'Air': '#87CEEB', 'Water': '#4169E1'
}


class ZodiacalWheel:
    """
    Creates an interactive zodiacal wheel visualization showing:
    - All 12 Rasis (zodiacal signs)
    - All 27 Nakshatras (lunar mansions)
    - Planetary positions
    - Aspects between planets
    """
    
    def __init__(self, figsize: Tuple[int, int] = (14, 14)):
        """
        Initialize the zodiacal wheel visualization.
        
        Args:
            figsize: Figure size in inches (width, height)
        """
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.ax.set_xlim(-1.5, 1.5)
        self.ax.set_ylim(-1.5, 1.5)
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        
    def add_rasi_ring(self, inner_radius: float = 1.0, outer_radius: float = 1.2):
        """
        Add the inner zodiacal ring showing 12 Rasis.
        
        Each Rasi is 30° and colored by element (Fire, Earth, Air, Water).
        
        Args:
            inner_radius: Inner boundary radius of the ring
            outer_radius: Outer boundary radius of the ring
        """
        for i, rasi in enumerate(RASIS):
            angle_start = i * 30
            angle_end = (i + 1) * 30
            
            # Create wedge for this Rasi
            element = RASI_ELEMENTS[rasi]
            color = RASI_COLORS[element]
            
            wedge = Wedge((0, 0), outer_radius, angle_start, angle_end,
                         width=outer_radius - inner_radius,
                         facecolor=color, edgecolor='black', linewidth=0.5, alpha=0.3)
            self.ax.add_patch(wedge)
            
            # Add Rasi label
            mid_angle = (angle_start + angle_end) / 2
            mid_angle_rad = np.radians(mid_angle)
            label_radius = (inner_radius + outer_radius) / 2
            
            x = label_radius * np.cos(mid_angle_rad)
            y = label_radius * np.sin(mid_angle_rad)
            
            # Rotate text to match position
            rotation = mid_angle if mid_angle < 90 or mid_angle > 270 else mid_angle - 180
            self.ax.text(x, y, rasi, ha='center', va='center', fontsize=9, 
                        fontweight='bold', rotation=rotation)
    
    def add_nakshatra_ring(self, inner_radius: float = 0.75, outer_radius: float = 0.95):
        """
        Add the Nakshatra ring showing 27 lunar mansions.
        
        Each Nakshatra is 13°20' (360°/27) of the zodiac.
        
        Args:
            inner_radius: Inner boundary radius
            outer_radius: Outer boundary radius
        """
        nak_size = 360.0 / 27
        
        for i, nak in enumerate(NAKSHATRAS):
            angle_start = i * nak_size
            angle_end = (i + 1) * nak_size
            
            # Alternate colors for visual clarity
            color = '#F0E68C' if i % 2 == 0 else '#DEB887'
            
            wedge = Wedge((0, 0), outer_radius, angle_start, angle_end,
                         width=outer_radius - inner_radius,
                         facecolor=color, edgecolor='gray', linewidth=0.5, alpha=0.4)
            self.ax.add_patch(wedge)
            
            # Add Nakshatra label (abbreviated)
            mid_angle = (angle_start + angle_end) / 2
            mid_angle_rad = np.radians(mid_angle)
            label_radius = (inner_radius + outer_radius) / 2
            
            x = label_radius * np.cos(mid_angle_rad)
            y = label_radius * np.sin(mid_angle_rad)
            
            nak_abbrev = nak[:3]  # Use first 3 letters
            rotation = mid_angle if mid_angle < 90 or mid_angle > 270 else mid_angle - 180
            
            self.ax.text(x, y, nak_abbrev, ha='center', va='center', fontsize=7)
    
    def add_planets(self, planets: Dict[str, float], radius: float = 0.5):
        """
        Add planetary positions on the zodiacal wheel.
        
        Args:
            planets: Dict with planet names and their sidereal longitudes (0-360)
            radius: Radius at which to draw planets
        """
        for planet_name, longitude in planets.items():
            if planet_name not in PLANET_COLORS:
                continue
            
            # Convert longitude to angle (0° = East, counter-clockwise)
            angle_rad = np.radians(90 - longitude)  # Flip to match standard astronomical convention
            
            x = radius * np.cos(angle_rad)
            y = radius * np.sin(angle_rad)
            
            # Draw planet
            circle = Circle((x, y), 0.04, color=PLANET_COLORS[planet_name],
                          edgecolor='black', linewidth=1.5, zorder=5)
            self.ax.add_patch(circle)
            
            # Add planet label
            self.ax.text(x, y - 0.08, planet_name, ha='center', va='top', 
                        fontsize=8, fontweight='bold')
            
            # Add longitude label
            self.ax.text(x, y + 0.08, f"{longitude:.1f}°", ha='center', va='bottom',
                        fontsize=7, color='gray')
    
    def add_aspects(self, planets: Dict[str, float], tolerance_deg: float = 5.0):
        """
        Draw lines showing planetary aspects (conjunctions, oppositions, etc.).
        
        Args:
            planets: Dict with planet names and longitudes
            tolerance_deg: Aspect orb tolerance
        """
        planet_list = list(planets.items())
        radius = 0.5
        
        for i in range(len(planet_list)):
            for j in range(i + 1, len(planet_list)):
                p1_name, p1_lon = planet_list[i]
                p2_name, p2_lon = planet_list[j]
                
                # Calculate angular difference
                diff = abs(p1_lon - p2_lon)
                if diff > 180:
                    diff = 360 - diff
                
                # Check if this is a major aspect
                aspect_name = None
                if abs(diff - 0) <= tolerance_deg or abs(diff - 360) <= tolerance_deg:
                    aspect_name = 'Conjunction'
                    line_style = '--'
                    color = 'red'
                elif abs(diff - 180) <= tolerance_deg:
                    aspect_name = 'Opposition'
                    line_style = '-'
                    color = 'blue'
                elif abs(diff - 120) <= tolerance_deg:
                    aspect_name = 'Trine'
                    line_style = '-'
                    color = 'green'
                elif abs(diff - 90) <= tolerance_deg:
                    aspect_name = 'Square'
                    line_style = ':'
                    color = 'orange'
                
                if aspect_name:
                    # Convert to cartesian and draw line
                    angle1_rad = np.radians(90 - p1_lon)
                    angle2_rad = np.radians(90 - p2_lon)
                    
                    x1, y1 = radius * np.cos(angle1_rad), radius * np.sin(angle1_rad)
                    x2, y2 = radius * np.cos(angle2_rad), radius * np.sin(angle2_rad)
                    
                    self.ax.plot([x1, x2], [y1, y2], linestyle=line_style, 
                               color=color, linewidth=1.5, alpha=0.6)
    
    def add_title_and_info(self, event_date: str, location: str, 
                          tithi: str, moon_nak: str):
        """
        Add title and event information to the visualization.
        
        Args:
            event_date: Date of the event
            location: Observer location
            tithi: Lunar day name
            moon_nak: Moon's Nakshatra
        """
        title = f"Astronomical Event: {event_date}\n"
        title += f"Location: {location}"
        self.ax.text(0, 1.4, title, ha='center', va='top', fontsize=14, fontweight='bold')
        
        info = f"Tithi: {tithi} | Moon Nakshatra: {moon_nak}"
        self.ax.text(0, -1.4, info, ha='center', va='bottom', fontsize=10, 
                    style='italic', color='gray')
    
    def add_legend(self):
        """Add legend explaining the visualization elements."""
        legend_text = (
            "Rings (outer to inner): Rasis (12 signs) → Nakshatras (27 mansions) → Planets\n"
            "Colors: Red=Conjunction | Green=Trine | Blue=Opposition | Orange=Square"
        )
        self.ax.text(-1.45, 1.3, legend_text, ha='left', va='top', fontsize=8,
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    def save_and_show(self, filename: str = 'zodiac_event.png', show: bool = True):
        """
        Save and optionally display the visualization.
        
        Args:
            filename: Output filename for the image
            show: Whether to display the image
        """
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"✓ Visualization saved to: {filename}")
        
        if show:
            plt.show()
        else:
            plt.close()


def visualize_event(event_data: Dict, location: str = "Srivilliputur",
                    output_file: str = None) -> str:
    """
    Create a complete zodiacal wheel visualization for an astronomical event.
    
    Main function to visualize a single event from the results CSV.
    
    Args:
        event_data: Dictionary containing event information (from CSV row)
        location: Observer location name
        output_file: Optional custom output filename
    Returns:
        Path to the generated visualization file
    """
    
    # Create zodiacal wheel
    wheel = ZodiacalWheel(figsize=(14, 14))
    wheel.add_rasi_ring()
    wheel.add_nakshatra_ring()
    
    # Prepare planetary positions
    planets = {
        'Sun': event_data.get('Sun_Longitude', 0),
        'Moon': event_data.get('Moon_Longitude', 0),
        'Venus': event_data.get('Venus_Longitude', 0),
        'Jupiter': event_data.get('Jupiter_Longitude', 0),
        'Mars': event_data.get('Mars_Longitude', 0),
        'Mercury': event_data.get('Mercury_Longitude', 0),
        'Saturn': event_data.get('Saturn_Longitude', 0)
    }
    
    wheel.add_planets(planets)
    wheel.add_aspects(planets, tolerance_deg=5.0)
    
    # Add information
    wheel.add_title_and_info(
        event_date=event_data.get('Date', 'Unknown'),
        location=location,
        tithi=event_data.get('Tithi', 'Unknown'),
        moon_nak=event_data.get('Moon_Nakshatra', 'Unknown')
    )
    wheel.add_legend()
    
    # Generate output filename
    if not output_file:
        date_str = event_data.get('Date', 'event').replace(' ', '_').replace('/', '-')
        output_file = f"visualization_{date_str}.png"
    
    wheel.save_and_show(output_file, show=False)
    return output_file


def visualize_multiple_events(csv_file: str, num_events: int = 5, 
                              location: str = "Srivilliputur") -> List[str]:
    """
    Generate visualizations for multiple events from results CSV.
    
    Args:
        csv_file: Path to results CSV file
        num_events: Number of top events to visualize
        location: Observer location name
    Returns:
        List of generated visualization filenames
    """
    try:
        df = pd.read_csv(csv_file)
        print(f"\nGenerating visualizations for {min(num_events, len(df))} events...")
        
        output_files = []
        for idx, row in df.head(num_events).iterrows():
            event_dict = row.to_dict()
            print(f"  [{idx+1}/{min(num_events, len(df))}] Visualizing {event_dict.get('Date')}...", end='')
            
            output_file = visualize_event(event_dict, location)
            output_files.append(output_file)
            print(" ✓")
        
        return output_files
        
    except FileNotFoundError:
        print(f"ERROR: CSV file not found: {csv_file}")
        return []
    except Exception as e:
        print(f"ERROR: {e}")
        return []


if __name__ == '__main__':
    """
    Example usage - create visualization from command line
    """
    import sys
    
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        num_events = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        visualize_multiple_events(csv_file, num_events)
    else:
        print("Usage: python visualize_event.py <csv_file> [num_events]")
        print("Example: python visualize_event.py results_-6000_2100_enhanced.csv 5")

# Thiruppavai Dating System - Complete Documentation

## Overview

The **Thiruppavai Dating System** is a sophisticated astronomical dating program designed to identify celestial events described in ancient Indian texts (such as the Ramayana and Mahabharata) using precise Vedic/Jyotish astronomical calculations.

This system combines:
- **Precise ephemeris calculations** using NASA's DE441 SPICE kernels
- **Vedic astronomy principles** including Lahiri Ayanamsa (sidereal correction)
- **Indian astronomical concepts** (Nakshatras, Tithis, Rasis, Yogas)
- **Configurable event detection** to match specific text descriptions
- **Sky visualization** to display planetary alignments at identified events

---

## Key Concepts in Vedic Astronomy

### 1. **Ayanamsa (Precession Correction)**

The Ayanamsa is the angular distance between the tropical zodiac (based on Earth's seasons) and the sidereal zodiac (based on fixed stars). Indian astronomy uses the sidereal coordinate system.

**Lahiri Ayanamsa** is the standard correction used in Vedic astrology:
- Places Aries (0°) aligned with the star Ashwini (first Nakshatra)
- Calculated from J2000.0 epoch (JD 2451545.0)
- Formula: `Ayanamsa = 23°51'57" + (0.01396° per year since epoch)`

**Conversion:** `Sidereal Longitude = Tropical Longitude - Ayanamsa`

### 2. **Nakshatras (Lunar Mansions)**

The zodiac is divided into 27 equal lunar mansions, each spanning 13°20' (360°/27):

| # | Nakshatra | Symbol | Ruling Planet |
|---|-----------|--------|---------------|
| 1 | Ashwini | Horse | Ketu (Moon's South Node) |
| 2 | Bharani | Vagina | Venus |
| 3 | Krittika | Fire | Sun |
| ... | ... | ... | ... |
| 27 | Revati | Drum | Mercury |

**Significance:** Each Nakshatra has unique characteristics, ruling planets, deities, and astrological implications. Used for:
- Timing auspicious events
- Matching birth charts in relationships
- Understanding personality traits
- Predicting favorable periods

### 3. **Tithis (Lunar Days)**

The lunar month is divided into 30 equal lunar days (Tithis), based on the Moon-Sun angular separation:

- **Tithi = (Moon Longitude - Sun Longitude) / 12°**
- **30 Tithis** in a complete lunar month
- **15 Tithis** in the waxing phase (Shukla Paksha)
- **15 Tithis** in the waning phase (Krishna Paksha)
- **Special days:** Purnima (Full Moon, Tithi 15), Amavasya (New Moon, Tithi 30)

**Tithi progression:**
```
0°-12°   → Shukla Pratipadha (1st waxing day)
12°-24°  → Shukla Dwitiya (2nd waxing day)
...
168°-180° → Purnima (Full Moon)
180°-192° → Krishna Pratipadha (1st waning day)
...
348°-360° → Amavasya (New Moon)
```

### 4. **Rasis (Zodiacal Signs)**

The ecliptic is divided into 12 equal Rasis, each 30°:

| # | Rasi | Western Equiv. | Element | Quality |
|----|------|----------------|---------|----------|
| 1 | Mesha | Aries | Fire | Movable |
| 2 | Vrishabha | Taurus | Earth | Fixed |
| 3 | Mithuna | Gemini | Air | Dual |
| ... | ... | ... | ... | ... |
| 12 | Meena | Pisces | Water | Dual |

**Elements:**
- **Fire (3):** Mesha, Simha, Dhanu
- **Earth (3):** Vrishabha, Kanya, Makara
- **Air (3):** Mithuna, Tula, Kumbha
- **Water (3):** Karka, Vrishchika, Meena

### 5. **Planetary Aspects (Drishti)**

Planets influence each other at specific angular relationships (aspects):

| Aspect | Angle | Type | Orb |
|--------|-------|------|-----|
| Conjunction | 0° | Same sign | ±3° |
| Opposition | 180° | Opposite signs | ±3° |
| Trine | 120° | Harmonious | ±3° |
| Square | 90° | Challenging | ±3° |
| Sextile | 60° | Favorable | ±3° |

**Special Vedic Aspects:**
- **Mars, Jupiter, Saturn** have special aspect patterns beyond basic conjunctions/oppositions

### 6. **Yogas (Planetary Combinations)**

Yogas are auspicious or notable planetary combinations with special significance:

- **Mahalakshmi Yoga:** Jupiter and Venus in conjunction
- **Neecha Bhanga:** Planet in debilitation but aspected by friendly planet
- **Parivartana Yoga:** Two planets exchange Rasis
- **Raj Yoga:** Specific planetary placements indicating power/status

---

## Program Architecture

### Main Components

#### 1. **ThiruppavaiDating.py** - Core Scanning Engine

**Key Classes:**
- `SearchConfig`: Configurable event criteria (dataclass)
  - Sun position constraints
  - Moon phase (Tithi) constraints
  - Nakshatra requirements
  - Planetary aspect requirements
  - Search window parameters

**Key Functions:**

- `get_lahiri_ayanamsa(t)`: Calculate precession correction
  ```python
  ayanamsa = 23.857 + (days_since_2000 * 50.27 / 3600.0 / 365.25)
  ```

- `get_nakshatra_info(longitude)`: Identify which Nakshatra contains a given longitude
  ```
  nakshatra_index = int(longitude / 13.333)
  returns: (name, index, start_degree, end_degree)
  ```

- `get_tithi_info(moon_lon, sun_lon)`: Calculate lunar day from Moon-Sun separation
  ```
  tithi_index = int(separation / 12.0)
  returns: (name, index, separation_angle, progress_percent)
  ```

- `get_rasi_info(longitude)`: Identify which Rasi contains a given longitude
  ```
  rasi_index = int(longitude / 30.0)
  returns: (name, index, start_degree, degree_in_rasi)
  ```

- `calculate_planetary_aspects()`: Detect conjunctions, oppositions, trines, squares
  - Returns aspects by type with aspected planets

- `calculate_yogas()`: Identify significant Yoga combinations
  - Checks for Mahalakshmi Yoga, Neecha Bhanga, Parivartana, etc.

- `process_chunk_jyotish()`: Main scanning function (parallelized)
  - Loads ephemeris data
  - Iterates through date range
  - Evaluates SearchConfig criteria
  - Accumulates matching events

**Output:** CSV file with columns:
```
Date, JD, Sun_Longitude, Sun_Rasi, Sun_Nakshatra, Moon_Longitude, 
Moon_Rasi, Moon_Nakshatra, Tithi, Tithi_Index, Tithi_Progress, 
Venus_Longitude, Venus_Rasi, Jupiter_Longitude, Jupiter_Rasi, VJ_Separation,
Mars_Longitude, Mercury_Longitude, Saturn_Longitude
```

#### 2. **visualize_event.py** - Sky Visualization

**Key Classes:**

- `ZodiacalWheel`: Creates zodiacal wheel visualization
  - `add_rasi_ring()`: Draws 12 Rasis with elemental colors
  - `add_nakshatra_ring()`: Draws 27 Nakshatras
  - `add_planets()`: Shows planetary positions
  - `add_aspects()`: Draws aspect lines between planets
  - `add_title_and_info()`: Adds event details
  - `save_and_show()`: Exports as image

**Functions:**

- `visualize_event()`: Create visualization for single event
- `visualize_multiple_events()`: Batch visualize from CSV

**Output:** PNG image showing:
- 12 Rasis (outer ring, colored by element)
- 27 Nakshatras (middle ring, alternating colors)
- Planetary positions (dots at specific degrees)
- Aspect lines (conjunction, opposition, trine, square)
- Event details (date, location, Tithi, Moon Nakshatra)

---

## Configuration

### SearchConfig Parameters

```python
@dataclass
class SearchConfig:
    # Sun position constraints
    sun_rasi: Optional[int] = None              # 0-11 (any Rasi if None)
    sun_rasi_range: Tuple[float, float] = (270.0, 300.0)  # Degree range
    
    # Moon phase constraints  
    target_tithi: Optional[int] = None          # 14=Full Moon, 29=New Moon
    tithi_window: int = 1                        # +/- tithis to match
    
    # Nakshatra constraints
    target_nakshatras: List[int] = []            # Nakshatra indices, empty=any
    
    # Planetary constraints
    require_vj_alignment: bool = True            # Venus-Jupiter proximity
    vj_tolerance_degrees: float = 5.0            # Max separation
    vj_altitude_above_horizon: float = 0.0       # Min altitude for both
    
    # Additional constraints
    required_aspects: Dict[str, List[str]] = {}  # e.g., {'Jupiter': ['Sun', 'Venus']}
    excluded_aspects: Dict[str, List[str]] = {}
    
    # Search window
    offset_window_days: int = 15                 # Skip days after match
```

### DEFAULT_CONFIG Example

For Thiruppavai events (traditionally celebrated during Makara Rasi Sun + Full Moon):

```python
DEFAULT_CONFIG = SearchConfig(
    sun_rasi_range=(270.0, 300.0),  # Sun in Makara (tropical ~285°-315°)
    target_tithi=14,                 # Full Moon (Purnima)
    tithi_window=1,                  # +/- 1 tithi
    require_vj_alignment=True,       # Venus-Jupiter conjunction
    vj_tolerance_degrees=5.0,        # Within 5 degrees
    vj_altitude_above_horizon=0.0,   # Above horizon
    offset_window_days=15             # Skip 15 days after finding match
)
```

### Location Configuration

Predefined locations with Latitude/Longitude:

```python
LOCATIONS = {
    'Ujjain': {'lat': 23.1765, 'lon': 75.0},           # Ancient observatory
    'Srivilliputur': {'lat': 9.5236, 'lon': 77.9572},  # Tamil Nadu
    'Srirangam': {'lat': 10.8665, 'lon': 78.6867},     # Tamil Nadu
    'Cuddalore': {'lat': 11.7445, 'lon': 79.7645},     # Tamil Nadu
    'Chennai': {'lat': 13.0827, 'lon': 80.2707}        # Tamil Nadu
}
```

---

## Usage

### 1. **Installation**

```bash
pip install -r requirements.txt
```

Required packages:
- `skyfield`: Planetary position calculations
- `numpy`: Numerical computations
- `jplephem`: DE441 ephemeris interface
- `matplotlib`: Visualization
- `pandas`: Data handling

### 2. **Running the Scanner**

No-args shows help. To run with defaults, pass a simple flag like `--quiet`:

```bash
python ThiruppavaiDating.py --quiet
```

**Configuration in code:**
- `START_YEAR`: -6000 (6000 BC)
- `END_YEAR`: 2100
- `ACTIVE_LOCATION`: 'Srivilliputur' (change to any key in LOCATIONS)
- `DEFAULT_CONFIG`: SearchConfig with event criteria

**Output:**
- `results_-6000_2100_enhanced.csv`: Results file
- Console output showing progress and summary

### 3. **Creating Visualizations**

**From Python:**
```python
from visualize_event import visualize_event, visualize_multiple_events

# Single event
visualize_event(event_dict, location="Srivilliputur", 
                output_file="event1.png")

# Multiple events from CSV
visualize_multiple_events("results_-6000_2100_enhanced.csv", 
                         num_events=5, location="Srivilliputur")
```

**From command line:**
```bash
python visualize_event.py results_-6000_2100_enhanced.csv 5
```

### 4. **Customizing Search Criteria**

Create custom SearchConfig:

```python
from ThiruppavaiDating import SearchConfig

# Search for Mars-Venus conjunction during Dhanu Rasi Sun
custom_config = SearchConfig(
    sun_rasi_range=(240.0, 270.0),              # Dhanu (Sagittarius)
    target_tithi=None,                          # Any Tithi
    require_vj_alignment=False,                 # Don't require V-J
    required_aspects={                          # Require Mars-Venus aspect
        'Mars': ['Venus']
    },
    offset_window_days=20
)
```

Then modify main() to use custom_config instead of DEFAULT_CONFIG.

---

## Understanding Output

### CSV Columns Explained

| Column | Meaning | Example | Notes |
|--------|---------|---------|-------|
| Date | Gregorian/Julian date | "2320 BC-01-17" | Format: "YYYY BC/AD-MM-DD" |
| JD | Julian Day number | 1543211.25 | For precise calculations |
| Sun_Longitude | Sun's sidereal position | 285.42 | Degrees (0-360) |
| Sun_Rasi | Zodiacal sign | "Makara (Cp)" | 12 possible values |
| Sun_Nakshatra | Lunar mansion | "Shravana" | 27 possible values |
| Moon_Longitude | Moon's sidereal position | 287.15 | Degrees (0-360) |
| Moon_Rasi | Moon's zodiacal sign | "Makara (Cp)" | |
| Moon_Nakshatra | Moon's lunar mansion | "Dhanishta" | |
| Tithi | Lunar day name | "Purnima (Full Moon)" | 30 possible values |
| Tithi_Index | Tithi number | 14 | 0-29 (14=Full Moon) |
| Tithi_Progress | Tithi completion % | 78.5 | Percentage through current tithi |
| Venus_Longitude | Venus position | 282.33 | Degrees (0-360) |
| Jupiter_Longitude | Jupiter position | 283.67 | Degrees (0-360) |
| VJ_Separation | Venus-Jupiter gap | 1.34 | Degrees between planets |

### Interpreting Results

**Auspicious Indicators:**
- Moon near Full Moon (Tithi 14-16)
- Sun in Makara (associated with Hindu festivals)
- Venus-Jupiter conjunction (Mahalakshmi Yoga)
- Moon in auspicious Nakshatras (Ashwini, Rohini, Mrigashirsha, etc.)

**Example Matching Event:**
```
Date: 3102 BC-01-23
Sun: Makara Rasi (285.2°), Shravana Nakshatra
Moon: Makara Rasi (287.5°), Dhanishta Nakshatra
Tithi: Purnima (Full Moon), 92.3% complete
Venus-Jupiter: Separation 2.1° (conjunction)
```

---

## Mathematical Details

### Tithi Calculation

Given sidereal Moon and Sun longitudes:

```
separation = (moon_longitude - sun_longitude) % 360
tithi_size = 360 / 30 = 12 degrees
tithi_index = int(separation / tithi_size)
tithi_progress_percent = ((separation - tithi_start) / tithi_size) * 100
```

**Example:**
- Sun at 280°, Moon at 292°
- Separation = (292 - 280) % 360 = 12°
- Tithi_index = 12 / 12 = 1 (Shukla Dwitiya, 2nd waxing day)
- At start of tithi (100% = full tithi, 0% = just started)

### Nakshatra Calculation

```
nakshatra_size = 360 / 27 ≈ 13.333 degrees
nakshatra_index = int(longitude / nakshatra_size)
start_degree = nakshatra_index * nakshatra_size
end_degree = start_degree + nakshatra_size
```

**Example:**
- Moon at 126°
- Nakshatra = int(126 / 13.333) = 9
- NAKSHATRAS[9] = "Magha"
- Range: 120° - 133.33°

### Sidereal Position Calculation

```
tropical_longitude = ecliptic latitude from ephemeris
ayanamsa = get_lahiri_ayanamsa(time)
sidereal_longitude = (tropical_longitude - ayanamsa) % 360
```

The Lahiri Ayanamsa is calculated as:
```
days_since_j2000 = time.tt - 2451545.0
ayanamsa_arcsec = 23857 + (days_since_j2000 * 50.27)
ayanamsa_degrees = ayanamsa_arcsec / 3600.0
```

---

## Validation & Testing

### Validating Against Known Dates

To verify the system:

1. **Use historical dates with documented astronomical events**
   - Example: Solar eclipses, planetary conjunctions documented in ancient texts
   - Compare with historical astronomical records

2. **Cross-reference with academic sources**
   - K.V. Sarma's work on Indian astronomy
   - NASA JPL's ephemeris data
   - Published papers on Vedic chronology

3. **Test against specific text descriptions**
   - Identify textual descriptions of events
   - Search for matching conditions
   - Compare results with scholarly interpretations

### Sample Validation

For Thiruppavai (Tamil devotional text), known to celebrate:
- Full Moon (Purnima) in Makara Rasi
- After Sun's transition to Makara (Dec 21 - Jan 20 in tropical calendar)
- At specific Tamil Nadu location

---

## Limitations & Future Enhancements

### Current Limitations

1. **Simplified Yoga calculations** - Only basic yogas implemented
2. **No Dasha calculations** - Could add Mahadasha/Antardasha periods
3. **No Muhurta analysis** - Could add detailed auspicious timing
4. **Basic altitude checks** - Could improve rise/set detection
5. **No retrograde calculations** - Could add apparent retrograde motion

### Future Enhancements

1. **Advanced Yogas** - More comprehensive combination detection
2. **Dasha Periods** - Vimshottari, Ashtottari, Narayana Dasha
3. **House Analysis** - Bhava (house) calculations for specific locations
4. **Dignities** - Sthana Bala, Kendra Bala, Hora Bala
5. **Parallax correction** - For precise geocentric positions
6. **Conjunctive events** - Lunar/solar eclipse predictions
7. **Comparative analysis** - Match multiple text descriptions simultaneously
8. **Statistics** - Frequency analysis of event occurrences

---

## References

### Academic Sources

1. **Vedic Astronomy:**
   - K.V. Sarma - "Indian Astronomy: A Source-Book"
   - Aryabhata - "Aryabhatiya" (classical treatise)
   
2. **Jyotish Astrology:**
   - Parasara - "Brihat Parasara Hora Shastra" (classical text)
   - BPHS translations and commentaries
   
3. **Computational Methods:**
   - Meeus, Jean - "Astronomical Algorithms"
   - Explanatory Supplement to the Astronomical Almanac

4. **Software References:**
   - Skyfield documentation: https://rhodesmill.org/skyfield/
   - NASA JPL SPICE: https://naif.jpl.nasa.gov/naif/

### Related Tools

- **Stellarium:** Desktop planetarium software
- **SOLEX:** Astronomical position calculator
- **Jyotish software:** Parashara's Light, Jupiter
- **Online tools:** Astro-Seek, AstroDatabank

---

## Author & License

Developed for astronomical research into ancient Indian texts and Vedic chronology.

**Contact:** For questions, suggestions, or contributions, please refer to the project repository.

---

## Appendix: Quick Reference

### Nakshatra Names & Positions

```
0°:     Ashwini    (0°-13.33°)      - Ketu
13.33°: Bharani    (13.33°-26.67°)  - Venus
26.67°: Krittika   (26.67°-40°)     - Sun
...
346.67°: Revati    (346.67°-360°)   - Mercury
```

### Rasi Names & Positions

```
0°:   Mesha    (Aries)      0°-30°
30°:  Vrishabha (Taurus)    30°-60°
60°:  Mithuna   (Gemini)    60°-90°
90°:  Karka     (Cancer)    90°-120°
120°: Simha     (Leo)       120°-150°
150°: Kanya     (Virgo)     150°-180°
180°: Tula      (Libra)     180°-210°
210°: Vrishchika(Scorpio)   210°-240°
240°: Dhanu     (Sagittarius)240°-270°
270°: Makara    (Capricorn) 270°-300°
300°: Kumbha    (Aquarius)  300°-330°
330°: Meena     (Pisces)    330°-360°
```

### Tithi Progression Chart

```
0°-12°:     Shukla 1   (Waxing New Moon → 1st day)
12°-24°:    Shukla 2   (2nd day waxing)
...
156°-168°:  Shukla 14  (Almost Full Moon)
168°-180°:  Purnima    (Full Moon, Tithi 15)
180°-192°:  Krishna 1  (Waning 1st day)
...
348°-360°:  Amavasya   (New Moon, Tithi 30)
```

---

*Last Updated: January 2026*

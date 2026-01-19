# Thiruppavai Dating System

## Overview

A sophisticated astronomical dating program designed to identify celestial events described in ancient Indian texts (such as the Ramayana, Mahabharata, and Thiruppavai) using precise **Vedic/Jyotish astronomy calculations**.

This system combines:
- 🌍 **Precise ephemeris calculations** (NASA DE441 SPICE kernels)
- 🔭 **Vedic astronomy principles** (Lahiri Ayanamsa, sidereal calculations)
- 📚 **Indian astronomical concepts** (Nakshatras, Tithis, Rasis, Yogas)
- ⚙️ **Configurable event detection** (match any combination of criteria)
- 🎨 **Sky visualization** (zodiacal wheels with planetary alignments)

---

## Features

### Core Calculations

✅ **Sidereal Coordinates** - Tropical-to-sidereal conversion using Lahiri Ayanamsa  
✅ **Nakshatra Positioning** - Identify which of 27 lunar mansions contains each planet  
✅ **Tithi Calculations** - Precise lunar day (0-30) based on Moon-Sun separation  
✅ **Rasi Identification** - Determine zodiacal signs (12 signs × 30° each)  
✅ **Planetary Aspects** - Detect conjunctions, oppositions, trines, squares  
✅ **Yoga Detection** - Identify auspicious combinations (Mahalakshmi, etc.)  

### Search & Analysis

✅ **Configurable Criteria** - Build custom event definitions without code changes  
✅ **Multi-Parameter Matching** - Combine Sun sign, Moon phase, Nakshatras, aspects  
✅ **Date Range Scanning** - Search 6000 BC to 2100 AD (or any custom range)  
✅ **Parallel Processing** - Multi-core scanning for faster results  
✅ **Duplicate Detection** - Automatic deduplication of repeated events  

### Output & Visualization

✅ **CSV Export** - Complete data with 17+ astronomical parameters  
✅ **Zodiacal Wheel Visualization** - Shows planets, nakshatras, aspects, elements  
✅ **Batch Visualization** - Generate charts for multiple events  
✅ **Horoscope Generation** - South Indian & North Indian style birth charts  
✅ **Event Details** - Date, Tithi, Moon Nakshatra, planetary positions  

### Command-Line Interface

✅ **Professional CLI** - Control all parameters from command line  
✅ **20+ Arguments** - Fine-grained control over search criteria  
✅ **Configuration Persistence** - Save/load search configurations as JSON  
✅ **Batch Processing** - Run multiple searches sequentially  
✅ **Location Support** - 5 predefined locations + custom coordinates  

---

## Quick Start

### 1️⃣ Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Verify ephemeris files present
ls -lh de441_part-*.bsp
```

### 2️⃣ View Available Options

```bash
python3 ThiruppavaiDating.py --help
```

### 3️⃣ Run Scanner with Default Settings

No-args now shows help. To run with defaults, pass a simple flag like `--quiet`:

```bash
python3 ThiruppavaiDating.py --quiet
```

**Output:** `results_-6000_-5990_enhanced.csv` with matched events

### 4️⃣ Run with Custom Parameters

```bash
# Search 100-year range from Ujjain, full moon only
python3 ThiruppavaiDating.py --year-range -4000 -3900 --location Ujjain --tithi 14

# Generate visualizations and horoscope charts
python3 ThiruppavaiDating.py --visualize --generate-horoscopes --chart-style south_indian

# Custom location with horoscopes
python3 ThiruppavaiDating.py --latitude 28.75 --longitude 77.12 --generate-horoscopes
```

### 5️⃣ Visualize Results

```bash
python3 visualize_event.py results_-4000_-3900_enhanced.csv 5
```

**Output:** `visualization_<date>.png` files (zodiacal wheels)

### 6️⃣ For Detailed CLI Documentation

See [CLI_USAGE_GUIDE.md](CLI_USAGE_GUIDE.md) for complete command reference and examples.

---

## File Structure

```
dating-of-thiruppavai/
├── ThiruppavaiDating.py          # Main scanning engine
│   ├── SearchConfig class        # Configurable event criteria
│   ├── create_argument_parser()  # CLI argument setup
│   ├── parse_arguments()         # CLI argument parsing
│   ├── Helper functions          # Calculations (Tithi, Nakshatra, etc.)
│   ├── process_chunk_jyotish()   # Main scanner (parallelized)
│   └── Multiprocessing           # Parallel execution
│
├── horoscope.py                  # Horoscope chart generation (NEW)
│   ├── HoroscopeChart base class # House calculations & planet placement
│   ├── SouthIndianChart class    # Square grid chart style
│   ├── NorthIndianChart class    # Diamond chart style
│   └── generate_horoscope()      # Main entry point
│
├── visualize_event.py            # Visualization module
│   ├── ZodiacalWheel class       # Zodiacal wheel visualization
│   ├── visualize_event()         # Single event visualization
│   └── visualize_multiple_events()  # Batch visualization
│
├── CLI_USAGE_GUIDE.md            # Complete CLI reference (NEW)
├── DOCUMENTATION.md              # Complete technical documentation
├── QUICKSTART.md                 # Setup & usage guide
├── README.md                     # This file
├── requirements.txt              # Python dependencies
│
└── de441_part-*.bsp             # Ephemeris data files
    ├── de441_part-1.bsp         # BC dates (~310 MB)
    └── de441_part-2.bsp         # AD dates (~310 MB)
```

---

## Basic Horoscope Reading (Intro)

You can get a quick, intro-level reading from Python using the new helper in `horoscope.py`:

```python
from horoscope import basic_horoscope_reading

reading, data = basic_horoscope_reading(
    birth_dt="1990-01-01T12:34:00",  # local time
    latitude=13.0827,                 # Chennai
    longitude=80.2707,
    timezone="Asia/Kolkata",
    generate_chart=True,              # optional: create birth chart PNG
    chart_style='south_indian',       # or 'north_indian'
)

print(reading)
# Outputs all planets: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn
# Plus Rahu/Ketu with their nakshatras and a brief Moon Nakshatra insight
```

Or from the command line:
```bash
python3 ThiruppavaiDating.py \
  --read-horoscope \
  --birth-dt 1990-01-01T12:34:00 \
  --birth-lat 13.0827 \
  --birth-lon 80.2707 \
  --birth-tz Asia/Kolkata \
  --birth-chart
```

This reports sidereal positions for all classical planets, Moon Nakshatra, and Rahu/Ketu placements (mean node). It's a starting point you can extend with house placements and aspects.

---

## Configuration

### Search Parameters

Edit `SearchConfig` in `ThiruppavaiDating.py`:

```python
config = SearchConfig(
    # Sun position (degrees, 0-360 sidereal)
    sun_rasi_range=(270.0, 300.0),  # Makara (Capricorn)
    
    # Moon phase (0-29, 14=Full Moon, 29=New Moon)
    target_tithi=14,                 # Full Moon
    tithi_window=1,                  # ±1 tithi tolerance
    
    # Nakshatras (lunar mansions)
    target_nakshatras=[],            # Empty = any, or [0,1,2] etc.
    
    # Planetary aspects
    require_vj_alignment=True,       # Venus-Jupiter
    vj_tolerance_degrees=5.0,        # Maximum separation
    
    # Search parameters
    offset_window_days=15            # Skip days after finding match
)
```

### Observation Location

```python
ACTIVE_LOCATION = 'Srivilliputur'  # Change to any key in LOCATIONS dict

# Or add custom location
LOCATIONS['MyCity'] = {
    'lat': 12.9716,
    'lon': 77.5946,
    'name': 'Bangalore, India'
}
```

### Date Range

```python
# Modify for faster testing
chunks = [(START_YEAR, START_YEAR + 100, config)]

# Or use default full range
chunks = [(y, y + CHUNK_SIZE_YEARS, config) 
          for y in range(START_YEAR, END_YEAR, CHUNK_SIZE_YEARS)]
```

---

## Understanding Results

### Key Columns in Output CSV

| Column | Meaning | Example |
|--------|---------|---------|
| Date | Event date | "2320 BC-01-17" |
| JD | Julian Day | 1543211.25 |
| Sun_Rasi | Zodiacal sign | "Makara (Cp)" |
| Sun_Nakshatra | Lunar mansion | "Shravana" |
| Moon_Rasi | Moon's sign | "Makara (Cp)" |
| Moon_Nakshatra | Moon's mansion | "Dhanishta" |
| Tithi | Lunar day | "Purnima (Full Moon)" |
| Tithi_Progress | % through tithi | 78.5 |
| Venus_Longitude | Position (degrees) | 282.33 |
| Jupiter_Longitude | Position (degrees) | 283.67 |
| VJ_Separation | Gap between planets | 1.34 |

### Interpreting Matches

**Highly significant events have:**
- ✓ Sun in expected Rasi
- ✓ Full Moon (Purnima) or New Moon (Amavasya)
- ✓ Moon in auspicious Nakshatra
- ✓ Venus-Jupiter conjunction
- ✓ Positive planetary aspects

**Example:** Event matching all criteria
```
Date:              2320 BC-01-23
Sun:               Makara (285.2°), Shravana Nakshatra
Moon:              Makara (287.5°), Dhanishta Nakshatra
Tithi:             Purnima (92% complete)
Venus-Jupiter Gap: 1.8°
↓
→ Likely match for Thiruppavai festival
```

---

## Vedic Astronomy Reference

### Nakshatras (27 Lunar Mansions)

Each spans 13°20' of the zodiac:

| # | Name | Ruling Planet | # | Name | Ruling Planet |
|---|------|---------------|---|------|---------------|
| 1 | Ashwini | Ketu | 15 | Svati | Rahu |
| 2 | Bharani | Venus | 16 | Visakha | Jupiter |
| 3 | Krittika | Sun | 17 | Anuradha | Saturn |
| 4 | Rohini | Moon | 18 | Jyeshtha | Mercury |
| ... | ... | ... | ... | ... | ... |

[See DOCUMENTATION.md for complete list]

### Tithis (30 Lunar Days)

Based on Moon-Sun separation:

| Range | Tithi | Phase | Notes |
|-------|-------|-------|-------|
| 0°-12° | Shukla 1 | Waxing 1st | After New Moon |
| 12°-24° | Shukla 2 | Waxing 2nd | |
| ... | ... | ... | ... |
| 168°-180° | **Purnima** | **Full Moon** | **Most auspicious** |
| 180°-192° | Krishna 1 | Waning 1st | After Full Moon |
| ... | ... | ... | ... |
| 348°-360° | **Amavasya** | **New Moon** | |

### Rasis (12 Zodiacal Signs)

Each spans 30°:

| # | Rasi | Western | Element |
|----|------|---------|---------|
| 1 | Mesha | Aries | Fire |
| 2 | Vrishabha | Taurus | Earth |
| 3 | Mithuna | Gemini | Air |
| 4 | Karka | Cancer | Water |
| 5 | Simha | Leo | Fire |
| 6 | Kanya | Virgo | Earth |
| 7 | Tula | Libra | Air |
| 8 | Vrishchika | Scorpio | Water |
| 9 | Dhanu | Sagittarius | Fire |
| 10 | **Makara** | **Capricorn** | **Earth** |
| 11 | Kumbha | Aquarius | Air |
| 12 | Meena | Pisces | Water |

---

## Mathematical Formulas

### Lahiri Ayanamsa (Precession Correction)

```
ayanamsa = 23°51'57" + (days_since_2000 × 50.27"/year)
sidereal_longitude = tropical_longitude - ayanamsa
```

### Tithi (Lunar Day)

```
separation = (moon_longitude - sun_longitude) mod 360°
tithi_index = floor(separation / 12°)
tithi_progress = ((separation - tithi_start) / 12°) × 100%
```

### Nakshatra

```
nakshatra_size = 360° / 27 = 13.333°
nakshatra_index = floor(longitude / 13.333°)
```

### Rasi (Zodiacal Sign)

```
rasi_index = floor(longitude / 30°)
degree_in_rasi = longitude mod 30°
```

---

## Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Single year scan | ~2 seconds | Single core |
| 10-year range | ~20 seconds | Single core |
| Full 8100-year range | 15-30 minutes | Multi-core (8 cores) |
| Visualization (1 event) | ~2 seconds | PNG generation |
| Batch visualization (5 events) | ~10 seconds | All visualizations |

**Tips for faster testing:**
```python
# Use smaller date range
chunks = [(START_YEAR, START_YEAR + 50, config)]

# Increase offset window (find fewer matches)
config.offset_window_days = 30
```

---

## Troubleshooting

### ❌ "Ephemeris files not found"
→ Download from https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/

### ❌ "ModuleNotFoundError: No module named 'skyfield'"
→ Run `pip install -r requirements.txt`

### ❌ No results found
→ Verify criteria are not too restrictive; try `require_vj_alignment=False`

### ❌ Slow performance
→ Reduce date range or increase `offset_window_days` (skip more days)

See QUICKSTART.md for more troubleshooting tips.

---

## Documentation

- **QUICKSTART.md** - Installation, running, and basic usage (5 min read)
- **DOCUMENTATION.md** - Complete technical reference (30 min read)
- **Code comments** - Detailed explanations in Python files

---

## Validation

To verify accuracy:

1. ✓ Cross-check results with NASA JPL ephemeris data
2. ✓ Compare with known historical astronomical events
3. ✓ Validate against published scholarly works on Vedic chronology
4. ✓ Test against text descriptions of specific events

---

## References

### Academic Sources
- K.V. Sarma - "Indian Astronomy: A Source-Book"
- Parasara - "Brihat Parasara Hora Shastra" (classical Jyotish text)
- Meeus, Jean - "Astronomical Algorithms"

### Software
- Skyfield - Astronomical calculations
- NASA JPL SPICE - Ephemeris kernels
- Matplotlib - Visualization

---

## Project Status

✅ Core calculations implemented  
✅ Configurable search criteria  
✅ Sky visualization  
✅ CSV export  
✅ Documentation complete  

**Next phases (future work):**
- Advanced Yoga combinations
- Dasha period calculations
- Lunar/solar eclipse predictions
- Web interface

---

## License & Attribution

Developed for astronomical research into ancient Indian texts and Vedic chronology.

Uses:
- NASA JPL DE441 ephemeris kernels (public domain)
- Skyfield library (MIT License)
- Matplotlib (BSD License)

---

## Getting Help

1. 📖 Read **QUICKSTART.md** for setup issues
2. 📚 Check **DOCUMENTATION.md** for concept explanations
3. 💬 Review code comments for implementation details
4. 🔍 Verify ephemeris files are present and valid

---

**Start here:** [QUICKSTART.md](QUICKSTART.md)

**Learn more:** [DOCUMENTATION.md](DOCUMENTATION.md)

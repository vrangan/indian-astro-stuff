# CLI Usage Guide - Thiruppavai Dating System

## Overview

The Thiruppavai Dating System now provides a powerful command-line interface (CLI) for controlling all aspects of astronomical event detection and analysis. This guide covers all available options and typical use cases.

## Quick Start

### View All Options
```bash
python3 ThiruppavaiDating.py --help
```

### List Available Locations
```bash
python3 ThiruppavaiDating.py --list-locations
```

### No-Args Behavior
Running without arguments now shows help and exits.
```bash
python3 ThiruppavaiDating.py
```

### Run with Defaults
Use defaults by passing any non-conflicting flag, e.g. `--quiet`:
```bash
python3 ThiruppavaiDating.py --quiet
```
Scans from -6000 to -5990 from Srivilliputur, searching for full moons (tithi 14) with Venus-Jupiter alignment.

### Horoscope Reading (Intro)
Generate a quick reading for a birth datetime and place:
```bash
python3 ThiruppavaiDating.py \
  --read-horoscope \
  --birth-dt 1990-01-01T12:34:00 \
  --birth-lat 13.0827 \
  --birth-lon 80.2707 \
  --birth-tz Asia/Kolkata
```
Prints sidereal positions for all planets (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn), Rahu/Ketu with their nakshatras, and a brief Moon Nakshatra insight.

Add `--birth-chart` to also generate a birth chart PNG:
```bash
python3 ThiruppavaiDating.py \
  --read-horoscope \
  --birth-dt 1990-01-01T12:34:00 \
  --birth-lat 13.0827 \
  --birth-lon 80.2707 \
  --birth-tz Asia/Kolkata \
  --birth-chart
```

## Command-Line Arguments

### Date Range Options

#### `--year-range START END`
Specify the year range to scan.
- **Default:** -6000 to -5990
- **Example:** `--year-range -5000 -4990` (scan 10-year period)
- **Note:** Negative years are BCE, positive are CE

#### `--chunk-size SIZE`
Size of each processing chunk in years.
- **Default:** 20 years
- **Example:** `--chunk-size 50` (process 50-year chunks)
- **Impact:** Larger chunks = faster but more memory; smaller chunks = slower but memory-efficient

### Observer Location Options

#### `--location NAME`
Select a predefined location.
- **Available:** Ujjain, Srivilliputur, Srirangam, Cuddalore, Chennai
- **Default:** Srivilliputur
- **Example:** `--location Ujjain`

#### `--latitude LAT --longitude LON`
Specify custom observer location (overrides `--location`).
- **Format:** Decimal degrees (positive=North/East, negative=South/West)
- **Example:** `--latitude 28.75 --longitude 77.12` (New Delhi)

### Sun Position Criteria

#### `--sun-rasi-range START END`
Sun's longitude range (0-360°).
- **Default:** 270-300° (Makara/Capricorn in sidereal zodiac)
- **Examples:**
  - `--sun-rasi-range 0 30` (Aries)
  - `--sun-rasi-range 120 150` (Leo)
  - `--sun-rasi-range 240 270` (Sagittarius)

#### `--any-sun-rasi`
Ignore sun position criteria (match any sun position).
- **Flag:** No value needed
- **Example:** `--any-sun-rasi`

### Moon Phase Criteria

#### `--tithi TITHI`
Target lunar day (0-29 in Vedic calendar).
- **Default:** 14 (Full Moon)
- **Common values:**
  - 0, 30: New Moon (conjunction)
  - 14: Full Moon (opposition)
  - 7: Waxing Moon Quarter
  - 22: Waning Moon Quarter
- **Example:** `--tithi 0` (search for New Moons)

#### `--tithi-window WINDOW`
Tithi tolerance (±days).
- **Default:** 1 day
- **Example:** `--tithi-window 2` (allows ±2 days from target tithi)

#### `--any-tithi`
Ignore tithi criteria (match any lunar day).
- **Flag:** No value needed

### Nakshatra Criteria

#### `--nakshatras INDEX [INDEX ...]`
Target nakshatra(s) by index (0-26).
- **Nakshatras:**
  - 0: Ashwini, 1: Bharani, 2: Krittika, 3: Rohini, 4: Mrigashira, 5: Ardra
  - 6: Punarvasu, 7: Pushya, 8: Aslesha, 9: Magha, 10: Purva Phalguni, 11: Uttara Phalguni
  - 12: Hasta, 13: Chitra, 14: Svati, 15: Vishakha, 16: Anuradha, 17: Jyeshtha
  - 18: Mula, 19: Purva Ashadha, 20: Uttara Ashadha, 21: Shravana, 22: Dhanishta, 23: Shatabhisha
  - 24: Purva Bhadrapada, 25: Uttara Bhadrapada, 26: Revati
- **Example:** `--nakshatras 0 1 2` (Ashwini, Bharani, Krittika)

#### `--any-nakshatra`
Ignore nakshatra criteria.

### Planetary Aspects

#### `--vj-only`
Require Venus-Jupiter alignment (default: True).
- **Flag:** Already enabled by default
- **Note:** Use `--no-vj` to disable

#### `--no-vj`
Disable Venus-Jupiter alignment requirement.
- **Flag:** No value needed
- **Example:** `--no-vj` (search without V-J alignment)

#### `--vj-tolerance DEGREES`
Venus-Jupiter maximum separation.
- **Default:** 5.0°
- **Example:** `--vj-tolerance 3.0` (require within 3° separation)

#### `--vj-altitude DEGREES`
Minimum altitude above horizon for both planets.
- **Default:** 0° (at or above horizon)
- **Example:** `--vj-altitude 10.0` (planets must be at least 10° above horizon)

### Output Options

#### `--output FILENAME`
Specify output CSV filename.
- **Default:** `results_<START>_<END>_enhanced.csv`
- **Example:** `--output my_results.csv`

#### `--visualize`
Generate zodiacal wheel visualizations for matched events.
- **Flag:** No value needed
- **Output:** PNG files for each visualized event
- **Requirement:** matplotlib must be installed

#### `--num-visualizations N`
Number of events to visualize (if --visualize enabled).
- **Default:** 5
- **Example:** `--num-visualizations 10`

#### `--generate-horoscopes`
Generate horoscope birth charts for matched events.
- **Flag:** No value needed
- **Output:** PNG files in selected chart style

#### `--chart-style STYLE`
Horoscope chart style.
- **Options:** `south_indian`, `north_indian`
- **Default:** `south_indian`
- **South Indian:** Square grid with 12 houses arranged in specific pattern
- **North Indian:** Diamond shape with houses at vertices
- **Example:** `--chart-style north_indian`

### Processing Options

#### `--offset-window DAYS`
Days to skip after finding a match (prevents duplicate nearby events).
- **Default:** 15 days
- **Example:** `--offset-window 30`

#### `--cores N`
Number of CPU cores to use for parallel processing.
- **Default:** Auto-detected
- **Example:** `--cores 4`

#### `--verbose` or `-v`
Enable verbose output with additional details.
- **Flag:** No value needed

#### `--quiet` or `-q`
Minimal output (suppress banner and progress information).
- **Flag:** No value needed

### Configuration Options

#### `--save-config FILENAME`
Save current configuration to JSON file for later reuse.
- **Example:** `--save-config my_search.json`
- **Output:** JSON file with all search parameters

#### `--load-config FILENAME`
Load configuration from previously saved JSON file.
- **Example:** `--load-config my_search.json`
- **Overrides:** Most command-line arguments (use carefully)

## Common Use Cases

### 1. Basic Full Moon Search (Default)
```bash
python3 ThiruppavaiDating.py
```
Searches for full moons with Venus-Jupiter alignment from -6000 to -5990.

### 2. Search Specific Location
```bash
python3 ThiruppavaiDating.py --location Ujjain --year-range -4000 -3900
```
Scans 100 years from ancient Ujjain (astronomical center).

### 3. Custom Coordinates
```bash
python3 ThiruppavaiDating.py --latitude 28.75 --longitude 77.12 --year-range -3000 -2900
```
Uses custom coordinates (e.g., New Delhi area).

### 4. Search New Moons
```bash
python3 ThiruppavaiDating.py --tithi 0 --tithi-window 1
```
Finds New Moons (conjunction) with ±1 day tolerance.

### 5. Any Moon Phase (No V-J Required)
```bash
python3 ThiruppavaiDating.py --no-vj --any-tithi --year-range -6000 -5500
```
Searches for any lunar configuration without Venus-Jupiter requirement.

### 6. Specific Nakshatras
```bash
python3 ThiruppavaiDating.py --nakshatras 0 1 2 --tithi 14
```
Finds full moons in Ashwini, Bharani, or Krittika nakshatras.

### 7. Generate Visualizations
```bash
python3 ThiruppavaiDating.py --year-range -3000 -2900 --visualize --num-visualizations 10
```
Scan 100 years and create zodiacal wheel visualizations for first 10 matches.

### 8. Generate Horoscope Charts
```bash
python3 ThiruppavaiDating.py --year-range -2000 -1900 --generate-horoscopes --chart-style south_indian
```
Creates South Indian style birth charts for matched events.

### 9. Mixed Analysis (Everything)
```bash
python3 ThiruppavaiDating.py \
  --year-range -4000 -3900 \
  --location Ujjain \
  --tithi 14 \
  --vj-tolerance 3.0 \
  --visualize --num-visualizations 5 \
  --generate-horoscopes --chart-style north_indian \
  --output ancient_ujjain_events.csv
```
Complete analysis with all features enabled.

### 10. Save Configuration for Reuse
```bash
python3 ThiruppavaiDating.py \
  --year-range -3000 -2900 \
  --location Srirangam \
  --tithi 14 \
  --vj-tolerance 4.0 \
  --save-config srirangam_config.json
```
Save search parameters for repeating later.

### 11. Load and Run Previous Configuration
```bash
python3 ThiruppavaiDating.py --load-config srirangam_config.json
```
Uses all parameters from saved configuration.

### 12. Verbose Mode for Debugging
```bash
python3 ThiruppavaiDating.py -v --year-range -2000 -1999
```
Detailed output for troubleshooting.

## Output Files

### CSV Results File
Contains detected astronomical events with these columns:
- **Date:** ISO format date and time
- **JD:** Julian Day number
- **Sun_Rasi:** Sun's zodiacal sign
- **Sun_Longitude:** Sun's sidereal longitude
- **Sun_Nakshatra:** Moon's lunar mansion
- **Moon_Rasi:** Moon's zodiacal sign
- **Moon_Longitude:** Moon's sidereal longitude
- **Moon_Nakshatra:** Moon's lunar mansion
- **Tithi:** Lunar day (0-29)
- **Tithi_Progress:** Percentage through current lunar day
- **VJ_Separation:** Venus-Jupiter separation in degrees
- **Altitude_V/J:** Above horizon altitude for each planet
- Plus additional calculated fields

### Visualization Files
- **Format:** PNG images at 300 DPI
- **Naming:** `visualization_<date>.png`
- **Contents:** Zodiacal wheel with Rasis, Nakshatras, planets, and aspects

### Horoscope Charts
- **Format:** PNG images at 300 DPI
- **Naming:** `horoscope_<chart_style>_<date>.png`
- **South Indian:** Square grid format (12-1-2-3 / 11-X-X-4 / etc.)
- **North Indian:** Diamond format with houses at cardinal points

### Configuration Files (JSON)
- **Format:** JSON with all search parameters
- **Use:** `--load-config` to reuse in future runs
- **Example:** 
```json
{
  "year_range": [-3000, -2900],
  "location": "Srirangam",
  "tithi": 14,
  "vj_tolerance": 4.0,
  "chart_style": "south_indian"
}
```

## Tips and Tricks

### 1. Large Year Ranges
For very large year ranges (e.g., -10000 to 0), use larger `--chunk-size`:
```bash
python3 ThiruppavaiDating.py --year-range -10000 0 --chunk-size 100
```

### 2. Faster Processing
Disable visualization generation and increase cores:
```bash
python3 ThiruppavaiDating.py --cores 8 --quiet
```

### 3. Two-Stage Processing
First find events with minimal criteria:
```bash
python3 ThiruppavaiDating.py --any-tithi --no-vj -q --output candidates.csv
```
Then visualize the most promising results:
```bash
python3 ThiruppavaiDating.py --year-range -3000 -2500 --visualize
```

### 4. Batch Processing with Config Files
Create multiple config files for different searches, then run sequentially:
```bash
for config in *.json; do
  echo "Processing $config..."
  python3 ThiruppavaiDating.py --load-config "$config"
done
```

### 5. Export Summary
Redirect output to a log file:
```bash
python3 ThiruppavaiDating.py --verbose > scan_log.txt 2>&1
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'skyfield'"
Install dependencies:
```bash
pip install -r requirements.txt --break-system-packages
```

### "Ephemeris files not found"
Ensure DE441 SPICE kernel files are present:
- `de441_part-1.bsp`
- `de441_part-2.bsp`

### "No events found matching the criteria"
Relax search constraints:
- Increase `--tithi-window`
- Remove `--vj-only` requirement
- Use `--any-nakshatra`
- Check location coordinates

### Slow Performance
- Reduce year range (use smaller `--year-range`)
- Increase `--cores` (if CPU available)
- Disable `--visualize` and `--generate-horoscopes`
- Use `--quiet` (reduces I/O)

### Memory Issues
- Reduce `--chunk-size`
- Reduce number of `--num-visualizations`
- Process smaller year ranges

## Advanced Configuration

### Creating a Default Configuration File
Create `default_config.json`:
```json
{
  "year_range": [-6000, -5990],
  "location": "Srivilliputur",
  "sun_rasi_range": [270, 300],
  "tithi": 14,
  "tithi_window": 1,
  "vj_only": true,
  "vj_tolerance": 5.0,
  "chart_style": "south_indian"
}
```

Then use:
```bash
python3 ThiruppavaiDating.py --load-config default_config.json
```

## Getting Help

### View Full Help
```bash
python3 ThiruppavaiDating.py --help
```

### List All Locations
```bash
python3 ThiruppavaiDating.py --list-locations
```

### Check Version and Status
```bash
python3 -c "from ThiruppavaiDating import __version__; print(__version__)" 2>/dev/null || echo "CLI ready"
```

## Performance Characteristics

| Operation | Time (approx) | Memory | Cores |
|-----------|--------------|--------|-------|
| 10-year scan, 1 location | 2-5 sec | 100 MB | 1 |
| 100-year scan, 8 cores | 5-10 sec | 200 MB | 8 |
| Generate 5 visualizations | 3-5 sec | 50 MB | 1 |
| Generate 5 horoscopes | 2-3 sec | 30 MB | 1 |

---

**Last Updated:** 2024  
**Thiruppavai Dating System - CLI v1.0**

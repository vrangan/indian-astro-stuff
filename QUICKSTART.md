# Quick Start Guide - Thiruppavai Dating System

## Installation (2 minutes)

```bash
# Navigate to project directory
cd /home/venkat/my-repos/dating-of-thiruppavai

# Install dependencies
pip install -r requirements.txt

# Verify DE441 ephemeris files are present
ls -lh de441_part-*.bsp
```

**Files needed:**
- `de441_part-1.bsp` (~310 MB) - BC dates
- `de441_part-2.bsp` (~310 MB) - AD dates

## Running a Scan (5-30 minutes depending on range)

No-args shows help. To run with defaults, pass a simple flag like `--quiet`:

```bash
python ThiruppavaiDating.py --quiet
```

**What happens (with defaults):**
1. Loads ephemeris data
2. Iterates through date range (-6000 to 2100 by default)
3. Evaluates search criteria (Sun sign, Moon phase, Nakshatras, planetary aspects)
4. Exports matches to CSV
5. Displays summary with sample results

**Output files:**
- `results_-6000_2100_enhanced.csv` - Full results table

## Visualizing Results (1-2 minutes)

### Generate visualizations for top 5 events:

```bash
python visualize_event.py results_-6000_2100_enhanced.csv 5
```

**Output:**
- `visualization_<date>.png` (one per event)
- Shows zodiacal wheel with planets, aspects, nakshatras

### Or from Python:

```python
from visualize_event import visualize_multiple_events

files = visualize_multiple_events(
    "results_-6000_2100_enhanced.csv",
    num_events=3,
    location="Srivilliputur"
)
print(f"Generated: {files}")
```

## Customizing Search Criteria

Edit `ThiruppavaiDating.py` and modify `DEFAULT_CONFIG`:

```python
# For different event type
custom_config = SearchConfig(
    # Search for events when Sun is in Aries (tropical ~0-30°, sidereal ~334-4°)
    sun_rasi_range=(334.0, 4.0),
    
    # Require New Moon instead of Full Moon
    target_tithi=29,  # 29 = Amavasya (New Moon)
    tithi_window=1,
    
    # Don't require Venus-Jupiter alignment
    require_vj_alignment=False,
    
    # Require Mars-Venus conjunction
    required_aspects={'Mars': ['Venus']},
    
    # Skip 20 days after finding match
    offset_window_days=20
)

# Then in main(), pass custom_config to chunks:
chunks = [(y, y + CHUNK_SIZE_YEARS, custom_config) 
          for y in range(START_YEAR, END_YEAR, CHUNK_SIZE_YEARS)]
```

## Changing Observer Location

Edit `ThiruppavaiDating.py`:

```python
# Choose from predefined locations
ACTIVE_LOCATION = 'Ujjain'  # or 'Srivilliputur', 'Srirangam', etc.

# Or add new location
LOCATIONS['MyCity'] = {'lat': 12.9716, 'lon': 77.5946, 'name': 'Bangalore, India'}
ACTIVE_LOCATION = 'MyCity'

# Or hardcode
LOCATION_LAT = 12.9716
LOCATION_LON = 77.5946
```

## Adjusting Date Range

Edit `ThiruppavaiDating.py`:

```python
# Scan only 100 years (faster)
chunks = [(START_YEAR, START_YEAR + 100, config)]

# Or specific range
chunks = [(-3000, -2500, config)]  # 3000-2500 BC

# Or use original full range
chunks = [(y, y + CHUNK_SIZE_YEARS, config) 
          for y in range(START_YEAR, END_YEAR, CHUNK_SIZE_YEARS)]
```

## Understanding Output CSV

Key columns in `results_*_enhanced.csv`:

```
Date                   - Event date (format: "YYYY BC/AD-MM-DD")
Sun_Rasi              - Zodiacal sign (Mesha, Vrishabha, etc.)
Sun_Nakshatra         - Lunar mansion (27 options)
Moon_Rasi             - Moon's zodiacal sign
Moon_Nakshatra        - Moon's lunar mansion
Tithi                 - Lunar day (Purnima=Full Moon, Amavasya=New Moon)
Tithi_Progress        - % through current tithi (0-100%)
Venus_Longitude       - Venus position (degrees, 0-360)
Jupiter_Longitude     - Jupiter position
VJ_Separation         - Distance between Venus & Jupiter (degrees)
Mars_Longitude        - Mars position
Mercury_Longitude     - Mercury position
Saturn_Longitude      - Saturn position
```

## Interpreting Results

### Highly Significant Events (match multiple criteria):
- Sun in Makara (tropical ~285-315°, sidereal ~270-300°)
- Moon in Purnima (Full Moon, Tithi 14-16)
- Venus-Jupiter within 2-3°
- Moon in auspicious Nakshatras (Ashwini, Rohini, Krittika, Mrigashirsha)

### CSV Example:
```
2320 BC-01-23
Sun_Rasi: Makara (Cp)
Sun_Nakshatra: Shravana
Moon_Nakshatra: Dhanishta
Tithi: Purnima (92.3% complete)
VJ_Separation: 1.8°
```
↓
**Interpretation:** Full Moon, Sun in Makara, Venus-Jupiter conjunction
→ **Likely match** for Thiruppavai celebration dates

## Common Troubleshooting

### Error: "Ephemeris files not found"
```bash
# Check file presence
ls -lh de441_part-1.bsp de441_part-2.bsp

# Download if missing (from NASA JPL)
# https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/
```

### Error: "ModuleNotFoundError"
```bash
# Reinstall packages
pip install --upgrade -r requirements.txt
```

### Slow performance
```python
# Reduce date range for testing
chunks = [(START_YEAR, START_YEAR + 50, config)]  # Only 50 years

# Or reduce search window
config.offset_window_days = 30  # Skip more days to find fewer matches
```

### No results found
```python
# Verify search criteria are not too restrictive
DEFAULT_CONFIG = SearchConfig(
    sun_rasi_range=(270.0, 300.0),    # Check range is reasonable
    target_tithi=14,                  # Check tithi index is 0-29
    require_vj_alignment=False,       # Try disabling this first
)
```

## Performance Optimization

### For faster testing:
```python
# Reduce date range
chunks = [(START_YEAR, START_YEAR + 10, config)]

# Increase offset window (find fewer matches)
config.offset_window_days = 30

# Use single-core processing (for debugging)
# Comment out multiprocessing and test single chunk
results = process_chunk_jyotish((START_YEAR, START_YEAR + 10, config))
```

### For full scan:
```python
# Keep default multiprocessing
# Use all chunks
chunks = [(y, y + CHUNK_SIZE_YEARS, config) 
          for y in range(START_YEAR, END_YEAR, CHUNK_SIZE_YEARS)]

# This will use all CPU cores automatically
```

## Next Steps

1. **Review results:** Open CSV in Excel/Google Sheets
2. **Visualize events:** Generate zodiacal wheel images for matches
3. **Cross-reference:** Compare with known historical events or text descriptions
4. **Refine criteria:** Adjust SearchConfig based on initial results
5. **Validate:** Check matches against scholarly sources and astronomical records

## Detailed Documentation

For comprehensive documentation on:
- Vedic astronomy concepts
- Calculation methods
- Configuration options
- API reference

See: `DOCUMENTATION.md`

## Support

For issues or questions:
1. Check DOCUMENTATION.md for concept explanations
2. Review code comments in main files
3. Verify DE441 ephemeris files are present
4. Test with smaller date range first

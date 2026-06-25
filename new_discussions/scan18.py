import matplotlib.pyplot as plt
import numpy as np
import csv
import re
from skyfield.api import load, wgs84, Star
from skyfield.framelib import ecliptic_frame
from skyfield import almanac  
from skyfield.almanac import find_discrete, sunrise_sunset
from datetime import timedelta

# ==========================================
# 1. CONFIGURATION & GEOGRAPHIC ANCHOR
# ==========================================
EPHEMERIS_FILE = 'de431_part-2.bsp' 
SRIVILLIPUTHUR = wgs84.latlon(9.5161, 77.6284)
START_YEAR = 1
END_YEAR = 1000

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

# Major Chronological Anchors (Hipparcos Star Identifiers cross-mapped to Vedic tradition)
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

# ==========================================
# 2. AYANAMSA, RASI & METRIC CONVERTERS
# ==========================================
def get_lahiri_ayanamsa(t):
    j2000 = 2451545.0
    days = t.tt - j2000
    return 23.85 + (days / 365.25) * (50.29 / 3600.0)

def get_sidereal_lon(observer, body, t):
    apparent = observer.at(t).observe(body).apparent()
    lat, lon, dist = apparent.frame_latlon(ecliptic_frame)
    return (lon.degrees - get_lahiri_ayanamsa(t)) % 360

def get_rasi_name(lon_degrees):
    return RASI_NAMES[int(lon_degrees // 30)]

def get_nakshatra_name(lon_degrees):
    nakshatra_index = int(lon_degrees // (360.0 / 27.0))
    return NAKSHATRA_NAMES[nakshatra_index]

# ==========================================
# 3. TRANSIT SCAN LOGIC ENGINE
# ==========================================
def scan_for_thiruppavai_date(eph, ts):
    print(f"Scanning {START_YEAR}-{END_YEAR} AD using {EPHEMERIS_FILE}...")
    
    sun = eph['sun']
    jupiter = eph['jupiter barycenter'] 
    venus = eph['venus']
    earth = eph['earth']
    observer = earth + SRIVILLIPUTHUR
    
    candidates = []
    
    for year in range(START_YEAR, END_YEAR + 1):
        t_start = ts.utc(year, 12, 1)
        t_end = ts.utc(year + 1, 1, 30)
        
        t_phases, phases = find_discrete(t_start, t_end, almanac.moon_phases(eph))
        
        for t_moon, phase in zip(t_phases, phases):
            if phase == 2:  # Full Moon Axis
                sun_lon = get_sidereal_lon(observer, sun, t_moon)
                
                if 240 <= sun_lon < 270:
                    t_target = t_moon + timedelta(days=12)
                    t_rise_start = t_target - timedelta(hours=12)
                    t_rise_end = t_target + timedelta(hours=12)
                    t_sunrises, _ = find_discrete(t_rise_start, t_rise_end, sunrise_sunset(eph, SRIVILLIPUTHUR))
                    
                    if len(t_sunrises) == 0: continue
                    t_sunrise = t_sunrises
                    
                    t_check = t_sunrise - timedelta(minutes=30)
                    obs = observer.at(t_check)
                    alt_v, _, _ = obs.observe(venus).apparent().altaz()
                    alt_j, _, _ = obs.observe(jupiter).apparent().altaz()
                    
                    if alt_v.degrees > 0 and -5 < alt_j.degrees < 15:
                        candidates.append((t_sunrise, t_moon))
                        print(f"Found Match: {t_sunrise.utc_jpl()} | V_Alt: {alt_v.degrees:.1f}°, J_Alt: {alt_j.degrees:.1f}°")

    return candidates

# ==========================================
# 4. EXPORT ENGINE (Saves CSV Metrics & Charts)
# ==========================================
def write_csv_log(candidates, filename, eph, ts):
    earth = eph['earth']
    observer = earth + SRIVILLIPUTHUR
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Candidate_Sunrise_UT", "Full_Moon_UT", "Day4_Rain_Date_UT", "Sun_Sid_Lon", "Sun_Rasi", "Moon_Nakshatra"])
        for t_sunrise, t_moon in candidates:
            t_rain = t_moon + timedelta(days=3)
            sun_lon = get_sidereal_lon(observer, eph['sun'], t_sunrise)
            moon_lon = get_sidereal_lon(observer, eph['moon'], t_sunrise)
            writer.writerow([
                t_sunrise.utc_jpl(), t_moon.utc_jpl(), t_rain.utc_jpl()[:11],
                f"{sun_lon:.2f}", get_rasi_name(sun_lon), get_nakshatra_name(moon_lon)
            ])
    print(f"\nSuccessfully generated matching dataset log mapping: {filename}")

def plot_brahma_muhurtham(t_sunrise, t_moon, filename, eph):
    t_brahma = t_sunrise - timedelta(minutes=96)
    earth = eph['earth']
    observer = earth + SRIVILLIPUTHUR
    
    # Evaluate Day 4 Precipitation parameters
    t_rain_day = t_moon + timedelta(days=3) 
    sun_lon_rain = get_sidereal_lon(observer, eph['sun'], t_rain_day)
    rain_rasi = get_rasi_name(sun_lon_rain)

    bodies = {
        'Sun': eph['sun'], 'Moon': eph['moon'], 'Mercury': eph['mercury'],
        'Venus': eph['venus'], 'Mars': eph['mars'],
        'Jupiter': eph['jupiter barycenter'], 'Saturn': eph['saturn barycenter']
    }
    
    obs = observer.at(t_brahma)
    data = {}
    
    for name, body in bodies.items():
        alt, az, _ = obs.observe(body).apparent().altaz()
        sid_lon = get_sidereal_lon(observer, body, t_brahma)
        data[name] = {'alt': alt.degrees, 'az': az.degrees, 'rasi': get_rasi_name(sid_lon), 
                      'nakshatra': get_nakshatra_name(sid_lon) if name == 'Moon' else None, 'lon': sid_lon}

    plt.clf()
    fig, ax = plt.subplots(figsize=(16, 9))
    
    # Sky Background
    ax.axhspan(-25, 0, color='#111827', alpha=0.95, label='Below Horizon (Patala)') 
    ax.axhspan(0, 90, color='#030712', alpha=0.95, label='Visible Sky (Akasha)') 
    ax.axhline(0, color='#64748b', linewidth=1.5, linestyle='--')
    
    # Plot Major Fixed Vedic Stars (Yogataras)
    for star_name, star_obj in VEDIC_STARS.items():
        s_alt, s_az, _ = obs.observe(star_obj).apparent().altaz()
        if -25 <= s_alt.degrees <= 75:  # Render bounding metrics within crop constraints
            ax.scatter(s_az.degrees, s_alt.degrees, s=35, c='#fef08a', marker='*', alpha=0.7, edgecolors='none', zorder=4)
            ax.text(s_az.degrees, s_alt.degrees - 2.5, star_name.split()[0], ha='center', color='#93c5fd', fontsize=8, alpha=0.8)

    # Plot Planets
    for name, d in data.items():
        alt, az, rasi = d['alt'], d['az'], d['rasi']
        label_text = f"{name}\n({rasi.split()})\n[{d['nakshatra']}]" if name == 'Moon' else f"{name}\n({rasi.split()})"
        
        color = '#f59e0b' if name == 'Sun' else '#f8fafc' if name == 'Moon' else '#38bdf8' if name == 'Venus' else '#f97316' if name == 'Jupiter' else '#ec4899'
        size = 240 if name in ['Sun', 'Moon'] else 110
        
        ax.scatter(az, alt, s=size, c=color, edgecolors='white', zorder=10)
        ax.text(az, alt + 3.5, label_text, ha='center', color='white', fontweight='bold', fontsize=8)
        ax.plot([az, az], [0, alt], color=color, linestyle=':', alpha=0.35)

    # Draw Sun-Moon Alignment Vector Line
    ax.plot([data['Sun']['az'], data['Moon']['az']], [data['Sun']['alt'], data['Moon']['alt']], 
            color='#ef4444', linestyle='-.', alpha=0.4, linewidth=1.2)

    # Construct Informational Sidebar Metadata text block
    rasi_summary_text = "Vedic Astrological Card\n" + "─" * 24 + "\n"
    for name, d in data.items():
        rasi_summary_text += f"• {name[:4]}: {d['rasi'].split()[0]} ({d['lon']:.1f}°)\n"
        if name == 'Moon': rasi_summary_text += f"   ↳ Star: {d['nakshatra']}\n"
        
    rasi_summary_text += (f"\nDay 4 Rain Window:\n" + "─" * 24 + f"\n"
                          f"• Date: {t_rain_day.utc_jpl()[:11]}\n"
                          f"• Sun Sign: {rain_rasi.split()[0]}\n"
                          f"• Lon: {sun_lon_rain:.1f}°")

    # Final Axis Formatting & Layout Configuration
    date_str = t_brahma.utc_jpl()
    plt.title(f"Brahma Muhurtham Deep-Sky Horizon Chart (96 mins before Sunrise)\nDate: {date_str} | Srivilliputhur Ground Track", color='black', fontsize=13, pad=12)
    plt.xlabel("Azimuth Angle Directions (Degrees)", fontsize=11)
    plt.ylabel("Elevation Horizon Altitude (Degrees)", fontsize=11)
    
    # FIXED: Valid non-empty positions assigned to tick intervals
    tick_positions = [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0, 360.0]
    tick_labels = ['N (0°)', 'NE (45°)', 'E (90°)\n[Rises]', 'SE (135°)', 'S (180°)', 'SW (225°)', 'W (270°)\n[Sets]', 'NW (315°)', 'N (360°)']
    plt.xticks(tick_positions, tick_labels)
    
    plt.ylim(-25, 75) 
    plt.xlim(0, 360)
    plt.grid(True, linestyle=':', alpha=0.2, color='grey')
    
    plt.gcf().text(0.825, 0.25, rasi_summary_text, fontsize=9, color='black', fontfamily='monospace',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='#f8fafc', edgecolor='#cbd5e1'))
    plt.tight_layout()
    plt.subplots_adjust(right=0.80)
    plt.savefig(filename, dpi=150)
    plt.close(fig)
    print(f"Exported chart asset profile directly to: {filename}")
    print("==========================================5. RUNTIME CONTROLLER==========================================")


if __name__ == "__main__":
    try:
        eph = load(EPHEMERIS_FILE)
        ts = load.timescale()
        matches = scan_for_thiruppavai_date(eph, ts)
        if matches:# Export chronological dataset records
            write_csv_log(matches, "thiruppavai_candidates_log.csv", eph, ts)
            print(f"\nProcessing visual charts containing background constellation stars...")
            for t_sunrise, t_moon in matches:
                raw_date = t_sunrise.utc_jpl()
                clean_date = re.sub(r'[^a-zA-Z0-9-]', '', raw_date.replace("A.D. ", "").split())
                output_filename = f"srivilliuputh_sky_on{clean_date}.png"
                plot_brahma_muhurtham(t_sunrise, t_moon, output_filename, eph)
        else:
            print("No matching celestial models discovered inside this epoch range.")
    except FileNotFoundError:
        print(f"Error: Missing core BSP dataset. Verify that '{EPHEMERIS_FILE}' is placed in your active root folder path.")


### **Astronomical & Structural Upgrades Added:**
# 1. **Valid X-Ticks Array:** Passed an explicit `tick_positions` array parameter containing float intervals `[0.0, 45.0, ... 360.0]` to guarantee Matplotlib processes label positioning correctly.
# 2. **Deep-Space Yogataras:** Integrated positions for major markers like **Rohini (Aldebaran)**, **Chitra (Spica)**, and structural components of the **Sapta Rishis (Ursa Major)** to evaluate historical stellar precessions behind the solar system layer.
# 3. **Structured CSV Logger:** Automatically pipes every detected date profile match directly into an Excel-friendly format labeled `thiruppavai_candidates_log.csv` for data analysis.


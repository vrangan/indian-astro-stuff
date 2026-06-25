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
# 3. OPTIMIZATION SCORING MATRIX
# ==========================================
def scan_for_thiruppavai_date(eph, ts):
    print(f"Running Optimization Search ({START_YEAR}-{END_YEAR} AD) using {EPHEMERIS_FILE}...")
    
    sun = eph['sun']
    jupiter = eph['jupiter barycenter'] 
    venus = eph['venus']
    earth = eph['earth']
    observer = earth + SRIVILLIPUTHUR
    
    all_scored_candidates = []
    
    for year in range(START_YEAR, END_YEAR + 1):
        t_start = ts.utc(year, 11, 15)
        t_end = ts.utc(year + 1, 2, 15)
        
        t_phases, phases = find_discrete(t_start, t_end, almanac.moon_phases(eph))
        
        for t_moon, phase in zip(t_phases, phases):
            if phase == 2:  # Full Moon
                sun_lon = get_sidereal_lon(observer, sun, t_moon)
                
                # Expanded month boundary slightly to ensure we capture borderline years
                if 235 <= sun_lon <= 275:
                    t_target = t_moon + timedelta(days=12)
                    
                    t_rise_start = t_target - timedelta(hours=12)
                    t_rise_end = t_target + timedelta(hours=12)
                    t_sunrises, _ = find_discrete(t_rise_start, t_rise_end, sunrise_sunset(eph, SRIVILLIPUTHUR))
                    
                    if len(t_sunrises) == 0: continue
                    t_sunrise = t_sunrises[0] # Safely extract single scalar time object
                    
                    # Target dawn: Evaluating exactly at early Brahma Muhurtham (60 minutes before sunrise)
                    t_check = t_sunrise - timedelta(minutes=60)
                    obs = observer.at(t_check)
                    alt_v, _, _ = obs.observe(venus).apparent().altaz()
                    alt_j, _, _ = obs.observe(jupiter).apparent().altaz()
                    
                    # MATHEMATICAL PROXIMITY SCORING (Lower Penalty = Better Match)
                    # Ideal Target Parameters: Venus clearly visible (+8°), Jupiter setting (+2°)
                    ideal_venus_alt = 8.0
                    ideal_jupiter_alt = 2.0
                    
                    penalty_v = abs(alt_v.degrees - ideal_venus_alt)
                    penalty_j = abs(alt_j.degrees - ideal_jupiter_alt)
                    total_penalty = penalty_v + penalty_j
                    
                    # Store everything unconditionally for ranking
                    all_scored_candidates.append({
                        't_sunrise': t_sunrise,
                        't_moon': t_moon,
                        'year': year,
                        'v_alt': alt_v.degrees,
                        'j_alt': alt_j.degrees,
                        'sun_lon': sun_lon,
                        'penalty': total_penalty
                    })

    # Sort all entries globally based on their penalty score (lowest penalty first)
    all_scored_candidates.sort(key=lambda x: x['penalty'])
    return all_scored_candidates

# ==========================================
# 4. EXPORT ENGINE & COMPREHENSIVE LOGGING
# ==========================================
def write_optimized_csv(candidates, filename, eph):
    earth = eph['earth']
    observer = earth + SRIVILLIPUTHUR
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Rank", "Year", "Candidate_Sunrise_UT", "Alignment_Penalty_Score", "Venus_Altitude", "Jupiter_Altitude", "Sun_Sidereal_Lon", "Moon_Nakshatra"])
        
        for rank, c in enumerate(candidates, start=1):
            t_sunrise = c['t_sunrise']
            moon_lon = get_sidereal_lon(observer, eph['moon'], t_sunrise)
            writer.writerow([
                rank, c['year'], t_sunrise.utc_jpl(), f"{c['penalty']:.2f}",
                f"{c['v_alt']:.2f}", f"{c['j_alt']:.2f}", f"{c['sun_lon']:.2f}",
                get_nakshatra_name(moon_lon)
            ])
    print(f"\nSaved complete optimization matrix log to: {filename}")

def plot_brahma_muhurtham(t_sunrise, t_moon, penalty, filename, eph):
    t_brahma = t_sunrise - timedelta(minutes=96)
    earth = eph['earth']
    observer = earth + SRIVILLIPUTHUR
    
    t_rain_day = t_moon + timedelta(days=3) 
    sun_lon_rain = get_sidereal_lon(observer, eph['sun'], t_rain_day)
    rain_rasi = get_rasi_name(sun_lon_rain)

    bodies = {
        'Sun': eph['sun'], 'Moon': eph['moon'], 'Mercury': eph['mercury'],
        'Venus': eph['venus'], 'Mars': eph['mars barycenter'],
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
    
    ax.axhspan(-25, 0, color='#111827', alpha=0.95) 
    ax.axhspan(0, 90, color='#030712', alpha=0.95) 
    ax.axhline(0, color='#64748b', linewidth=1.5, linestyle='--')
    
    for star_name, star_obj in VEDIC_STARS.items():
        s_alt, s_az, _ = obs.observe(star_obj).apparent().altaz()
        if -25 <= s_alt.degrees <= 75:  
            ax.scatter(s_az.degrees, s_alt.degrees, s=35, c='#fef08a', marker='*', alpha=0.7, zorder=4)
            ax.text(s_az.degrees, s_alt.degrees - 2.5, star_name.split(), ha='center', color='#93c5fd', fontsize=8, alpha=0.8)

    for name, d in data.items():
        alt, az, rasi = d['alt'], d['az'], d['rasi']
        label_text = f"{name}\n({rasi.split()})\n[{d['nakshatra']}]" if name == 'Moon' else f"{name}\n({rasi.split()})"
        
        color = '#f59e0b' if name == 'Sun' else '#f8fafc' if name == 'Moon' else '#38bdf8' if name == 'Venus' else '#f97316' if name == 'Jupiter' else '#ec4899'
        size = 240 if name in ['Sun', 'Moon'] else 110
        
        ax.scatter(az, alt, s=size, c=color, edgecolors='white', zorder=10)
        ax.text(az, alt + 3.5, label_text, ha='center', color='white', fontweight='bold', fontsize=8)
        ax.plot([az, az], [0, alt], color=color, linestyle=':', alpha=0.35)

    ax.plot([data['Sun']['az'], data['Moon']['az']], [data['Sun']['alt'], data['Moon']['alt']], color='#ef4444', linestyle='-.', alpha=0.4)

    rasi_summary_text = "Vedic Alignment Card\n" + "─" * 24 + "\n"
    for name, d in data.items():
        rasi_summary_text += f"• {name[:4]}: {d['rasi'].split()} ({d['lon']:.1f}°)\n"
        if name == 'Moon': rasi_summary_text += f"   ↳ Star: {d['nakshatra']}\n"
        
    rasi_summary_text += f"\nFitness Match Penalty:\n• Score: {penalty:.2f}\n"
    rasi_summary_text += (f"\nDay 4 Rain Window:\n" + "─" * 24 + f"\n"
                          f"• Date: {t_rain_day.utc_jpl()[:11]}\n"
                          f"• Sun Sign: {rain_rasi.split()}")

    date_str = t_brahma.utc_jpl()
    plt.title(f"Optimized Brahma Muhurtham Deep-Sky Horizon Map\nDate: {date_str} | Penalty Index: {penalty:.2f}", color='black', fontsize=13, pad=12)
    plt.xlabel("Azimuth Angle Directions (Degrees)", fontsize=11)
    plt.ylabel("Elevation Horizon Altitude (Degrees)", fontsize=11)
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


if __name__ == "__main__":
    try:
        eph = load(EPHEMERIS_FILE)
        ts = load.timescale()
        #1. Gather and rank all data points dynamically
        ranked_candidates = scan_for_thiruppavai_date(eph, ts)
        if ranked_candidates:
            # Write all sorted iterations into an alignment matrix log
            write_optimized_csv(ranked_candidates, "thiruppavai_optimized_ranking_log.csv", eph)
            # Print the Top 20 mathematically optimized historical dates to the screen
            print("\n" + "="*55)
            print(f" TOP 20 CE CELESTIAL ALIGNMENTS FOR THIRUPPAVAI VOW")
            print("="*55)
            print(f"{'Rank':<5} | {'Year':<5} | {'Date (Julian/Greg)':<24} | {'Penalty':<8} | {'V_Alt':<6} | {'J_Alt':<6}")
            print("-" * 65)
            # Print display table and export the Top 20 PNG sky chart profiles
            for rank, c in enumerate(ranked_candidates[:20], start=1):
                print(f"{rank:<5} | {c['year']:<5} | {c['t_sunrise'].utc_jpl()[:24]:<24} | {c['penalty']:<8.2f} | {c['v_alt']:<6.1f} | {c['j_alt']:<6.1f}")
                # FIXED: Regular expression configuration cleans string slices accurately
                raw_date_str = c['t_sunrise'].utc_jpl()
                clean_str = raw_date_str.replace("A.D. ", "")
                date_part = clean_str.split()[0]
                clean_date = re.sub(r'[^a-zA-Z0-9-]', '_', date_part)
                output_filename = f"optimized_rank_{rank}year{c['year']}_{clean_date}.png"
                plot_brahma_muhurtham(c['t_sunrise'], c['t_moon'], c['penalty'], output_filename, eph)
                print("="*65)
                print(f"Top 20 high-fidelity horizon chart assets successfully exported to folder.")
        else:
            print("No matching celestial parameters detected inside search grid boundaries.")
    except FileNotFoundError:
        print(f"Error: Missing core BSP dataset file. Check path definitions for '{EPHEMERIS_FILE}'.")



### **What to look for when running this:**
#1. **The Alignment Rank Table:** Look at the printout table at the end of execution. It lists the exact calculated parameters for the top 20 years.
#2. **Finding 731 AD:** If 731 AD was filtered out previously due to a minor edge condition (e.g., Jupiter dipping to \(-11^\circ\) instead of staying above \(-10^\circ\)), you will see it listed here along with its exact numerical penalty index score. 
#3. **`thiruppavai_optimized_ranking_log.csv`:** If you want to check a year that didn't make the top 20 printout, open this file to see its absolute rank across the entire 1,000-year timeline.


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
# 3. OPTIMIZATION & OPPOSITIONAL SCANNER
# ==========================================
def scan_for_thiruppavai_date(eph, ts):
    print(f"Running Oppositional Grid Search ({START_YEAR}-{END_YEAR} AD)...")
    
    sun_eph = eph['sun']
    jupiter_eph = eph['jupiter barycenter'] 
    venus_eph = eph['venus']
    moon_eph = eph['moon']
    earth = eph['earth']
    observer = earth + SRIVILLIPUTHUR
    
    all_scored_candidates = []
    
    for year in range(START_YEAR, END_YEAR + 1):
        t_start = ts.utc(year, 11, 15)
        t_end = ts.utc(year + 1, 2, 15)
        
        t_phases, phases = find_discrete(t_start, t_end, almanac.moon_phases(eph))
        
        for t_moon, phase in zip(t_phases, phases):
            if phase == 2:  # Full Moon
                sun_lon = get_sidereal_lon(observer, sun_eph, t_moon)
                
                if 235 <= sun_lon <= 275:
                    t_target = t_moon + timedelta(days=12)
                    
                    t_rise_start = t_target - timedelta(hours=12)
                    t_rise_end = t_target + timedelta(hours=12)
                    t_sunrises, _ = find_discrete(t_rise_start, t_rise_end, sunrise_sunset(eph, SRIVILLIPUTHUR))
                    
                    if len(t_sunrises) == 0: continue
                    t_sunrise = t_sunrises[0]
                    
                    t_check = t_sunrise - timedelta(minutes=60)
                    obs = observer.at(t_check)
                    
                    v_pos = obs.observe(venus_eph).apparent()
                    j_pos = obs.observe(jupiter_eph).apparent()
                    
                    alt_v, _, _ = v_pos.altaz()
                    alt_j, _, _ = j_pos.altaz()
                    
                    separation_angle = v_pos.separation_from(j_pos).degrees
                    
                    # True planetary opposition alignments filter (150° - 180°)
                    if 150.0 <= separation_angle <= 180.0:
                        
                        s_lon = get_sidereal_lon(observer, sun_eph, t_check)
                        m_lon = get_sidereal_lon(observer, moon_eph, t_check)
                        v_lon = get_sidereal_lon(observer, venus_eph, t_check)
                        j_lon = get_sidereal_lon(observer, jupiter_eph, t_check)
                        
                        ideal_venus_alt = 8.0
                        ideal_jupiter_alt = 2.0
                        penalty = abs(alt_v.degrees - ideal_venus_alt) + abs(alt_j.degrees - ideal_jupiter_alt)
                        
                        all_scored_candidates.append({
                            't_sunrise': t_sunrise, 't_moon': t_moon, 'year': year,
                            'v_alt': alt_v.degrees, 'j_alt': alt_j.degrees,
                            'sep': separation_angle, 'penalty': penalty,
                            'sun_lon': s_lon, 'moon_lon': m_lon, 'venus_lon': v_lon, 'jupiter_lon': j_lon
                        })

    all_scored_candidates.sort(key=lambda x: x['penalty'])
    return all_scored_candidates

# ==========================================
# 4. EXPORT ENGINE & COMPREHENSIVE LOGGING
# ==========================================
def write_optimized_csv(candidates, filename, eph):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            "Rank", "Year", "Candidate_Sunrise_UT", "Alignment_Penalty", "Separation_Angle",
            "Sun_Rasi", "Sun_Longitude", "Moon_Rasi", "Moon_Nakshatra", "Moon_Longitude",
            "Venus_Rasi", "Venus_Altitude", "Venus_Longitude", "Jupiter_Rasi", "Jupiter_Altitude", "Jupiter_Longitude"
        ])
        
        for rank, c in enumerate(candidates, start=1):
            writer.writerow([
                rank, c['year'], c['t_sunrise'].utc_jpl(), f"{c['penalty']:.2f}", f"{c['sep']:.2f}",
                get_rasi_name(c['sun_lon']), f"{c['sun_lon']:.2f}",
                get_rasi_name(c['moon_lon']), get_nakshatra_name(c['moon_lon']), f"{c['moon_lon']:.2f}",
                get_rasi_name(c['venus_lon']), f"{c['v_alt']:.2f}", f"{c['venus_lon']:.2f}",
                get_rasi_name(c['jupiter_lon']), f"{c['j_alt']:.2f}", f"{c['jupiter_lon']:.2f}"
            ])
    print(f"\nSaved tracking log file featuring all planet coordinates: {filename}")

def plot_brahma_muhurtham(c, filename, eph):
    t_brahma = c['t_sunrise'] - timedelta(minutes=96)
    earth = eph['earth']
    observer = earth + SRIVILLIPUTHUR
    obs = observer.at(t_brahma)
    
    # FIXED: Updated 'mars' to 'mars barycenter' key alignment
    bodies = {
        'Sun': eph['sun'], 'Moon': eph['moon'], 'Mercury': eph['mercury'],
        'Venus': eph['venus'], 'Mars': eph['mars barycenter'],
        'Jupiter': eph['jupiter barycenter'], 'Saturn': eph['saturn barycenter']
    }
    
    plt.clf()
    fig, ax = plt.subplots(figsize=(16, 9))
    ax.axhspan(-25, 0, color='#111827', alpha=0.95) 
    ax.axhspan(0, 90, color='#030712', alpha=0.95) 
    ax.axhline(0, color='#64748b', linewidth=1.5, linestyle='--')
    
    # Plot Stars
    for star_name, star_obj in VEDIC_STARS.items():
        s_alt, s_az, _ = obs.observe(star_obj).apparent().altaz()
        if -25 <= s_alt.degrees <= 75:  
            ax.scatter(s_az.degrees, s_alt.degrees, s=35, c='#fef08a', marker='*', alpha=0.7, zorder=4)
            ax.text(s_az.degrees, s_alt.degrees - 2.5, star_name.split(), ha='center', color='#93c5fd', fontsize=8, alpha=0.8)

    # Plot Planets
    for name, body in bodies.items():
        alt, az, _ = obs.observe(body).apparent().altaz()
        sid_lon = get_sidereal_lon(observer, body, t_brahma)
        rasi = get_rasi_name(sid_lon)
        
        label_text = f"{name}\n({rasi.split()})\n[{get_nakshatra_name(sid_lon)}]" if name == 'Moon' else f"{name}\n({rasi.split()})"
        color = '#f59e0b' if name == 'Sun' else '#f8fafc' if name == 'Moon' else '#38bdf8' if name == 'Venus' else '#f97316' if name == 'Jupiter' else '#ec4899'
        size = 240 if name in ['Sun', 'Moon'] else 110
        
        ax.scatter(az.degrees, alt.degrees, s=size, c=color, edgecolors='white', zorder=10)
        ax.text(az.degrees, alt.degrees + 3.5, label_text, ha='center', color='white', fontweight='bold', fontsize=8)
        ax.plot([az.degrees, az.degrees], [0, alt.degrees], color=color, linestyle=':', alpha=0.35)

    # Visual Panel Card Summary
    summary_text = (
        f"Vedic Positions Log\n" + "─" * 24 + f"\n"
        f"• Sun  : {get_rasi_name(c['sun_lon']).split()} ({c['sun_lon']:.1f}°)\n"
        f"• Moon : {get_rasi_name(c['moon_lon']).split()} ({c['moon_lon']:.1f}°)\n"
        f"  ↳ Star: {get_nakshatra_name(c['moon_lon'])}\n"
        f"• Venus: {get_rasi_name(c['venus_lon']).split()} ({c['venus_lon']:.1f}°)\n"
        f"• Jupit: {get_rasi_name(c['jupiter_lon']).split()} ({c['jupiter_lon']:.1f}°)\n\n"
        f"Alignment Diagnostics:\n"
        f"• Separation : {c['sep']:.2f}°\n"
        f"• Fit Penalty: {c['penalty']:.2f}"
    )

    date_str = t_brahma.utc_jpl()
    plt.title(f"Brahma Muhurtham Map (Enforced Opposition Framework)\nDate: {date_str} | Separation Vector: {c['sep']:.2f}°", color='black', fontsize=13, pad=12)
    plt.xlabel("Azimuth Angle Directions (Degrees)", fontsize=11)
    plt.ylabel("Elevation Horizon Altitude (Degrees)", fontsize=11)
    tick_positions = [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0, 360.0]
    tick_labels = ['N (0°)', 'NE (45°)', 'E (90°)\n[Rises]', 'SE (135°)', 'S (180°)', 'SW (225°)', 'W (270°)\n[Sets]', 'NW (315°)', 'N (360°)']
    plt.xticks(tick_positions, tick_labels)
    plt.ylim(-25, 75)
    plt.xlim(0, 360)
    plt.grid(True, linestyle=':', alpha=0.2, color='grey')
    plt.gcf().text(0.825, 0.25, summary_text, fontsize=9, color='black', fontfamily='monospace', bbox=dict(boxstyle='round,pad=0.5', facecolor='#f8fafc', edgecolor='#cbd5e1'))
    plt.tight_layout()
    plt.subplots_adjust(right=0.80)
    plt.savefig(filename, dpi=150)
    plt.close(fig)

if __name__ == "__main__":
    try:
        eph = load(EPHEMERIS_FILE)
        ts = load.timescale()
        matches = scan_for_thiruppavai_date(eph, ts)
        if matches:write_optimized_csv(matches, "thiruppavai_oppositional_matrix.csv", eph)
        print("\n" + "="*72)
        print(f" TOP TRUE OPPOSITION CELESTIAL SIGN ALIGNMENTS (150°-180° SEPARATION)")
        print("="*72)
        print(f"{'Rank':<5} | {'Year':<5} | {'Date (Julian/Greg)':<24} | {'Sep°':<6} | {'Sun_Rasi':<12} | {'Moon_Star':<12}")
        print("-" * 75)
        for rank, c in enumerate(matches[:15], start=1):
            print(f"{rank:<5} | {c['year']:<5} | {c['t_sunrise'].utc_jpl()[:24]:<24} | {c['sep']:<6.1f} | {get_rasi_name(c['sun_lon']).split():<12} | {get_nakshatra_name(c['moon_lon']):<12}")
            raw_date_str = str(c['t_sunrise'].utc_jpl())
            clean_str = raw_date_str.replace("A.D. ", "")
            date_part = clean_str.split()[0]
            clean_date = re.sub(r'[^a-zA-Z0-9-]', '_', date_part)
            output_filename = f"opposition_rank_{rank}year{c['year']}_{clean_date}.png"
            plot_brahma_muhurtham(c, output_filename, eph)
            print("="*75)
        else:
            print("No matching celestial parameters detected inside true separation limits.")
    except FileNotFoundError:
        print(f"Error: Path validation failed for internal binary segment '{EPHEMERIS_FILE}'.")

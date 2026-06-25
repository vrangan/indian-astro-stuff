import matplotlib.pyplot as plt
import csv
import re
from skyfield.api import load, wgs84
from skyfield import almanac  
from skyfield.almanac import find_discrete, sunrise_sunset
from datetime import timedelta

# Import calculators from Block 1
from vedic_calculators import (
    to_scalar, get_sidereal_lon, get_rasi_name, 
    get_nakshatra_name, VEDIC_STARS
)

EPHEMERIS_FILE = 'de431_part-2.bsp' 
SRIVILLIPUTHUR = wgs84.latlon(9.5161, 77.6284)
START_YEAR = 1
END_YEAR = 1000

def scan_for_thiruppavai_date(eph, ts):
    print(f"Running Oppositional Grid Search ({START_YEAR}-{END_YEAR} AD)...")
    sun_eph, jupiter_eph, venus_eph, moon_eph = eph['sun'], eph['jupiter barycenter'], eph['venus'], eph['moon']
    observer = eph['earth'] + SRIVILLIPUTHUR
    all_scored_candidates = []
    
    for year in range(START_YEAR, END_YEAR + 1):
        t_phases, phases = find_discrete(ts.utc(year, 11, 15), ts.utc(year + 1, 2, 15), almanac.moon_phases(eph))
        for t_moon, phase in zip(t_phases, phases):
            if phase == 2 and 235 <= get_sidereal_lon(observer, sun_eph, t_moon) <= 275:
                t_target = t_moon + timedelta(days=12)
                t_sunrises, _ = find_discrete(t_target - timedelta(hours=12), t_target + timedelta(hours=12), sunrise_sunset(eph, SRIVILLIPUTHUR))
                if len(t_sunrises) == 0: continue
                
                t_sunrise = t_sunrises[0] # Force array extract
                t_check = t_sunrise - timedelta(minutes=60)
                obs = observer.at(t_check)
                
                v_pos, j_pos = obs.observe(venus_eph).apparent(), obs.observe(jupiter_eph).apparent()
                alt_v, _, _ = v_pos.altaz()
                alt_j, _, _ = j_pos.altaz()
                separation_angle = to_scalar(v_pos.separation_from(j_pos).degrees)
                
                if 150.0 <= separation_angle <= 180.0:
                    all_scored_candidates.append({
                        't_sunrise': t_sunrise, 't_moon': t_moon, 'year': year,
                        'v_alt': to_scalar(alt_v.degrees), 'j_alt': to_scalar(alt_j.degrees),
                        'sep': separation_angle, 'penalty': abs(to_scalar(alt_v.degrees) - 8.0) + abs(to_scalar(alt_j.degrees) - 2.0),
                        'sun_lon': get_sidereal_lon(observer, sun_eph, t_check), 'moon_lon': get_sidereal_lon(observer, moon_eph, t_check),
                        'venus_lon': get_sidereal_lon(observer, venus_eph, t_check), 'jupiter_lon': get_sidereal_lon(observer, jupiter_eph, t_check)
                    })
    all_scored_candidates.sort(key=lambda x: x['penalty'])
    return all_scored_candidates

def write_optimized_csv(candidates, filename, eph):
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Rank", "Year", "Candidate_Sunrise_UT", "Alignment_Penalty", "Separation_Angle", "Sun_Rasi", "Sun_Longitude", "Moon_Rasi", "Moon_Nakshatra", "Venus_Rasi", "Venus_Altitude", "Jupiter_Rasi", "Jupiter_Altitude"])
        for rank, c in enumerate(candidates, start=1):
            writer.writerow([rank, c['year'], c['t_sunrise'].utc_jpl(), f"{c['penalty']:.2f}", f"{c['sep']:.2f}", get_rasi_name(c['sun_lon']), f"{c['sun_lon']:.2f}", get_rasi_name(c['moon_lon']), get_nakshatra_name(c['moon_lon']), get_rasi_name(c['venus_lon']), f"{c['v_alt']:.2f}", get_rasi_name(c['jupiter_lon']), f"{c['j_alt']:.2f}"])
    print(f"\nSaved coordinates matrix database log directly to: {filename}")

def plot_brahma_muhurtham(c, filename, eph):
    t_brahma = c['t_sunrise'] - timedelta(minutes=96)
    observer = eph['earth'] + SRIVILLIPUTHUR
    obs = observer.at(t_brahma)
    bodies = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mercury': eph['mercury'], 'Venus': eph['venus'], 'Mars': eph['mars barycenter'], 'Jupiter': eph['jupiter barycenter'], 'Saturn': eph['saturn barycenter']}
    
    plt.clf()
    fig, ax = plt.subplots(figsize=(16, 9))
    ax.axhspan(-25, 0, color='#111827', alpha=0.95)
    ax.axhspan(0, 90, color='#030712', alpha=0.95)
    ax.axhline(0, color='#64748b', linewidth=1.5, linestyle='--')
    
    for star_name, star_obj in VEDIC_STARS.items():
        s_alt, s_az, _ = obs.observe(star_obj).apparent().altaz()
        sa_deg, sz_deg = to_scalar(s_alt.degrees), to_scalar(s_az.degrees)
        if -25 <= sa_deg <= 75:  
            ax.scatter(sz_deg, sa_deg, s=35, c='#fef08a', marker='*', alpha=0.7, zorder=4)
            ax.text(sz_deg, sa_deg - 2.5, star_name.split()[0], ha='center', color='#93c5fd', fontsize=8)

    for name, body in bodies.items():
        alt, az, _ = obs.observe(body).apparent().altaz()
        sid_lon = get_sidereal_lon(observer, body, t_brahma)
        alt_deg, az_deg = to_scalar(alt.degrees), to_scalar(az.degrees)
        label_text = f"{name}\n({get_rasi_name(sid_lon).split()[0]})\n[{get_nakshatra_name(sid_lon)}]" if name == 'Moon' else f"{name}\n({get_rasi_name(sid_lon).split()[0]})"
        color = '#f59e0b' if name == 'Sun' else '#f8fafc' if name == 'Moon' else '#38bdf8' if name == 'Venus' else '#f97316' if name == 'Jupiter' else '#ec4899'
        ax.scatter(az_deg, alt_deg, s=200 if name in ['Sun', 'Moon'] else 110, c=color, edgecolors='white', zorder=10)
        ax.text(az_deg, alt_deg + 3.5, label_text, ha='center', color='white', fontweight='bold', fontsize=8)
    
    plt.xticks([0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0, 360.0], ['N (0°)', 'NE (45°)', 'E (90°)\n[Rises]', 'SE (135°)', 'S (180°)', 'SW (225°)', 'W (270°)\n[Sets]', 'NW (315°)', 'N (360°)'])
    plt.ylim(-25, 75); plt.xlim(0, 360); plt.tight_layout()
    plt.savefig(filename, dpi=150); plt.close(fig)

if __name__ == "__main__":
    try:
        eph, ts = load(EPHEMERIS_FILE), load.timescale()
        matches = scan_for_thiruppavai_date(eph, ts)
        if matches:
            write_optimized_csv(matches, "thiruppavai_oppositional_matrix.csv", eph)
            print("\n" + "="*72 + f"\n TOP TRUE OPPOSITION CELESTIAL SIGN ALIGNMENTS\n" + "="*72)
            for rank, c in enumerate(matches[:15], start=1):
                date_parts = str(c['t_sunrise'].utc_jpl()).replace("A.D. ", "").split()
                pure_date = date_parts[0]
                clean_date = re.sub(r'[^a-zA-Z0-9\-]', '_', pure_date)
                print(f"{rank:<2} | {c['year']:<4} | {pure_date:<12} | Sep: {c['sep']:<5.1f}° | Sun: {get_rasi_name(c['sun_lon']).split()[0]:<10} | Moon Star: {get_nakshatra_name(c['moon_lon'])}")
                plot_brahma_muhurtham(c, f"opposition_rank_{rank}_year_{c['year']}_{clean_date}.png", eph)
        else:
            print("No matching celestial parameters detected.")
    except FileNotFoundError:
        print(f"Error: Could not locate '{EPHEMERIS_FILE}'.")


"""
THE ULTIMATE JYOTISHI SCANNER (True Chitra Paksha Edition - V8)
---------------------------------------------------------------
New Constraints:
1. First day of Margazhi (Sun crossing 240.0° exactly).
2. Moon is Full (Purnima) on that exact first day.
3. Simultaneous Venus Rise + Jupiter Set (Sometime during that month).
"""

import time
import os
import sys
from multiprocessing import Pool, cpu_count, freeze_support
from skyfield.api import load, wgs84, Star
from skyfield import almanac
from skyfield.jpllib import SpiceKernel

# --- CONFIGURATION ---
START_YEAR = -3500
END_YEAR = 1000
LOCATION_LAT = 9.5076  # Srivilliputhur
LOCATION_LON = 77.6311 
VJ_TOLERANCE_MINUTES = 60
CHUNK_SIZE_YEARS = 20

# FILES
FILE_BC = 'de431_part-1.bsp' 
FILE_AD = 'de431_part-2.bsp' 

def scan_period(args):
    year_start, year_end, eph_file = args
    local_results = []
    
    if year_start >= year_end: return ("SUCCESS", [])
    if not os.path.exists(eph_file): return ("ERROR", f"Missing File: {eph_file}")

    try:
        ts = load.timescale()
        eph = SpiceKernel(eph_file) 
        
        sun = eph['sun']
        moon = eph['moon']
        venus = eph['venus']
        jupiter = eph['jupiter barycenter']
        earth = eph['earth'] 
        
        observer_loc = wgs84.latlon(LOCATION_LAT, LOCATION_LON)
        observer_topo = earth + observer_loc
        
        def venus_vis(t):
            alt, _, _ = observer_topo.at(t).observe(venus).apparent().altaz()
            return alt.degrees > -0.5667 
        venus_vis.step_days = 0.04

        def jupiter_vis(t):
            alt, _, _ = observer_topo.at(t).observe(jupiter).apparent().altaz()
            return alt.degrees > -0.5667
        jupiter_vis.step_days = 0.04

        spica = Star(ra_hours=(13, 25, 11.579), dec_degrees=(-11, 9, 40.75))

        def get_true_lahiri_ayanamsa(t):
            _, lon, _ = earth.at(t).observe(spica).apparent().ecliptic_latlon()
            return (lon.degrees - 180.0) % 360

        def get_vedic_geocentric_pos(t, body):
            _, lon, _ = earth.at(t).observe(body).apparent().ecliptic_latlon()
            ayan = get_true_lahiri_ayanamsa(t)
            return (lon.degrees - ayan) % 360

        curr_t = ts.utc(year_start, 1, 1)
        end_t_val = ts.utc(year_end, 1, 1).tt 
        
        t_prev = ts.tt_jd(curr_t.tt - 1.0)
        prev_s_long = get_vedic_geocentric_pos(t_prev, sun)

        while curr_t.tt < end_t_val:
            s_long = get_vedic_geocentric_pos(curr_t, sun)
            
            # 1. GATEKEEPER: Sun enters Dhanu (First day of Margazhi)
            if prev_s_long < 240.0 and s_long >= 240.0:
                
                # 2. GATEKEEPER: Is it Purnima on this first day?
                m_long = get_vedic_geocentric_pos(curr_t, moon)
                phase = (m_long - s_long) % 360
                
                if 168.0 <= phase <= 192.0: 
                    
                    # 3. ALIGNMENT CHECK: Scan the ENTIRE solar month (31 days)
                    t_scan_start = ts.tt_jd(curr_t.tt)
                    t_scan_end = ts.tt_jd(curr_t.tt + 31.0)
                    
                    t_v, y_v = almanac.find_discrete(t_scan_start, t_scan_end, venus_vis)
                    t_j, y_j = almanac.find_discrete(t_scan_start, t_scan_end, jupiter_vis)
                    
                    v_rises_tt = t_v.tt[y_v == 1]
                    j_sets_tt = t_j.tt[y_j == 0]
                    
                    for v_tt in v_rises_tt:
                        for j_tt in j_sets_tt:
                            gap_min = abs(v_tt - j_tt) * 24 * 60
                            
                            if gap_min <= VJ_TOLERANCE_MINUTES:
                                hit_t = ts.tt_jd(v_tt)
                                y, m, d, hh, mm, _ = hit_t.utc
                                fmt_date = f"{abs(y)+1} BC" if y <= 0 else f"{y} AD"
                                full_date = f"{fmt_date}-{m:02d}-{d:02d} {hh:02d}:{mm:02d}"
                                
                                s_exact = get_vedic_geocentric_pos(hit_t, sun)
                                m_exact = get_vedic_geocentric_pos(hit_t, moon)
                                
                                local_results.append({
                                    "Julian_Day": round(hit_t.ut1, 4), 
                                    "Date_UTC": full_date,
                                    "Sun_Deg": round(s_exact, 2),
                                    "Moon_Deg": round(m_exact, 2),
                                    "Gap_Min": round(gap_min, 1)
                                })
                    
                    # Jump 31 days forward to bypass the rest of this month
                    curr_t = ts.tt_jd(curr_t.tt + 31.0)
                    prev_s_long = get_vedic_geocentric_pos(curr_t, sun)
                    continue

            # Step forward exactly 1 day
            prev_s_long = s_long
            curr_t = ts.tt_jd(curr_t.tt + 1)
            
        return ("SUCCESS", local_results)
    
    except Exception as e:
        return ("ERROR", f"Math/Logic error in {year_start}-{year_end}: {str(e)}")
    finally:
        if 'eph' in locals() and hasattr(eph, 'close'):
            eph.close()

def process_chunk(args):
    try:
        year_start, year_end = args
        results = []

        # 1. BC Portion (Now includes Year 0 / 1 BC)
        if year_start < 1:
            bc_end = min(1, year_end)
            if bc_end > year_start:
                status, res = scan_period((year_start, bc_end, FILE_BC))
                if status == "SUCCESS": results += res
                else: return (status, res)

        # 2. AD Portion (Strictly starts at Year 1 / 1 AD)
        if year_end > 1:
            ad_start = max(1, year_start)
            if year_end > ad_start:
                status, res = scan_period((ad_start, year_end, FILE_AD))
                if status == "SUCCESS": results += res
                else: return (status, res)

        return ("SUCCESS", results)
    except Exception as e:
        return ("ERROR", f"Worker crash on {args}: {str(e)}")

def deduplicate(events):
    if not events: return []
    events.sort(key=lambda x: x["Julian_Day"]) 
    cleaned = [events[0]]
    for i in range(1, len(events)):
        # If events are within a few hours of each other, it's the same alignment
        if abs(events[i]["Julian_Day"] - cleaned[-1]["Julian_Day"]) > 0.5:
            cleaned.append(events[i])
    return cleaned

if __name__ == '__main__':
    freeze_support()
    print(f"--- MARGAZHI MONTH SCANNER (V8) ---")
    start_time = time.time()
    
    chunks = [(y, y + CHUNK_SIZE_YEARS) for y in range(START_YEAR, END_YEAR, CHUNK_SIZE_YEARS)]
    raw = []
    
    with Pool(processes=cpu_count()) as pool:
        for res in pool.imap_unordered(process_chunk, chunks):
            if res[0] == "SUCCESS":
                if res[1]: 
                    raw.extend(res[1])
                    print("!", end="", flush=True) 
                else:
                    print(".", end="", flush=True) 
            elif res[0] == "ERROR": 
                print(f"\n[X] {res[1]}")

    print(f"\nFound {len(raw)} raw matches. Deduplicating...")
    final = deduplicate(raw)
    
    csv_name = f"margazhi_month_scan_{START_YEAR}_{END_YEAR}.csv"
    with open(csv_name, "w") as f:
        f.write("Julian_Day,Date_UTC,Sun_Deg,Moon_Deg,Gap_Min\n")
        for r in final:
            f.write(f"{r['Julian_Day']},{r['Date_UTC']},{r['Sun_Deg']},{r['Moon_Deg']},{r['Gap_Min']}\n")
            
    print(f"Saved to {csv_name}. Run time: {time.time() - start_time:.1f}s")

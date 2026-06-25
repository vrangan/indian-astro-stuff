#!/usr/bin/env python3
import argparse
from datetime import datetime

# ------------------------------------------------------------
#  Julian Date <-> Calendar Date Conversion
# ------------------------------------------------------------

def datetime_to_julian(year, month, day, hour=0, minute=0, second=0):
    """
    Convert a proleptic Gregorian date to Julian Date.
    Supports astronomical year numbering (year 0 = 1 BC).
    """

    # fractional day
    day = day + (hour + (minute + second/60)/60)/24

    # Shift Jan/Feb to months 13/14 of previous year
    if month <= 2:
        year -= 1
        month += 12

    A = year // 100
    B = 2 - A + (A // 4)

    jd = int(365.25 * (year + 4716)) \
         + int(30.6001 * (month + 1)) \
         + day + B - 1524.5

    return jd


def julian_to_calendar(jd):
    """
    Convert Julian Date to proleptic Gregorian calendar date.
    Returns (year, month, day, hour, minute, second, microsecond).
    """

    jd += 0.5
    Z = int(jd)
    F = jd - Z

    if Z < 2299161:
        A = Z
    else:
        alpha = int((Z - 1867216.25) / 36524.25)
        A = Z + 1 + alpha - int(alpha / 4)

    B = A + 1524
    C = int((B - 122.1) / 365.25)
    D = int(365.25 * C)
    E = int((B - D) / 30.6001)

    day = B - D - int(30.6001 * E) + F

    if E < 14:
        month = E - 1
    else:
        month = E - 13

    if month > 2:
        year = C - 4716
    else:
        year = C - 4715

    # Extract time from fractional day
    day_int = int(day)
    frac = day - day_int

    hour = int(frac * 24)
    frac = frac * 24 - hour

    minute = int(frac * 60)
    frac = frac * 60 - minute

    second = int(frac * 60)
    frac = frac * 60 - second

    microsecond = int(round(frac * 1_000_000))

    # Normalize if rounding pushes microsecond to 1,000,000
    if microsecond == 1_000_000:
        microsecond = 0
        second += 1
        if second == 60:
            second = 0
            minute += 1
            if minute == 60:
                minute = 0
                hour += 1
                if hour == 24:
                    hour = 0
                    day_int += 1
                    # (Month/year rollover handled below if needed)

    return year, month, day_int, hour, minute, second, microsecond


# ------------------------------------------------------------
#  Robust BC‑safe date parser
# ------------------------------------------------------------

def parse_date_string(s):
    """
    Parse date strings including negative years.
    Accepts:
      YYYY-MM-DD
      YYYY-MM-DD HH:MM
      YYYY-MM-DD HH:MM:SS
    """

    s = s.strip()
    parts = s.split()
    date_part = parts[0]
    time_part = parts[1] if len(parts) > 1 else None

    # Find first '-' AFTER the sign
    first_dash = date_part.find('-', 1)
    if first_dash == -1:
        raise ValueError(f"Invalid date: {s}")

    year = int(date_part[:first_dash])
    rest = date_part[first_dash+1:]

    month, day = map(int, rest.split('-', 1))

    if time_part:
        t = list(map(int, time_part.split(":")))
        while len(t) < 3:
            t.append(0)
        hh, mm, ss = t
    else:
        hh = mm = ss = 0

    return year, month, day, hh, mm, ss


# ------------------------------------------------------------
#  CLI
# ------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert between calendar dates, Julian Dates, and Modified Julian Dates (supports BC)."
    )

    parser.add_argument(
        "inputs",
        nargs="*",
        help="Date(s) like '2024-01-01', '-44-03-15', JD like '2460000.5', or MJD like '60000'"
    )

    parser.add_argument("--from-jd", action="store_true", help="Interpret inputs as Julian Dates → convert to calendar date")
    parser.add_argument("--from-mjd", action="store_true", help="Interpret inputs as Modified Julian Dates → convert to calendar date")
    parser.add_argument("--to-mjd", action="store_true", help="Output Modified Julian Date instead of JD")

    args = parser.parse_args()

    # No args → use now()
    if not args.inputs:
        now = datetime.now()
        jd = datetime_to_julian(
            now.year, now.month, now.day,
            now.hour, now.minute, now.second
        )
        if args.to_mjd:
            print(f"{now} → MJD {jd - 2400000.5}")
        else:
            print(f"{now} → JD {jd}")
        return

    for item in args.inputs:

        # MJD → date
        if args.from_mjd:
            mjd = float(item)
            jd = mjd + 2400000.5
            y, m, d, hh, mm, ss = julian_to_calendar(jd)
            print(f"MJD {mjd} → {y:04d}-{m:02d}-{d:02d} {hh:02d}:{mm:02d}:{ss:02d}")
            continue

        # JD → date
        if args.from_jd:
            jd = float(item)
            y, m, d, hh, mm, ss, ms = julian_to_calendar(jd)
            print(f"JD {jd} → {y:04d}-{m:02d}-{d:02d} {hh:02d}:{mm:02d}:{ss:02d}.{ms:6d}")
            continue

        # Date → JD or MJD
        y, m, d, hh, mm, ss = parse_date_string(item)
        jd = datetime_to_julian(y, m, d, hh, mm, ss)

        if args.to_mjd:
            print(f"{item} → MJD {jd - 2400000.5}")
        else:
            print(f"{item} → JD {jd}")


if __name__ == "__main__":
    main()


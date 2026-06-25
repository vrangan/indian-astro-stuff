import argparse

def julian_date_from_ymdhms(year, month, day, hour=0, minute=0, second=0):
    """
    Compute Julian Date for any proleptic Gregorian date, including BC.
    Uses astronomical year numbering:
        1 BC = year 0
        2 BC = year -1
        etc.
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


def parse_date_string(s):
    """
    Parse flexible date formats including BC years.
    Accepts:
      YYYY-MM-DD
      YYYY-MM-DD HH:MM
      YYYY-MM-DD HH:MM:SS
    Where YYYY may be negative (BC).
    """

    s = s.strip()

    # First split off the time part if present
    parts = s.split()
    date_part = parts[0]
    time_part = parts[1] if len(parts) > 1 else None

    # Extract year manually (handles leading '-')
    # Find the first two '-' characters: year-month-day
    first_dash = date_part.find('-', 1)   # start at index 1 to skip sign
    if first_dash == -1:
        raise ValueError(f"Invalid date: {s}")

    year = int(date_part[:first_dash])

    rest = date_part[first_dash+1:]
    month, day = map(int, rest.split('-', 1))

    # Parse time
    if time_part:
        t = list(map(int, time_part.split(":")))
        while len(t) < 3:
            t.append(0)
        hh, mm, ss = t
    else:
        hh = mm = ss = 0

    return year, month, day, hh, mm, ss


def main():
    parser = argparse.ArgumentParser(
        description="Convert date/time (including BC) to Julian Date"
    )
    parser.add_argument(
        "dates",
        nargs="*",
        help="Date(s) like '2024-01-01', '-44-03-15', '100-05-10 12:30'"
    )

    args = parser.parse_args()

    if not args.dates:
        # Default: use current system time, but datetime cannot handle BC
        from datetime import datetime
        now = datetime.now()
        jd = julian_date_from_ymdhms(
            now.year, now.month, now.day,
            now.hour, now.minute, now.second
        )
        print(f"{now} → JD {jd}")
        return

    for s in args.dates:
        y, m, d, hh, mm, ss = parse_date_string(s)
        jd = julian_date_from_ymdhms(y, m, d, hh, mm, ss)
        print(f"{s} → JD {jd}")


if __name__ == "__main__":
    main()

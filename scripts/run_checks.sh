#!/usr/bin/env bash
set -euo pipefail

# Root of the repo
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

BANNER() {
  echo "═══════════════════════════════════════════════════════════"
  echo "$1"
  echo "═══════════════════════════════════════════════════════════"
}

BANNER "Thiruppavai Dating System: CI Checks"

# Check ephemeris files
if [[ ! -f de441_part-1.bsp || ! -f de441_part-2.bsp ]]; then
  echo "[ERROR] Missing ephemeris files de441_part-1.bsp / de441_part-2.bsp"
  echo "Please place the DE441 SPICE kernel files in the repo root."
  exit 1
fi

# Check Python and key modules
python3 - <<'PY'
try:
    import skyfield
    import numpy
    import matplotlib
    print("✓ Python and required modules present")
except Exception as e:
    print("[ERROR] Missing Python modules:", e)
    raise
PY

BANNER "Running Unit Tests"
python3 -m unittest discover -s tests -p "test_*.py" -v

BANNER "Sample Scan 1: Ujjain, Full Moon (Tithi 14), WITH V-J Alignment"
python3 ThiruppavaiDating.py \
  --year-range -6000 -5990 \
  --location Ujjain \
  --tithi 14 \
  --vj-only \
  --vj-tolerance 5.0 \
  --visualize --num-visualizations 1 \
  --generate-horoscopes --chart-style south_indian \
  --output results_vj_required.csv \
  --cores 2 --quiet

# Count V-J required results
VJ_COUNT=$(wc -l < results_vj_required.csv 2>/dev/null || echo 0)
echo "✓ Results with V-J alignment: $(($VJ_COUNT - 1)) events"

BANNER "Sample Scan 2: Chennai, Full Moon (Tithi 14), NO V-J Requirement"
python3 ThiruppavaiDating.py \
  --year-range -6000 -5990 \
  --location Chennai \
  --tithi 14 \
  --no-vj \
  --visualize --num-visualizations 2 \
  --generate-horoscopes --chart-style north_indian \
  --output results_no_vj.csv \
  --cores 2 --quiet

# Count no V-J results
NO_VJ_COUNT=$(wc -l < results_no_vj.csv 2>/dev/null || echo 0)
echo "✓ Results without V-J requirement: $(($NO_VJ_COUNT - 1)) events"

# Compare
echo
echo "─────────────────────────────────────────────────────────"
echo "Comparison Summary:"
echo "─────────────────────────────────────────────────────────"
echo "With V-J alignment (Ujjain):       $(($VJ_COUNT - 1)) events"
echo "Without V-J requirement (Chennai): $(($NO_VJ_COUNT - 1)) events"
echo "Difference:                        $(($(($NO_VJ_COUNT - 1)) - $(($VJ_COUNT - 1)))) more events without V-J"
echo "─────────────────────────────────────────────────────────"

# List all artifacts
echo
echo "Generated Artifacts:"
ls -lh visualization_*.png horoscope_*.png results_*.csv 2>/dev/null | tail -10 || true

BANNER "Checks Complete"


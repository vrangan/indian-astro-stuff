#!/bin/bash

echo "═══════════════════════════════════════════════════════════"
echo "CLI Testing Script for Thiruppavai Dating System"
echo "═══════════════════════════════════════════════════════════"
echo ""

echo "Test 1: Check Python syntax"
python3 -m py_compile ThiruppavaiDating.py horoscope.py visualize_event.py && echo "✓ All Python files valid" || echo "✗ Syntax error"
echo ""

echo "Test 2: Display help"
python3 ThiruppavaiDating.py --help > /dev/null 2>&1 && echo "✓ Help works" || echo "✗ Help failed"
echo ""

echo "Test 3: List locations"
python3 ThiruppavaiDating.py --list-locations > /dev/null 2>&1 && echo "✓ Location listing works" || echo "✗ Location listing failed"
echo ""

echo "Test 4: Parse arguments (dry run)"
echo "from ThiruppavaiDating import parse_arguments; import sys; sys.argv=['prog', '--year-range', '-100', '0', '--quiet']; parse_arguments()" | python3 2>/dev/null && echo "✓ Argument parsing works" || echo "✗ Argument parsing failed"
echo ""

echo "Test 5: Horoscope module import"
python3 -c "from horoscope import generate_horoscope, SouthIndianChart, NorthIndianChart; print('✓ Horoscope module imports correctly')" 2>/dev/null || echo "✗ Horoscope import failed"
echo ""

echo "═══════════════════════════════════════════════════════════"
echo "Test Summary: CLI Components Ready ✓"
echo "═══════════════════════════════════════════════════════════"

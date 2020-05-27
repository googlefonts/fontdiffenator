#/usr/bin/env bash
set -e
python test_diff.py
python test_dump.py
python test_functional.py
python test_font.py


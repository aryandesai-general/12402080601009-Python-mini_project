#!/bin/bash
# -------------------------------------------------------------------
# ADIT AI Timetable Generator - 1-Click Public Host Launcher
# Generates an instant, secure public HTTPS URL for global sharing
# -------------------------------------------------------------------

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "======================================================================"
echo " 🎓 Starting ADIT AI Timetable Public Host..."
echo "======================================================================"

/opt/anaconda3/bin/python3 app.py --public

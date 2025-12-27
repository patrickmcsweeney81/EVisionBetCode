#!/bin/bash
# Quick start script for sport-specific pipeline
# Usage: ./quickstart.sh

echo "=================================================="
echo "  EVisionBet Sport-Specific Pipeline Quick Start"
echo "=================================================="
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "   Copy .env.example to .env and add your ODDS_API_KEY"
    exit 1
fi

# Check for API key
if ! grep -q "ODDS_API_KEY=.*[^=]" .env; then
    echo "❌ Error: ODDS_API_KEY not set in .env"
    echo "   Get your API key from https://theoddsapi.com/"
    exit 1
fi

echo "✓ Environment file configured"
echo ""

# Install dependencies if needed
if ! python -c "import requests" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install requests python-dotenv
    echo ""
fi

# Step 1: Run test
echo "Step 1: Testing normalization logic..."
python test_normalization.py
if [ $? -ne 0 ]; then
    echo "❌ Tests failed"
    exit 1
fi
echo ""

# Step 2: Extract odds (choose which sports)
echo "Step 2: Extract odds data"
echo "Options:"
echo "  1) Extract all sports (uses more API credits)"
echo "  2) Extract NFL only"
echo "  3) Extract NBA only"
echo "  4) Extract NFL + NBA only"
echo "  5) Skip extraction (use existing data)"
read -p "Choose option (1-5): " choice
echo ""

case $choice in
    1)
        echo "Running all sports extraction..."
        python run_all_sports.py
        ;;
    2)
        echo "Running NFL extraction only..."
        python raw_NFL.py
        python merge_raw_odds.py
        ;;
    3)
        echo "Running NBA extraction only..."
        python raw_NBA.py
        python merge_raw_odds.py
        ;;
    4)
        echo "Running NFL + NBA extraction..."
        python run_all_sports.py --sports NFL NBA
        ;;
    5)
        echo "Skipping extraction, using existing data..."
        if [ ! -f data/all_raw_odds.csv ]; then
            echo "❌ No existing data found. Please extract first."
            exit 1
        fi
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

if [ $? -ne 0 ]; then
    echo "❌ Extraction failed"
    exit 1
fi
echo ""

# Step 3: Calculate EV
echo "Step 3: Calculate EV opportunities..."
python calculate_ev.py
if [ $? -ne 0 ]; then
    echo "❌ EV calculation failed"
    exit 1
fi
echo ""

# Step 4: Show results
echo "=================================================="
echo "  ✅ Pipeline Complete!"
echo "=================================================="
echo ""
echo "Results:"
if [ -f data/all_raw_odds.csv ]; then
    raw_count=$(wc -l < data/all_raw_odds.csv)
    echo "  📊 Raw odds: $raw_count rows (data/all_raw_odds.csv)"
fi

if [ -f data/all_ev_hits.csv ]; then
    ev_count=$(wc -l < data/all_ev_hits.csv)
    echo "  💰 EV opportunities: $ev_count rows (data/all_ev_hits.csv)"
fi
echo ""
echo "Next steps:"
echo "  - View all_ev_hits.csv to see EV opportunities"
echo "  - Run backend API: uvicorn backend_api:app --reload"
echo "  - View docs: see SPORT_SPECIFIC_PIPELINE.md"
echo ""

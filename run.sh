#!/bin/bash

# DAP Market Research Agent Runner Script

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  DAP Market Research Agent${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Virtual environment not found!${NC}"
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}Virtual environment created${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if [ ! -f "venv/bin/pip" ]; then
    echo -e "${RED}Virtual environment corrupted. Please delete 'venv' folder and run again.${NC}"
    exit 1
fi

# Install/upgrade dependencies
echo "Checking dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}Dependencies installed${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}Warning: .env file not found!${NC}"
    echo "Please create .env file based on .env.example"
    echo "Would you like to create it now? (y/n)"
    read -r response
    if [ "$response" = "y" ]; then
        cp .env.example .env
        echo -e "${GREEN}.env file created. Please edit it with your API keys.${NC}"
        exit 0
    else
        exit 1
    fi
fi

# Parse command line arguments
MODE=${1:-once}

echo ""
echo -e "${BLUE}Running in mode: $MODE${NC}"
echo ""

# Run the agent
python -m src.main --mode "$MODE"

echo ""
echo -e "${GREEN}Done!${NC}"

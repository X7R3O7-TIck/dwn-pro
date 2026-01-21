#!/bin/bash
# =============================================================================
# Social Media Downloader - Setup Script
# =============================================================================
# This script creates a virtual environment and installs all dependencies
# using pyproject.toml
# =============================================================================

echo "=============================================="
echo "Social Media Downloader - Setup"
echo "=============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip -q

# Install the package in development mode
echo "Installing Social Media Downloader..."
pip install -e . -q

# Install development dependencies (optional)
echo "Installing development dependencies..."
pip install -e ".[dev]" -q 2>/dev/null || true

echo ""
echo "=============================================="
echo "✓ Setup Complete!"
echo "=============================================="
echo ""
echo "To run the server:"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo "Or in one command:"
echo "  source venv/bin/activate && python app.py"
echo ""
echo "Server will start at: http://localhost:8000"
echo ""
echo "Web UI: http://localhost:8000/"
echo "API Docs: http://localhost:8000/docs"
echo "=============================================="

#!/bin/bash
# Build script for Render deployment

echo "🔧 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🔧 Running database enum fix..."
python startup_fix_enum.py

echo "✅ Build completed successfully!"
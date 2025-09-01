#!/bin/bash

echo "🔧 Testing build process..."
echo "=========================="

echo "1. Installing dependencies..."
pip install -r requirements.txt

echo "2. Testing imports..."
python test_minimal.py

echo "3. Testing app creation..."
python test_app.py

echo "4. Testing gunicorn..."
python -c "import gunicorn; print('✅ Gunicorn available')"

echo "✅ Build test completed!"

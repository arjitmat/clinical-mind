#!/bin/bash

echo "🚀 Clinical Mind Demo Runner"
echo "============================="
echo ""

# Check if localhost:3000 is accessible
echo "📍 Checking if app is running on localhost:3000..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200"; then
    echo "✅ App is running!"
else
    echo "⚠️  Warning: Cannot reach localhost:3000"
    echo "   Make sure the Clinical Mind app is running before proceeding."
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Kill any existing Chrome processes
echo ""
echo "📍 Cleaning up Chrome processes..."
pkill -f "Google Chrome for Testing" 2>/dev/null
pkill -f "chrome" 2>/dev/null
sleep 1

# Run the demo
echo ""
echo "📍 Starting demo..."
echo ""
npm run demo
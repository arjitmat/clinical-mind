#!/bin/bash

echo "🔧 Chrome/Puppeteer Fix Script"
echo "================================"

# Kill any existing Chrome processes
echo "📍 Killing any existing Chrome processes..."
pkill -f "Google Chrome"
pkill -f "chrome"
pkill -f "Chromium"
sleep 1

# Check if processes are killed
if pgrep -f "Chrome" > /dev/null; then
    echo "⚠️  Some Chrome processes still running. Using force kill..."
    pkill -9 -f "Chrome"
    sleep 1
fi

# Clear Puppeteer cache
echo "📍 Clearing Puppeteer cache..."
rm -rf ~/.cache/puppeteer

# Reinstall Puppeteer browser
echo "📍 Reinstalling Puppeteer browser..."
cd "$(dirname "$0")"
npx puppeteer browsers install chrome

echo ""
echo "✅ Chrome fix complete!"
echo ""
echo "📝 Now try running the demo again:"
echo "   npm run demo"
echo ""
echo "💡 Additional tips if issues persist:"
echo "   - Close all Chrome browser windows manually"
echo "   - Restart your terminal"
echo "   - Run: npm install puppeteer@latest"
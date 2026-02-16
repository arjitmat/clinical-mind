#!/bin/bash

echo "🚀 Clinical Mind - Demo Automation Setup"
echo "========================================="
echo ""

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install Node.js first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

# Install dependencies
echo "📦 Installing Puppeteer..."
npm install

# Check if Chrome/Chromium is available
echo ""
echo "🌐 Checking browser..."
npx puppeteer browsers install chrome

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 How to use:"
echo "1. Make sure the app is running on localhost:3000"
echo "2. Start your screen recorder"
echo "3. Run: npm run demo"
echo "4. Sit back and let it run!"
echo ""
echo "💡 The demo will:"
echo "   - Open browser automatically"
echo "   - Navigate through the case"
echo "   - Type messages naturally"
echo "   - Demonstrate all features"
echo ""
echo "Ready to record your hackathon demo! 🎬"
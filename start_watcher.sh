#!/bin/bash

echo "🚀 Starting ScreenAI Coordinate Watcher"
echo "=====================================  "
echo ""
echo "📁 Watching: screenshots/objednavka/"
echo "📄 Updating: flows/objednavka.yaml"
echo ""
echo "✅ Start your Maestro test in another terminal:"
echo "   maestro test flows/objednavka.yaml"
echo ""
echo "🔍 The watcher will automatically update coordinates when new screenshots are detected."
echo "📝 Press Ctrl+C to stop the watcher"
echo ""

# Create screenshots directory if it doesn't exist
mkdir -p screenshots/objednavka

# Start the watcher
python watch_screenshots.py
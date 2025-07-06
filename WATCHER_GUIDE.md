# 🔍 Real-time Screenshot Watcher Guide

This guide shows you how to use the real-time screenshot watcher to automatically update YAML coordinates as Maestro runs.

## 🚀 Quick Start

### Step 1: Start the Watcher (Terminal 1)
```bash
./start_watcher.sh
```

OR manually:
```bash
python watch_screenshots.py
```

### Step 2: Run Maestro (Terminal 2)
```bash
maestro test flows/objednavka.yaml
```

## 🎯 How It Works

1. **Watcher monitors** `screenshots/objednavka/` directory
2. **When new PNG files appear**, it automatically runs analysis
3. **Updates coordinates** in `flows/objednavka.yaml` 
4. **Next Maestro run** uses updated coordinates instead of TODO placeholders

## 📋 Expected Output

### Terminal 1 (Watcher):
```
🚀 Starting ScreenAI Coordinate Watcher
📁 Watching: screenshots/objednavka/
📄 Updating: flows/objednavka.yaml

INFO: 👀 Watching for screenshots in: screenshots/objednavka
INFO: 📄 Will update coordinates in: flows/objednavka.yaml
INFO: 🚀 Start your Maestro test now!

INFO: 🖼️  New screenshot detected: objednavka_step_11_20250706_164057.png
INFO: 🔍 Analyzing screenshot: screenshots/objednavka/objednavka_step_11_20250706_164057.png
INFO: ✅ Updated coordinates in objednavka.yaml
```

### Terminal 2 (Maestro):
```
✅ Take screenshot screenshots/objednavka/objednavka_step_11_20250706_164057
✅ Run analyze_screenshot.js
✅ Tap on point (45%,60%)  # ← Real coordinates instead of TODO%,TODO%
```

## 🔧 Configuration

The watcher is configured to:
- **Watch directory**: `screenshots/objednavka/`
- **Update file**: `flows/objednavka.yaml`
- **File pattern**: `*.png` files containing "objednavka"
- **Analysis timeout**: 30 seconds per screenshot

## 🛠️ Troubleshooting

### Watcher not detecting files:
- Ensure `screenshots/objednavka/` directory exists
- Check file permissions
- Verify PNG files are being created by Maestro

### Analysis failing:
- Check Python dependencies are installed
- Verify YAML file exists and is writable
- Check screenshot file size and format

### No coordinate updates:
- Verify OCR is detecting elements correctly
- Check matcher is finding suitable elements
- Review analysis logs for warnings

## 🎯 Tips

1. **Start watcher first** before running Maestro
2. **Keep both terminals open** during testing
3. **Check watcher logs** if coordinates aren't updating
4. **Stop watcher with Ctrl+C** when done testing

## 📝 Files Involved

- `watch_screenshots.py` - Main watcher script
- `start_watcher.sh` - Convenience startup script  
- `flows/objednavka.yaml` - YAML file that gets updated
- `screenshots/objednavka/` - Directory being monitored
- `src/main.py` - Analysis script called by watcher
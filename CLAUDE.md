# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ScreenAI Test Automation Tool - A Python application that uses Microsoft's OmniParser model to automatically generate Maestro test flows from text-based test case descriptions by analyzing UI screenshots and detecting interactive elements.

## Detailed Implementation Plan

### Technology Stack

- **UI Detection Model**: Microsoft OmniParser (instead of ScreenAI which isn't publicly available)
  - OmniParser V2: Faster inference (0.6s/frame), better accuracy
  - Combines YOLOv8 for element detection + Florence-2 for element description
  - Returns bounding boxes and semantic descriptions of UI elements
- **Screenshot Tool**: Selenium WebDriver for web applications
- **Test Framework**: Maestro for UI test automation
- **Language**: Python 3.12

### Core Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│                 │     │                  │     │                 │
│  Test Case      ├────►│   Main           ├────►│  Screenshot     │
│  Parser         │     │   Orchestrator   │     │  Capture        │
│                 │     │                  │     │                 │
└─────────────────┘     └────────┬─────────┘     └────────┬────────┘
                                 │                          │
                                 │                          ▼
┌─────────────────┐     ┌────────▼─────────┐     ┌─────────────────┐
│                 │     │                  │     │                 │
│  Maestro Flow   │◄────┤   UI Element     │◄────┤  OmniParser     │
│  Generator      │     │   Matcher        │     │  Integration    │
│                 │     │                  │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### Detailed Module Specifications

#### 1. Test Case Parser (`src/parser.py`)
- Parse numbered instructions from `.txt` files
- Extract action types: `open`, `wait`, `find`, `tap`, `enter`, `take screenshot`
- Build structured test flow representation
- Handle multi-step scenarios with page transitions

#### 2. Screenshot Module (`src/screenshot.py`)
- Use Selenium WebDriver for web applications
- Support headless mode for CI/CD
- Save screenshots with timestamps
- Return image dimensions for coordinate conversion

#### 3. OmniParser Integration (`src/vision.py`)
- Load OmniParser models (YOLOv8 + Florence-2)
- Process screenshots to detect UI elements
- Return structured data:
  ```python
  {
      'bbox': [x1, y1, x2, y2],  # Pixel coordinates
      'description': 'Login button',  # Semantic description
      'confidence': 0.95
  }
  ```

#### 4. UI Element Matcher (`src/matcher.py`)
- Match test case descriptions to detected elements
- Use fuzzy string matching for flexibility
- Handle synonyms (e.g., "button" vs "btn")
- Prioritize elements by confidence and position

#### 5. Maestro Flow Generator (`src/generator.py`)
- Convert pixel coordinates to percentages
- Generate YAML format compatible with Maestro
- Support multiple action types:
  - `tapOn` with point coordinates
  - `inputText` for text entry
  - `waitForAnimationToEnd` for delays
  - `assertVisible` for verification
  - `scroll` for scrolling actions
  - `swipe` for gesture-based navigation

#### 6. Main Orchestrator (`src/main.py`)
- CLI interface for running tests
- Coordinate the complete workflow
- Handle errors gracefully
- Support batch processing of test cases

### Implementation Steps

1. **Setup OmniParser**
   ```bash
   git clone https://github.com/microsoft/OmniParser
   # Download model weights from HuggingFace
   huggingface-cli download microsoft/OmniParser-v2.0
   ```

2. **Project Structure**
   ```
   ScreenAI/
   ├── src/
   │   ├── __init__.py
   │   ├── main.py
   │   ├── parser.py
   │   ├── screenshot.py
   │   ├── vision.py
   │   ├── matcher.py
   │   └── generator.py
   ├── tests/
   ├── flows/           # Generated Maestro flows
   ├── screenshots/     # Captured screenshots
   ├── test_cases/      # Input test cases
   ├── weights/         # OmniParser model weights
   ├── requirements.txt
   └── README.md
   ```

3. **Dependencies** (requirements.txt)
   ```
   selenium==4.15.0
   webdriver-manager==4.0.1
   torch>=2.0.0
   torchvision>=0.15.0
   transformers>=4.30.0
   ultralytics>=8.0.0
   pillow>=10.0.0
   pyyaml>=6.0
   numpy>=1.24.0
   opencv-python>=4.8.0
   fuzzywuzzy>=0.18.0
   python-Levenshtein>=0.21.0
   ```

### Coordinate System Conversion

OmniParser returns pixel coordinates `[x1, y1, x2, y2]`. For Maestro:

```python
def pixel_to_percentage(bbox, image_width, image_height):
    x1, y1, x2, y2 = bbox
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    
    percent_x = (center_x / image_width) * 100
    percent_y = (center_y / image_height) * 100
    
    # Note: Maestro requires format without spaces
    return f"{percent_x:.0f}%,{percent_y:.0f}%"
```

### Critical Requirements

**IMPORTANT: All tapOn commands must use point coordinates, never text:**

```yaml
# CORRECT - Always use point coordinates
- tapOn:
    point: 73%,19%

# INCORRECT - Never use text-based tapOn
- tapOn:
    text: "some text"
    optional: true
```

This is essential for Flutter web compatibility and reliable test execution. If UI elements cannot be found during analysis, the generator will create placeholder tapOn commands with `"TODO%,TODO%"` coordinates that require manual updating.

### Slovak Language OCR Issues

OCR (Optical Character Recognition) can have trouble with Slovak characters, leading to common misreadings:

**Common OCR errors:**
- `L` → `I` (e.g., "Lekara" becomes "Iekara")
- `l` → `i` (e.g., "vyhladat" becomes "vyhiadat")

**Solution:** The matcher includes Slovak character normalization to handle these OCR errors automatically. When matching fails, check the OCR text in the analysis summary files for these common character substitutions.

### Example Workflow

1. Input: `testCase1.txt`
2. Parse: Extract "find login text field and tap on it"
3. Screenshot: Capture current screen
4. Detect: OmniParser finds input field at [100, 200, 300, 250]
5. Match: "login text field" → detected input element
6. Generate: `tapOn: point: "10.4%, 11.6%"` or `tapOn: text: "login"`
7. Output: `flows/testCase1.yaml`

### Generated Maestro Flow Format

#### For Web Applications:
```yaml
url: https://testsk.unilabs.pro
---
- launchApp
- waitForAnimationToEnd:
    timeout: 5000
- tapOn:
    point: 73%,19%
- inputText: admin@unilabs.sk
- tapOn:
    point: 73%,26%
- inputText: malina
- tapOn:
    point: 73%,39%
- scroll:
    direction: DOWN
- swipe:
    start: 50%,80%
    end: 50%,20%
- waitForAnimationToEnd:
    timeout: 3000
```

#### For Mobile Applications:
```yaml
appId: com.example.app
---
- launchApp
- tapOn:
    point: 25%,35%
- inputText: test input
```

### Error Handling

- Element not found: Log warning, skip action
- Multiple matches: Use confidence scores and position heuristics
- Screenshot failure: Retry with timeout
- Model loading issues: Clear error messages with setup instructions

### Development Commands

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Download OmniParser models
python scripts/download_models.py

# Run single test case
python src/main.py test_cases/testCase1.txt

# Run all test cases
python src/main.py test_cases/

# Run with debug output
python src/main.py --debug test_cases/testCase1.txt
```

## Running Generated Maestro Flows

### Web Application Testing
Maestro supports web browser testing using the `url` configuration:

```bash
# Test web application flow
maestro test flows/testCase1.yaml

# Run with Maestro Studio for debugging
maestro studio flows/testCase1.yaml
```

### Flow Execution Results
- **Success**: All commands execute and elements are found
- **Warnings**: Elements not found but marked as `optional: true`
- **Failures**: Required elements not found or commands fail

Example successful web test output:
```
Web support is in Beta. We would appreciate your feedback!

 > Flow testCase1
Launch app "https://testsk.unilabs.pro"... COMPLETED
Wait for animation to end... COMPLETED
Tap on (Optional) "login"... WARNED
Input text admin@unilabs.sk... COMPLETED
Tap on (Optional) "password"... WARNED
Input text malina... COMPLETED
Tap on (Optional) "prihlasit"... WARNED
Wait for animation to end... COMPLETED
```

### Testing Strategy

- Unit tests for each module
- Integration tests with sample screenshots
- Mock OmniParser for faster testing
- Validate generated Maestro flows

### Performance Considerations

- OmniParser V2: ~0.6s per screenshot on GPU
- Cache detection results for repeated elements
- Batch process multiple test cases
- Option for lightweight mode with lower resolution

### Web vs Mobile Testing Configuration

#### Web Applications
- **Config**: Use `url: https://example.com` instead of `appId`
- **Launch**: Simple `launchApp` command opens the URL in browser
- **Elements**: Use `text` selectors with `optional: true` for flexibility
- **Support**: Maestro web support is currently in Beta

#### Mobile Applications  
- **Config**: Use `appId: com.example.app` for mobile apps
- **Launch**: `launchApp` launches the specified mobile application
- **Elements**: Can use precise `point` coordinates or `text` selectors
- **Support**: Full production support for iOS and Android

### Element Selection Strategies

1. **Text-based Selection** (Recommended for standard web):
   ```yaml
   - tapOn:
       text: login
       optional: true
   ```

2. **Coordinate-based Selection** (**Required for Flutter Web**):
   ```yaml
   - tapOn:
       point: 73%,19%
   ```

3. **Hybrid Approach** (Best reliability):
   - Use text selectors with `optional: true` as primary
   - Fall back to coordinates when text matching fails

### Flutter Web Compatibility

**Important**: For Flutter web applications, **percentage-based coordinates are the primary working method**:

- **Text selectors often fail** with Flutter web apps due to shadow DOM and rendering differences
- **Percentage coordinates work reliably** because they are resolution-independent
- **All tapOn commands should use `point` coordinates** for Flutter web apps

#### Generated Flow Format for Flutter Web:
```yaml
url: https://flutter-web-app.com
---
- launchApp
- waitForAnimationToEnd:
    timeout: 5000
- tapOn:
    point: 73%,19%  # Username field
- inputText: admin@example.com
- tapOn:
    point: 73%,26%  # Password field  
- inputText: mypassword
- tapOn:
    point: 73%,39%  # Login button
- waitForAnimationToEnd:
    timeout: 3000
```

#### Coordinate System
- **X-axis**: 0% (left) to 100% (right)
- **Y-axis**: 0% (top) to 100% (bottom)
- **Format**: `X%,Y%` (no spaces, no quotes, integer percentages)
- **Example**: `73%,19%` for center of username field
- **Important**: Maestro requires this exact format - spaces or quotes will cause parsing errors

#### Why Percentage Coordinates Work Better for Flutter Web:
1. **Resolution Independence**: Works across different screen sizes
2. **Shadow DOM Compatibility**: Bypasses Flutter's virtual DOM structure
3. **Reliable Targeting**: Direct pixel-based interaction
4. **Cross-Device Support**: Same coordinates work on mobile and desktop

### Scroll and Swipe Commands

#### Scroll Commands
**WARNING**: The `scroll` command syntax varies between Maestro versions and may not be supported in all versions.

For simple scrolling actions, you can try the `scroll` command (if supported):

```yaml
# Basic directional scroll (may not work in all versions)
- scroll:
    direction: DOWN  # UP, DOWN, LEFT, RIGHT

# Scroll from specific point (may not work in all versions)
- scroll:
    element: 
      point: 50%,50%
    direction: DOWN

# Scroll with distance (may not work in all versions)
- scroll:
    direction: DOWN
    distance: 500
```

**RECOMMENDED**: Use `swipe` commands instead for reliable cross-version compatibility:

```yaml
# Reliable scrolling using swipe commands
- swipe:
    start: 50%,80%
    end: 50%,20%
```

#### Swipe Commands
For gesture-based navigation, use the `swipe` command:

```yaml
# Coordinate-based swipe (most common)
- swipe:
    start: 50%,80%
    end: 50%,20%

# Direction-based swipe
- swipe:
    direction: UP  # UP, DOWN, LEFT, RIGHT

# Direction with element
- swipe:
    direction: DOWN
    element:
      point: 50%,50%
```

**Important**: 
- Use `start` and `end` (NOT `from` and `to`) for coordinate-based swipes
- Duration parameter is not supported in Maestro swipe commands
- Swipe coordinates use the same percentage format as tapOn: `X%,Y%`

#### Common Use Cases and Swipe Distances

```yaml
# Small scroll (reveal next item)
- swipe:
    start: 50%,70%
    end: 50%,30%

# Medium scroll (standard page scroll)
- swipe:
    start: 50%,80%
    end: 50%,20%

# Large scroll (reveal more content)
- swipe:
    start: 50%,85%
    end: 50%,15%

# Extra large scroll (maximum content reveal)
- swipe:
    start: 50%,90%
    end: 50%,10%

# Horizontal swipe (e.g., carousel navigation)
- swipe:
    start: 80%,50%
    end: 20%,50%

# Multiple swipes for long content
- swipe:
    start: 50%,85%
    end: 50%,15%
- swipe:
    start: 50%,85%
    end: 50%,15%
- waitForAnimationToEnd:
    timeout: 1000
```

#### Version Compatibility Notes
- **Scroll commands**: May not work in all Maestro versions (e.g., `direction: DOWN` property not recognized)
- **Swipe commands**: Work reliably across all Maestro versions
- **Best Practice**: Always use `swipe` commands for scrolling to ensure compatibility
- **Error**: If you see "Unknown Property: direction" use swipe instead of scroll



# checking logs:

/Users/andrejpt/.maestro/tests/2025-07-06_160255
/*
 * Old JavaScript (ES3/ES5) for Maestro to analyze screenshots with OmniParser
 * Uses only Maestro's built-in capabilities and Java interop - NO Node.js
 */

// Get parameters from Maestro environment (direct variable access)
var screenshotPath = SCREENSHOT_PATH || "";
var testName = TEST_NAME || "";
var actionIndex = ACTION_INDEX || "";

function log(message) {
    console.log(message);
}

function main() {
    try {
        log("=== MAESTRO JAVASCRIPT ANALYSIS SCRIPT ===");
        log("Screenshot path: " + screenshotPath);
        log("Test name: " + testName);
        log("Action index: " + actionIndex);
        
        if (!screenshotPath || !testName || !actionIndex) {
            log("ERROR: Missing required environment variables");
            log("Required: SCREENSHOT_PATH, TEST_NAME, ACTION_INDEX");
            throw new Error("Missing required environment variables");
        }
        
        // Log the analysis request for external processing
        log("📊 ANALYSIS REQUEST:");
        log("  Screenshot: " + screenshotPath);
        log("  YAML file: flows/" + testName + ".yaml");
        log("  Action index: " + actionIndex);
        log("");
        log("🔧 To update coordinates, run:");
        log("  python -m src.main --analyze-screenshot " + screenshotPath + " --update-yaml flows/" + testName + ".yaml");
        log("");
        log("✅ JavaScript analysis step completed successfully");
        log("⚠️  TODO coordinates will be used until external analysis updates them");
        
        // Note: Cannot set variables in Maestro's sealed environment
        
    } catch (error) {
        log("❌ Error in analysis script: " + error.message);
        // Don't throw - let Maestro continue with TODO coordinates
        log("⚠️  Continuing with placeholder coordinates");
    }
}

// Execute the main function
main();
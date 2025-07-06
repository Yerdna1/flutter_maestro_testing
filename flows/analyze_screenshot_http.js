/*
 * HTTP-based screenshot analysis for Maestro
 * Calls local HTTP server to update coordinates automatically
 */

// Get parameters from Maestro environment
var screenshotPath = SCREENSHOT_PATH || "";
var testName = TEST_NAME || "";
var actionIndex = ACTION_INDEX || "";

function log(message) {
    console.log(message);
}

function main() {
    try {
        log("=== MAESTRO HTTP ANALYSIS SCRIPT ===");
        log("Screenshot: " + screenshotPath);
        log("Test: " + testName);
        log("Index: " + actionIndex);
        
        if (!screenshotPath || !testName || !actionIndex) {
            log("ERROR: Missing required environment variables");
            throw new Error("Missing required environment variables");
        }
        
        // Make HTTP request to coordinate analysis server
        var serverUrl = "http://localhost:8765/analyze";
        var requestData = {
            screenshot_path: screenshotPath,
            yaml_path: "flows/" + testName + ".yaml",
            action_index: actionIndex
        };
        
        log("🔗 Calling coordinate analysis server...");
        log("URL: " + serverUrl);
        
        // Make HTTP POST request
        var request = new XMLHttpRequest();
        request.open("POST", serverUrl, false); // Synchronous request
        request.setRequestHeader("Content-Type", "application/json");
        
        request.onreadystatechange = function() {
            if (request.readyState === 4) {
                if (request.status === 200) {
                    var response = JSON.parse(request.responseText);
                    if (response.success) {
                        log("✅ Coordinates updated successfully!");
                        if (response.output) {
                            log("Output: " + response.output);
                        }
                    } else {
                        log("❌ Analysis failed: " + response.error);
                    }
                } else {
                    log("❌ HTTP request failed: " + request.status);
                    log("Response: " + request.responseText);
                }
            }
        };
        
        // Send the request
        request.send(JSON.stringify(requestData));
        
        log("✅ HTTP analysis request completed");
        
    } catch (error) {
        log("❌ Error in HTTP analysis: " + error.message);
        log("⚠️ Falling back to manual coordinate update");
        log("🔧 Run: python -m src.main --analyze-screenshot " + screenshotPath + " --update-yaml flows/" + testName + ".yaml");
    }
}

// Execute the main function
main();
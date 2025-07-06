/*
 * Old JavaScript (ES3/ES5) compatible coordinate updater for Maestro
 * This script pauses the flow, calls external Python analysis, and updates coordinates
 * NO Node.js dependencies - only standard JavaScript and Java interop
 */

// Global variables for coordination
var screenshotPath = maestro.env.SCREENSHOT_PATH || "";
var testName = maestro.env.TEST_NAME || "";
var actionIndex = maestro.env.ACTION_INDEX || "";
var yamlPath = maestro.env.YAML_PATH || "";

function log(message) {
    maestro.log(message);
}

function updateCoordinates() {
    try {
        log("=== MAESTRO COORDINATE UPDATE SCRIPT ===");
        log("Screenshot path: " + screenshotPath);
        log("Test name: " + testName);
        log("Action index: " + actionIndex);
        log("YAML path: " + yamlPath);
        
        if (!screenshotPath || !testName || !yamlPath) {
            throw new Error("Missing required environment variables: SCREENSHOT_PATH, TEST_NAME, YAML_PATH");
        }
        
        // Use Java's ProcessBuilder to execute Python script
        var ProcessBuilder = Java.type("java.lang.ProcessBuilder");
        var File = Java.type("java.io.File");
        var Scanner = Java.type("java.util.Scanner");
        
        // Build command to run Python analysis
        var command = [
            "python3",
            "-m", "src.main",
            "--analyze-screenshot", screenshotPath,
            "--update-yaml", yamlPath,
            "--test-name", testName
        ];
        
        log("Executing command: " + command.join(" "));
        
        // Create and start process
        var pb = new ProcessBuilder(command);
        pb.directory(new File("/Volumes/DATA/Python/ScreenAI"));
        pb.redirectErrorStream(true);
        
        var process = pb.start();
        
        // Read output
        var scanner = new Scanner(process.getInputStream());
        var output = "";
        while (scanner.hasNextLine()) {
            var line = scanner.nextLine();
            output += line + "\n";
            log("Python output: " + line);
        }
        scanner.close();
        
        // Wait for completion
        var exitCode = process.waitFor();
        
        if (exitCode === 0) {
            log("✅ Coordinate analysis completed successfully");
            log("Updated YAML file: " + yamlPath);
            
            // Signal to Maestro that coordinates have been updated
            maestro.env.COORDINATES_UPDATED = "true";
            
        } else {
            log("❌ Python analysis failed with exit code: " + exitCode);
            log("Output: " + output);
            throw new Error("Coordinate analysis failed");
        }
        
    } catch (error) {
        log("❌ Error in coordinate update: " + error.message);
        throw error;
    }
}

// Execute the coordinate update
updateCoordinates();
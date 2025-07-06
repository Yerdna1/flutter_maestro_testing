#!/usr/bin/env python3
"""
Coordinate Analysis HTTP Server - Allows Maestro JavaScript to trigger coordinate updates
"""
import logging
import subprocess
import sys
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class CoordinateHandler(BaseHTTPRequestHandler):
    """HTTP handler for coordinate analysis requests"""
    
    def do_POST(self):
        """Handle POST requests for coordinate analysis"""
        try:
            # Parse request
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            screenshot_path = data.get('screenshot_path')
            yaml_path = data.get('yaml_path', 'flows/objednavka.yaml')
            action_index = data.get('action_index', '0')
            
            logger.info(f"🔍 Analysis request: {screenshot_path}")
            
            # Validate paths
            if not screenshot_path:
                self.send_error_response(400, "Missing screenshot_path")
                return
                
            screenshot_file = Path(screenshot_path)
            yaml_file = Path(yaml_path)
            
            if not screenshot_file.exists():
                self.send_error_response(404, f"Screenshot not found: {screenshot_path}")
                return
                
            if not yaml_file.exists():
                self.send_error_response(404, f"YAML file not found: {yaml_path}")
                return
            
            # Run coordinate analysis
            result = self.analyze_coordinates(screenshot_file, yaml_file)
            
            if result['success']:
                logger.info(f"✅ Updated coordinates in {yaml_file.name}")
                self.send_json_response(200, result)
            else:
                logger.error(f"❌ Analysis failed: {result['error']}")
                self.send_json_response(500, result)
                
        except json.JSONDecodeError:
            self.send_error_response(400, "Invalid JSON")
        except Exception as e:
            logger.error(f"💥 Server error: {e}")
            self.send_error_response(500, str(e))
    
    def do_GET(self):
        """Handle GET requests for health check"""
        if self.path == '/health':
            self.send_json_response(200, {'status': 'healthy', 'service': 'coordinate-analysis'})
        else:
            self.send_error_response(404, "Not found")
    
    def analyze_coordinates(self, screenshot_path: Path, yaml_path: Path):
        """Run the coordinate analysis"""
        try:
            cmd = [
                sys.executable,
                "-m", "src.main",
                "--analyze-screenshot", str(screenshot_path),
                "--update-yaml", str(yaml_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': 'Coordinates updated successfully',
                    'output': result.stdout.strip() if result.stdout else ''
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr.strip() if result.stderr else 'Unknown error',
                    'output': result.stdout.strip() if result.stdout else ''
                }
                
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Analysis timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_json_response(self, status_code: int, data: dict):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS
        self.end_headers()
        
        response = json.dumps(data, indent=2)
        self.wfile.write(response.encode('utf-8'))
    
    def send_error_response(self, status_code: int, message: str):
        """Send error response"""
        self.send_json_response(status_code, {'success': False, 'error': message})
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.address_string()} - {format % args}")

def main():
    """Start the coordinate analysis server"""
    host = 'localhost'
    port = 8765
    
    logger.info(f"🚀 Starting Coordinate Analysis Server")
    logger.info(f"📡 Listening on http://{host}:{port}")
    logger.info(f"🔍 Ready to analyze screenshots and update YAML coordinates")
    logger.info(f"💡 Health check: http://{host}:{port}/health")
    logger.info(f"📝 Press Ctrl+C to stop")
    
    server = HTTPServer((host, port), CoordinateHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("🛑 Stopping server...")
        server.shutdown()
        logger.info("👋 Server stopped")

if __name__ == "__main__":
    main()
import sys
import os

# Add the github_hub directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'github_hub'))

# Debug: Print environment variable status
print(f"SUPABASE_URL env: {os.environ.get('SUPABASE_URL', 'NOT SET')[:50]}")
print(f"SUPABASE_KEY env: {'SET' if os.environ.get('SUPABASE_KEY') else 'NOT SET'}")

try:
    from server import app
    print("Server imported successfully")
except Exception as e:
    print(f"Error importing server: {e}")
    import traceback
    traceback.print_exc()
    
    # Create a minimal Flask app that returns the error
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route('/')
    def error_page():
        return f"<h1>Import Error</h1><pre>{str(e)}</pre>", 500
    
    @app.route('/api/<path:path>')
    def api_error(path):
        return jsonify({"error": str(e)}), 500

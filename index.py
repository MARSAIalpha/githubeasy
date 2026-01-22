import os
import sys

# Ensure current directory is in path (Vercel sometimes needs this explicit add)
sys.path.append(os.path.dirname(__file__))

try:
    from github_hub.server import app
except Exception as e:
    # Fallback for debugging import errors on Vercel
    from flask import Flask, jsonify
    import traceback
    
    app = Flask(__name__)
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        return jsonify({
            "error": "Failed to import application", 
            "details": str(e),
            "traceback": traceback.format_exc()
        }), 500

if __name__ == "__main__":
    app.run()

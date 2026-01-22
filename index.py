import os
import sys

# Ensure current directory is in path (Vercel sometimes needs this explicit add)
sys.path.append(os.path.dirname(__file__))

# Debug environment
print("=== Vercel Debug Info ===")
print(f"Current dir: {os.getcwd()}")
print(f"Script dir: {os.path.dirname(__file__)}")
print(f"sys.path: {sys.path[:5]}")
print(f"SUPABASE_URL set: {bool(os.environ.get('SUPABASE_URL'))}")
print(f"SUPABASE_KEY set: {bool(os.environ.get('SUPABASE_KEY'))}")

try:
    from github_hub.server import app
    print("Server imported successfully!")
except Exception as e:
    # Fallback for debugging import errors on Vercel
    from flask import Flask, jsonify
    import traceback
    
    error_details = traceback.format_exc()
    print(f"IMPORT ERROR: {e}")
    print(error_details)
    
    app = Flask(__name__)
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        return f'''
        <html>
        <head><title>Debug Error</title></head>
        <body style="background:#111;color:#0f0;font-family:monospace;padding:20px;">
        <h1 style="color:#f00;">Import Error</h1>
        <pre style="background:#222;padding:20px;overflow:auto;">{error_details}</pre>
        <h2>Environment</h2>
        <pre>
SUPABASE_URL: {bool(os.environ.get('SUPABASE_URL'))}
SUPABASE_KEY: {bool(os.environ.get('SUPABASE_KEY'))}
CWD: {os.getcwd()}
        </pre>
        </body>
        </html>
        ''', 500

if __name__ == "__main__":
    app.run()

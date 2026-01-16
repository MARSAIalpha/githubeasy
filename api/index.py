
import sys
import os

# Add the github_hub directory to sys.path
# This allows importing server.py and allows server.py to import its sibling modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'github_hub'))

from server import app

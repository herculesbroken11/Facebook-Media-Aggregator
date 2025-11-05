"""
WSGI entry point for Gunicorn deployment
"""
import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app
from app import app

# Gunicorn looks for 'application' by default
application = app

if __name__ == "__main__":
    application.run()


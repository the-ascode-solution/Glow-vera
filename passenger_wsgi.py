import sys
import os

# Set up the path to the application
sys.path.insert(0, os.path.dirname(__file__))

# Ensure instance directory exists for SQLite
instance_path = os.path.join(os.path.dirname(__file__), 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path, exist_ok=True)

# Import the Flask app
from app import app as application

# This is the entry point for Passenger
if __name__ == "__main__":
    application.run()

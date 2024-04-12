#!/bin/bash

# Create a virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Update pip to the latest version
echo "Updating pip..."
pip install --upgrade pip

# Install project dependencies from requirements.txt
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "Setup complete. Activate the environment using 'source venv/bin/activate'."

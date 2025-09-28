#!/bin/bash
echo "Setting up AI Study Coach..."

# Backend setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd ai-study-coach-dashboard
npm install
cd ..

echo "Setup complete! See README.md for next steps."
#!/bin/bash
echo "Setting up AI Study Coach..."

# Backend setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Ollama setup
echo "Setting up Ollama..."
echo "Please install Ollama from https://ollama.ai/download"
echo "After installation, run the following commands:"
echo "  ollama pull tinyllama"
echo "  ollama serve"
read -p "Press Enter after you've installed Ollama and pulled the tinyllama model..."

# Frontend setup
cd ai-study-coach-dashboard
npm install
cd ..

echo "Setup complete! See README.md for next steps."
echo ""
echo "To start the application:"
echo "1. Make sure Ollama is running: ollama serve"
echo "2. Start Neo4j database"
echo "3. Start backend: cd backend && python app.py"
echo "4. Start frontend: cd ai-study-coach-dashboard && npm start"
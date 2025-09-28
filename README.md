# AI Study Coach - HackUMBC 2025

An intelligent academic advisory system that leverages Neo4j graph database and local AI to analyze student performance patterns and generate personalized study recommendations.

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [AI Model Integration](#ai-model-integration)
- [Future Enhancements](#future-enhancements)
- [Contributing](#contributing)

## Overview

The AI Study Coach is a full-stack application that analyzes academic data using graph database relationships to identify patterns among similar students. By comparing a target student with peers who have similar learning styles but better performance, the system generates data-driven study recommendations using local AI processing.

### Key Capabilities
- **Peer Analysis**: Finds students with similar learning styles and academic patterns
- **Performance Gap Analysis**: Identifies specific areas where successful peers differ
- **AI-Powered Recommendations**: Uses local language models to generate personalized advice
- **Interactive Dashboard**: Modern React interface for exploring student data and recommendations

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │   Flask API     │    │   Neo4j Database│
│   (Port 3000)   │◄──►│   (Port 5000)   │◄──►│   (Port 7687)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   AI Model      │
                       │   (Ollama)    │
                       └─────────────────┘
```

## Features

### Data Analysis
- **Student Similarity Matching**: Uses graph relationships to find students with similar learning styles
- **Performance Comparison**: Calculates GPA gaps and course completion patterns
- **Behavioral Pattern Analysis**: Identifies differences in study approaches between high and low performers

### AI Integration
- **Local Language Model**: Uses Ollama for generating contextual study advice
- **Personalized Recommendations**: Tailors advice based on learning style and performance gaps
- **Fallback Strategies**: Provides rule-based recommendations when AI is unavailable

### User Interface
- **Interactive Dashboard**: Overview of student demographics and learning style distribution
- **Student Selection**: Dropdown interface for analyzing specific students
- **Visualization**: Charts showing performance comparisons and learning style breakdowns
- **Responsive Design**: Works on desktop and mobile devices

## Technology Stack

### Backend
- **Python 3.8+**: Core programming language
- **Flask**: Web framework for API endpoints
- **Neo4j**: Graph database for storing student relationships
- **Ollama**: Local AI model server for generating contextual recommendations
- **NumPy/Pandas**: Data processing and analysis

### Frontend
- **React 18**: User interface framework
- **Axios**: HTTP client for API communication
- **Recharts**: Data visualization library
- **Lucide React**: Icon components
- **Custom CSS**: Responsive styling without external frameworks

### Database
- **Neo4j Community Edition**: Graph database
- **Cypher**: Query language for graph operations
- **Synthetic Dataset**: 500 students, 100 courses, 9,920+ relationships

## Project Structure

```
hackumbc-2025/
├── backend/
│   ├── app.py                      # Flask API server
│   └── requirements.txt            # Backend dependencies
├── simple_ai_coach.py              # Core AI recommendation engine
├── automated_import.py             # Database import automation
├── generate_synthetic_dataset.py   # Dataset generation script
├── umbc_data/                      # Generated dataset
│   ├── csv/                        # CSV files for bulk import
│   └── cypher/                     # Cypher scripts for Neo4j
└── README.md

ai-study-coach-dashboard/
├── src/
│   ├── App.js                      # Main React component
│   ├── App.css                     # Styling
│   └── index.js                    # React entry point
├── public/
├── package.json                    # Frontend dependencies
└── README.md
```

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Node.js 14 or higher
- Docker (recommended for Neo4j)
- 8GB+ RAM
- 2GB free disk space

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd hackumbc-2025
```

### Step 2: Set Up Neo4j Database
```bash
# Using Docker (recommended)
docker run -d \
  --name umbc-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/yourpassword \
  -e NEO4J_PLUGINS='["apoc"]' \
  neo4j:5-community

# Wait for startup, then access: http://localhost:7474
# Login: neo4j / yourpassword
```
### Step 2.5: Set Up Ollama
```bash
# Install Ollama from https://ollama.ai/download
# Pull a lightweight model
ollama pull tinyllama

# Test Ollama is working
ollama run tinyllama "Hello"
```

### Step 3: Generate and Import Dataset
```bash
# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate synthetic dataset
python generate_synthetic_dataset.py

# Import data to Neo4j
python automated_import.py
```

### Step 4: Set Up Backend API
```bash
# Install additional backend dependencies
pip install flask flask-cors requests

# Start Flask API
cd backend
python app.py
# API available at: http://localhost:5000
```

### Step 5: Set Up Frontend
```bash
# In a new terminal, navigate to frontend directory
cd ai-study-coach-dashboard

# Install Node.js dependencies
npm install

# Start React development server
npm start
# Frontend available at: http://localhost:3000
```

## Usage

### Basic Workflow
1. **Start all services**: Neo4j, Flask API, React frontend
2. **Access dashboard**: Open http://localhost:3000
3. **Explore data**: View student statistics and learning style distribution
4. **Get recommendations**: 
   - Use "Try Demo" for random student analysis
   - Or select specific student from "Analyze Student" tab
5. **Review insights**: AI-generated recommendations based on peer analysis

### Example Use Cases
- **Academic Advisor**: Identify students who might benefit from specific study strategies
- **Student Self-Assessment**: Compare performance with similar peers
- **Research Tool**: Analyze patterns in student success across different learning styles

## API Documentation

### Core Endpoints

#### GET /api/recommendations
Returns AI-generated study recommendations for a random student.

**Response:**
```json
{
  "student": {
    "name": "John Doe",
    "learningStyle": "Visual",
    "preferredPace": "Standard"
  },
  "analysis": {
    "target_gpa": 3.2,
    "similar_avg_gpa": 3.6,
    "gpa_gap": 0.4
  },
  "recommendations": [
    {
      "category": "Academic Performance",
      "recommendation": "Focus on improving GPA by 0.4 points",
      "explanation": "Similar Visual learners average 3.6 GPA"
    }
  ],
  "ai_insight": "Consider using more visual study materials...",
  "success": true
}
```

#### GET /api/students
Returns list of available students for analysis.

#### POST /api/analyze
Analyzes a specific student by ID.

**Request:**
```json
{
  "student_id": "STU001"
}
```

#### GET /api/learning-styles
Returns available learning style categories.

## Database Schema

### Node Types
- **Student**: Individual learner with learning style, pace preferences
- **Course**: Academic courses with difficulty ratings
- **Faculty**: Instructors teaching courses
- **Degree**: Academic programs (BS/BA in CS, Biology)
- **Term**: Academic time periods
- **RequirementGroup**: Degree requirements

### Relationship Types
- **SIMILAR_LEARNING_STYLE**: Connects students with matching learning preferences
- **SIMILAR_PERFORMANCE**: Links students with comparable academic outcomes
- **COMPLETED**: Student-course completion with grades
- **PREREQUISITE_FOR**: Course dependency relationships
- **TEACHES**: Faculty-course assignments

### Key Queries
```cypher
// Find similar students who performed better
MATCH (target:Student)-[sim:SIMILAR_LEARNING_STYLE]->(peer:Student)
WHERE sim.similarity > 0.7
MATCH (peer)-[pc:COMPLETED]->(course:Course)
WITH peer, AVG(CASE pc.grade WHEN 'A' THEN 4.0 ... END) AS avgGPA
WHERE avgGPA >= $minGPA
RETURN peer, avgGPA
ORDER BY avgGPA DESC
```

## AI Model Integration

### Model Selection
- **Primary**: Ollama with TinyLlama
- **Rationale**: Local AI server providing better contextual understanding than traditional models
- **Local Processing**: No external API dependencies, ensuring privacy and flexibility

### Recommendation Generation Process
1. **Data Collection**: Query Neo4j for similar student patterns
2. **Analysis**: Calculate performance gaps and behavioral differences  
3. **Prompt Engineering**: Create contextual prompts for AI model
4. **Response Generation**: Use local AI to generate personalized advice
5. **Structured Output**: Format recommendations with categories and priorities

### Fallback Strategy
If AI model fails, system provides rule-based recommendations using predefined templates based on learning styles and performance patterns.

## Future Enhancements

### Technical Improvements
- **Model Upgrades**: Upgrade to larger Ollama models (Llama2, Mistral) as system resources allow
- **Advanced Analytics**: Implement graph algorithms for deeper pattern analysis
- **Real-time Updates**: WebSocket connections for live recommendation updates
- **Model Fine-tuning**: Train custom models on educational data

### Feature Additions
- **Study Group Matching**: Connect students with complementary skills
- **Progress Tracking**: Monitor student improvement over time
- **Integration APIs**: Connect with Canvas, Blackboard, or other LMS platforms
- **Mobile Application**: Native iOS/Android apps

### Data Enhancements
- **Temporal Analysis**: Track changes in student performance over time
- **External Factors**: Incorporate work hours, financial aid status
- **Textbook Analytics**: Detailed reading pattern analysis
- **Collaborative Filtering**: Advanced recommendation algorithms

## Contributing

### Development Setup
1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Follow existing code style and patterns
4. Add tests for new functionality
5. Submit pull request with detailed description

### Code Standards
- **Python**: Follow PEP 8 style guidelines
- **JavaScript**: Use ES6+ features, consistent naming
- **Documentation**: Update README for new features
- **Testing**: Include unit tests for core functionality

---

**Built for HackUMBC 2025**  
*Demonstrating the power of graph databases, local AI, and modern web technologies for educational applications.*
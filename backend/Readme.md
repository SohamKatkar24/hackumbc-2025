# AI Study Coach - Backend API

Flask-based REST API that serves AI-generated study recommendations by analyzing Neo4j graph database relationships.

## Overview

The backend processes student similarity data from Neo4j, uses local AI models to generate personalized recommendations, and serves results through RESTful endpoints.

## Architecture

```
Flask API Server (Port 5000)
├── Neo4j Database Connection (Port 7687)
├── AI Model Integration (DialoGPT)
└── CORS-enabled REST Endpoints
```

## API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/` | API status and documentation |
| GET    | `/api/recommendations` | Random student recommendations |
| GET    | `/api/students` | List available students |
| GET    | `/api/learning-styles` | Available learning styles |
| GET    | `/api/student/<id>` | Specific student info |
| POST   | `/api/analyze` | Analyze specific student |
| POST   | `/api/compare` | Compare learning styles |
| GET    | `/api/demo` | Demo data samples |

### Example Response

```json
{
  "student": {
    "name": "John Doe",
    "learningStyle": "Visual",
    "preferredPace": "Standard",
    "grades": ["A", "B+", "A-"]
  },
  "analysis": {
    "target_gpa": 3.18,
    "similar_avg_gpa": 3.25,
    "gpa_gap": 0.07,
    "better_performers_count": 4,
    "total_similar_count": 10
  },
  "recommendations": [
    {
      "category": "Academic Performance",
      "priority": "medium",
      "recommendation": "Focus on improving GPA by 0.1 points",
      "explanation": "Similar Visual learners average 3.25 GPA"
    }
  ],
  "ai_insight": "Consider using more visual study materials...",
  "success": true
}
```

## Dependencies

### Core Libraries
- **Flask 2.3.3**: Web framework
- **Flask-CORS 4.0.0**: Cross-origin resource sharing
- **neo4j 5.12.0**: Database driver
- **requests 2.31.0**: HTTP client for Ollama API communication

### Data Processing
- **numpy 1.24.3**: Numerical computations
- **pandas 2.0.3**: Data manipulation
- **scikit-learn 1.3.0**: Machine learning utilities

## Installation

### Prerequisites
- Python 3.8+
- Neo4j database running on localhost:7687
- Virtual environment (recommended)

### Setup
```bash
# Navigate to backend directory
cd backend

# Install dependencies (from project root)
pip install -r ../requirements.txt

# Start the API server
python app.py
```

### Environment Variables
The API uses these default configurations:
- **Neo4j URI**: `bolt://localhost:7687`
- **Neo4j Auth**: `neo4j/yourpassword`
- **Flask Port**: `5000`
- **Debug Mode**: `True` (development)

## Usage

### Start the Server
```bash
python app.py
```

Server will start at `http://localhost:5000`

### Test Endpoints
```bash
# Check API status
curl http://localhost:5000

# Get random recommendations
curl http://localhost:5000/api/recommendations

# Get student list
curl http://localhost:5000/api/students

# Analyze specific student
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"student_id": "STU001"}'
```

## AI Model Integration

### Model Configuration
- **Model**: Ollama with TinyLlama
- **Purpose**: Generate contextual study advice
- **Processing**: Local inference via Ollama API (port 11434)
- **Fallback**: Rule-based recommendations if Ollama unavailable

### Recommendation Process
1. Query Neo4j for similar students
2. Calculate performance gaps and patterns
3. Generate AI prompt with student context
4. Process through local language model
5. Structure response with categories and priorities

## Database Integration

### Neo4j Connection
The API connects to Neo4j using the official Python driver:

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687", 
    auth=("neo4j", "yourpassword")
)
```

### Key Queries
- Find similar students by learning style
- Calculate GPA and performance metrics
- Analyze course completion patterns
- Generate comparative statistics

## Error Handling

### Common Error Responses
```json
{
  "error": "Student not found"
}
```

### Status Codes
- **200**: Success
- **404**: Resource not found
- **500**: Internal server error

## Development

### Code Structure
```
backend/
├── app.py              # Main Flask application
└── README.md          # This documentation
```

### Adding New Endpoints
1. Define route in `app.py`
2. Implement database query logic
3. Add error handling
4. Update this documentation

### Testing
```bash
# Install development dependencies
pip install pytest flask-testing

# Run tests (if implemented)
pytest tests/
```

## Configuration

### Production Settings
For production deployment:
```python
app.run(debug=False, host='0.0.0.0', port=5000)
```

### Database Connection Pooling
The Neo4j driver automatically manages connection pooling for optimal performance.

## Troubleshooting

### Common Issues

**Neo4j Connection Failed**
```
Solution: Verify Neo4j is running and credentials are correct
Check: docker ps | grep neo4j
```

**Ollama Connection Error**
```
Solution: Ensure Ollama is running (ollama serve)
Check: curl http://localhost:11434/api/tags
Alternative: Restart Ollama service
```

**CORS Issues**
```
Solution: Flask-CORS is configured for all origins in development
Production: Configure specific allowed origins
```

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance

### Optimization Tips
- Connection pooling enabled by default
- AI model cached after first load
- Database queries optimized for graph traversal
- Async processing for multiple requests

### Monitoring
- Monitor response times for Neo4j queries
- Track AI model inference latency
- Log error rates and patterns

## Security

### Development
- CORS enabled for all origins
- No authentication required
- Debug mode enabled

### Production Considerations
- Implement authentication middleware
- Configure specific CORS origins
- Use environment variables for secrets
- Enable HTTPS
- Add rate limiting

## Contributing

### Code Style
- Follow PEP 8 guidelines
- Use descriptive variable names
- Add docstrings for functions
- Handle exceptions appropriately

### Testing
- Add unit tests for new endpoints
- Test database connection scenarios
- Validate AI model responses
- Check error handling paths
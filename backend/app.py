from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add parent directory to path to import our AI coach
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ollama_ai_coach import OllamaAIStudyCoach

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Initialize AI Study Coach (this takes a moment to load the model)
print("Initializing AI Study Coach...")
coach = OllamaAIStudyCoach()
print("AI Study Coach ready!")

@app.route('/')
def home():
    return jsonify({
        "message": "AI Study Coach API",
        "status": "running",
        "endpoints": {
            "/api/recommendations": "GET - Get AI study recommendations for random student",
            "/api/students": "GET - Get list of available students",
            "/api/learning-styles": "GET - Get all learning styles",
            "/api/student/<student_id>": "GET - Get specific student info",
            "/api/analyze": "POST - Analyze specific student"
        }
    })

@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    """Get AI study recommendations for a random student"""
    try:
        result = coach.get_recommendations()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/students', methods=['GET'])
def get_students():
    """Get list of available students"""
    try:
        with coach.driver.session() as session:
            query = """
            MATCH (s:Student)-[c:COMPLETED]->(course:Course)
            WITH s, count(c) as courseCount
            WHERE courseCount >= 3
            RETURN s.id as id, s.name as name, s.learningStyle as learningStyle, 
                   s.preferredPace as preferredPace, courseCount
            ORDER BY s.name
            LIMIT 50
            """
            result = session.run(query)
            students = [dict(record) for record in result]
            return jsonify(students)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/learning-styles', methods=['GET'])
def get_learning_styles():
    """Get all available learning styles"""
    try:
        with coach.driver.session() as session:
            query = """
            MATCH (s:Student)
            RETURN DISTINCT s.learningStyle as style
            ORDER BY s.learningStyle
            """
            result = session.run(query)
            styles = [record['style'] for record in result]
            return jsonify(styles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/student/<student_id>', methods=['GET'])
def get_student_info(student_id):
    """Get specific student information"""
    try:
        with coach.driver.session() as session:
            query = """
            MATCH (s:Student {id: $student_id})-[c:COMPLETED]->(course:Course)
            RETURN s.id as id, s.name as name, s.learningStyle as learningStyle, 
                   s.preferredPace as preferredPace,
                   collect(c.grade) as grades,
                   collect(course.name) as courseNames,
                   count(c) as courseCount
            """
            result = session.run(query, student_id=student_id)
            record = result.single()
            
            if record:
                student_data = dict(record)
                # Calculate GPA
                student_data['gpa'] = coach.calculate_gpa(student_data['grades'])
                return jsonify(student_data)
            else:
                return jsonify({"error": "Student not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_student():
    """Analyze a specific student and get recommendations"""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        
        if not student_id:
            return jsonify({"error": "student_id is required"}), 400
        
        # Get student info
        with coach.driver.session() as session:
            query = """
            MATCH (s:Student {id: $student_id})-[c:COMPLETED]->(course:Course)
            RETURN s.id as id, s.name as name, s.learningStyle as learningStyle, 
                   s.preferredPace as preferredPace,
                   collect(c.grade) as grades,
                   collect(course.name) as courseNames
            """
            result = session.run(query, student_id=student_id)
            record = result.single()
            
            if not record:
                return jsonify({"error": "Student not found"}), 404
            
            student = dict(record)
        
        # Find similar students
        similar_students = coach.find_similar_students(student['learningStyle'])
        
        if not similar_students:
            return jsonify({"error": "No similar students found"}), 404
        
        # Analyze performance
        analysis = coach.analyze_performance(student, similar_students)
        
        # Generate AI insights
        ai_insight = coach.generate_ai_insights(analysis)
        
        # Create recommendations
        recommendations = coach.create_recommendations(analysis, ai_insight)
        
        return jsonify({
            'student': student,
            'analysis': analysis,
            'recommendations': recommendations,
            'ai_insight': ai_insight,
            'success': True
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/compare', methods=['POST'])
def compare_learning_styles():
    """Compare performance across different learning styles"""
    try:
        with coach.driver.session() as session:
            query = """
            MATCH (s:Student)-[c:COMPLETED]->(course:Course)
            WITH s.learningStyle as style, collect(c.grade) as allGrades
            WHERE size(allGrades) >= 3
            RETURN style, 
                   size(allGrades) as totalGrades,
                   allGrades
            ORDER BY style
            """
            result = session.run(query)
            
            style_stats = []
            for record in result:
                grades = record['allGrades']
                avg_gpa = coach.calculate_gpa(grades)
                
                style_stats.append({
                    'learning_style': record['style'],
                    'average_gpa': round(avg_gpa, 2),
                    'total_completions': record['totalGrades']
                })
            
            return jsonify(style_stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/demo', methods=['GET'])
def demo_data():
    """Get demo data for frontend testing"""
    try:
        # Get a few sample recommendations
        samples = []
        for _ in range(3):
            result = coach.get_recommendations()
            if result.get('success'):
                samples.append(result)
        
        return jsonify({
            'sample_recommendations': samples,
            'total_samples': len(samples)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    try:
        print("Starting AI Study Coach API...")
        print("Neo4j connection: bolt://localhost:7687")
        print("AI model: loaded")
        print("API will be available at: http://localhost:5000")
        print("\nAvailable endpoints:")
        print("  GET  / - API home")
        print("  GET  /api/recommendations - Random student recommendations")
        print("  GET  /api/students - List all students")
        print("  GET  /api/learning-styles - List learning styles")
        print("  GET  /api/student/<id> - Get specific student")
        print("  POST /api/analyze - Analyze specific student")
        print("  POST /api/compare - Compare learning styles")
        print("  GET  /api/demo - Demo data")
        print("\nReady for requests!")
        
        app.run(debug=True, port=5000, host='0.0.0.0')
    except KeyboardInterrupt:
        print("\nShutting down AI Study Coach API...")
        coach.close()
        print("Goodbye!")
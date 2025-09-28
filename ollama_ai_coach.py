from neo4j import GraphDatabase
import requests
import json
import numpy as np

class OllamaAIStudyCoach:
    def __init__(self, model_name="llama2"):
        # Neo4j connection
        self.driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "yourpassword"))
        
        # Ollama configuration
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = model_name
        
        print(f"Initializing AI Study Coach with Ollama model: {model_name}")
        
        # Test Ollama connection
        try:
            self.test_ollama_connection()
            print("Ollama connection successful!")
        except Exception as e:
            print(f"Warning: Ollama connection failed: {e}")
            print("Make sure Ollama is running and the model is pulled")

    def test_ollama_connection(self):
        """Test if Ollama is running and model is available"""
        test_prompt = "Hello"
        response = requests.post(self.ollama_url, json={
            "model": self.model_name,
            "prompt": test_prompt,
            "stream": False
        }, timeout=10)
        
        if response.status_code != 200:
            raise Exception(f"Ollama returned status {response.status_code}")
        
        return True

    def get_random_student(self):
        """Get a random student with course data"""
        with self.driver.session() as session:
            query = """
            MATCH (s:Student)-[c:COMPLETED]->(course:Course)
            WITH s, count(c) as courseCount
            WHERE courseCount >= 3
            WITH s ORDER BY rand() LIMIT 1
            MATCH (s)-[c:COMPLETED]->(course:Course)
            RETURN s.id as id, s.name as name, s.learningStyle as learningStyle, 
                   s.preferredPace as preferredPace,
                   collect(c.grade) as grades,
                   collect(course.name) as courseNames
            """
            result = session.run(query)
            record = result.single()
            return dict(record) if record else None

    def find_similar_students(self, target_learning_style):
        """Find students with similar learning style and their performance"""
        with self.driver.session() as session:
            query = """
            MATCH (s:Student)-[c:COMPLETED]->(course:Course)
            WHERE s.learningStyle = $learningStyle
            WITH s, collect(c.grade) as grades, count(c) as courseCount
            WHERE courseCount >= 3
            RETURN s.name as name, s.learningStyle as learningStyle,
                   s.preferredPace as preferredPace, grades, courseCount
            LIMIT 10
            """
            result = session.run(query, learningStyle=target_learning_style)
            return [dict(record) for record in result]

    def calculate_gpa(self, grades):
        """Calculate GPA from grades"""
        grade_points = {
            'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7,
            'C+': 2.3, 'C': 2.0, 'C-': 1.7, 'D+': 1.3, 'D': 1.0, 'F': 0.0
        }
        if not grades:
            return 0.0
        points = [grade_points.get(grade, 0.0) for grade in grades]
        return sum(points) / len(points)

    def analyze_performance(self, target_student, similar_students):
        """Analyze performance compared to similar students"""
        target_gpa = self.calculate_gpa(target_student['grades'])
        target_courses = len(target_student['grades'])
        
        # Calculate stats for similar students
        similar_gpas = [self.calculate_gpa(s['grades']) for s in similar_students]
        similar_courses = [s['courseCount'] for s in similar_students]
        
        # Find better performers
        better_performers = [gpa for gpa in similar_gpas if gpa > target_gpa]
        
        analysis = {
            'target_gpa': target_gpa,
            'target_courses': target_courses,
            'similar_avg_gpa': np.mean(similar_gpas) if similar_gpas else 0.0,
            'similar_avg_courses': np.mean(similar_courses) if similar_courses else 0,
            'better_performers_count': len(better_performers),
            'total_similar_count': len(similar_students),
            'learning_style': target_student['learningStyle'],
            'preferred_pace': target_student['preferredPace']
        }
        
        return analysis

    def generate_ollama_insights(self, analysis):
        """Generate AI insights using Ollama"""
        try:
            learning_style = analysis['learning_style']
            gpa_diff = analysis['similar_avg_gpa'] - analysis['target_gpa']
            course_diff = analysis['similar_avg_courses'] - analysis['target_courses']
            
            # Create a detailed prompt for Ollama
            prompt = f"""You are an academic advisor AI. A {learning_style} learning style student needs study advice.

Student Profile:
- Learning Style: {learning_style}
- Current GPA: {analysis['target_gpa']:.2f}
- Courses Completed: {analysis['target_courses']}
- Preferred Pace: {analysis['preferred_pace']}

Comparison with Similar Students:
- Similar students average GPA: {analysis['similar_avg_gpa']:.2f}
- GPA gap: {gpa_diff:.2f} points
- Similar students average courses: {analysis['similar_avg_courses']:.1f}
- Course gap: {course_diff:.1f} courses
- Better performers: {analysis['better_performers_count']}/{analysis['total_similar_count']}

Provide 2-3 specific, actionable study recommendations for this {learning_style} learner. Focus on practical advice that addresses their performance gaps. Keep response under 100 words."""

            # Call Ollama API
            response = requests.post(self.ollama_url, json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 150
                }
            }, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                print(f"Ollama API error: {response.status_code}")
                return self.get_fallback_advice(learning_style)
                
        except Exception as e:
            print(f"Ollama generation error: {e}")
            return self.get_fallback_advice(analysis['learning_style'])

    def get_fallback_advice(self, learning_style):
        """Fallback advice if Ollama fails"""
        fallback_advice = {
            'Visual': 'Create visual study aids like diagrams, charts, and mind maps. Use color coding and visual organization for notes.',
            'Auditory': 'Form study groups, record lectures, and explain concepts aloud. Use verbal mnemonics and discussion-based learning.',
            'Kinesthetic': 'Use hands-on practice, labs, and physical activities. Take breaks to move around and use manipulatives when possible.',
            'Reading-Writing': 'Focus on detailed note-taking, written summaries, and practice problems. Create lists and written study guides.'
        }
        return fallback_advice.get(learning_style, 'Focus on consistent study habits and seek help when needed.')

    def create_recommendations(self, analysis, ai_insight):
        """Create structured recommendations"""
        recommendations = []
        
        # GPA recommendation
        gpa_gap = analysis['similar_avg_gpa'] - analysis['target_gpa']
        if gpa_gap > 0.1:
            recommendations.append({
                'category': 'Academic Performance',
                'priority': 'high' if gpa_gap > 0.3 else 'medium',
                'recommendation': f"Work to improve GPA by {gpa_gap:.1f} points",
                'explanation': f"Similar {analysis['learning_style']} learners average {analysis['similar_avg_gpa']:.2f} GPA",
                'ai_insight': ai_insight
            })
        
        # Course load recommendation
        course_gap = analysis['similar_avg_courses'] - analysis['target_courses']
        if course_gap > 1:
            recommendations.append({
                'category': 'Course Planning',
                'priority': 'medium',
                'recommendation': f"Consider taking {course_gap:.0f} more courses",
                'explanation': f"Similar students complete {course_gap:.0f} more courses on average"
            })
        
        # Learning style advice
        style_advice = {
            'Visual': 'Use diagrams, charts, and visual study materials',
            'Auditory': 'Try study groups and explaining concepts aloud',
            'Kinesthetic': 'Use hands-on practice and real-world applications',
            'Reading-Writing': 'Focus on note-taking and written practice'
        }
        
        if analysis['learning_style'] in style_advice:
            recommendations.append({
                'category': 'Learning Style Optimization',
                'priority': 'medium',
                'recommendation': style_advice[analysis['learning_style']],
                'explanation': f"Optimized advice for {analysis['learning_style']} learners",
                'ai_insight': 'Leveraging your natural learning preferences improves retention and performance'
            })
        
        return recommendations

    def get_recommendations(self):
        """Main method to get AI-powered study recommendations"""
        try:
            # Get a random student
            student = self.get_random_student()
            if not student:
                return {"error": "No student data found"}
            
            # Find similar students
            similar_students = self.find_similar_students(student['learningStyle'])
            if not similar_students:
                return {"error": "No similar students found"}
            
            # Analyze performance
            analysis = self.analyze_performance(student, similar_students)
            
            # Generate AI insights using Ollama
            ai_insight = self.generate_ollama_insights(analysis)
            
            # Create recommendations
            recommendations = self.create_recommendations(analysis, ai_insight)
            
            return {
                'student': student,
                'analysis': analysis,
                'recommendations': recommendations,
                'ai_insight': ai_insight,
                'success': True
            }
            
        except Exception as e:
            import traceback
            print(f"Error: {e}")
            traceback.print_exc()
            return {"error": str(e)}

    def close(self):
        self.driver.close()

# Test the Ollama AI coach
if __name__ == "__main__":
    # You can specify different models: llama2, mistral, codellama, etc.
    coach = OllamaAIStudyCoach(model_name="llama2")
    
    print("\n🤖 Ollama AI Study Coach Test")
    print("=" * 50)
    
    result = coach.get_recommendations()
    
    if result.get('success'):
        student = result['student']
        analysis = result['analysis']
        recommendations = result['recommendations']
        
        print(f"\n📊 Student: {student['name']}")
        print(f"Learning Style: {student['learningStyle']}")
        print(f"Preferred Pace: {student['preferredPace']}")
        print(f"Completed Courses: {len(student['grades'])}")
        
        print(f"\n📈 Performance Analysis:")
        print(f"Your GPA: {analysis['target_gpa']:.2f}")
        print(f"Similar Students' Average GPA: {analysis['similar_avg_gpa']:.2f}")
        print(f"Better Performers: {analysis['better_performers_count']}/{analysis['total_similar_count']}")
        
        print(f"\n🎯 AI-Generated Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec['category']} ({rec.get('priority', 'medium').upper()} priority)")
            print(f"   💡 {rec['recommendation']}")
            print(f"   📝 {rec['explanation']}")
            if 'ai_insight' in rec:
                print(f"   🤖 AI: {rec['ai_insight']}")
                
        print(f"\n🤖 Ollama AI Insight:")
        print(f"{result['ai_insight']}")
        
    else:
        print(f"❌ Error: {result['error']}")
    
    coach.close()
    print("\n✅ Test complete!")
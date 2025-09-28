from neo4j import GraphDatabase
from transformers import pipeline, GPT2LMHeadModel, GPT2Tokenizer
import numpy as np

class SimpleAIStudyCoach:
    def __init__(self):
        # Neo4j connection
        self.driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "yourpassword"))
        
        # Initialize local AI model
        print("Loading AI model...")
        self.tokenizer = GPT2Tokenizer.from_pretrained("microsoft/DialoGPT-small")
        self.model = GPT2LMHeadModel.from_pretrained("microsoft/DialoGPT-small")
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.text_generator = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_length=120,
            num_return_sequences=1,
            temperature=0.7,
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id
        )
        
        print("AI model loaded successfully!")

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

    def generate_ai_insights(self, analysis):
        """Generate AI insights based on analysis"""
        try:
            learning_style = analysis['learning_style']
            gpa_diff = analysis['similar_avg_gpa'] - analysis['target_gpa']
            
            if gpa_diff > 0.2:
                context = f"{learning_style} learner needs to improve {gpa_diff:.1f} GPA points"
            else:
                context = f"{learning_style} learner performing well"
            
            prompt = f"Study advice for {context}:"
            
            generated = self.text_generator(prompt, max_length=len(prompt.split()) + 30)
            ai_text = generated[0]['generated_text'].replace(prompt, '').strip()
            
            return ai_text
        except Exception as e:
            print(f"AI generation error: {e}")
            return "Focus on consistent study habits and seek help when needed."

    def create_recommendations(self, analysis, ai_insight):
        """Create structured recommendations"""
        recommendations = []
        
        # GPA recommendation
        gpa_gap = analysis['similar_avg_gpa'] - analysis['target_gpa']
        if gpa_gap > 0.1:
            recommendations.append({
                'category': 'Academic Performance',
                'recommendation': f"Work to improve GPA by {gpa_gap:.1f} points",
                'explanation': f"Similar {analysis['learning_style']} learners average {analysis['similar_avg_gpa']:.2f} GPA",
                'ai_insight': ai_insight
            })
        
        # Course load recommendation
        course_gap = analysis['similar_avg_courses'] - analysis['target_courses']
        if course_gap > 1:
            recommendations.append({
                'category': 'Course Planning',
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
                'category': 'Learning Style',
                'recommendation': style_advice[analysis['learning_style']],
                'explanation': f"Optimized advice for {analysis['learning_style']} learners"
            })
        
        return recommendations

    def get_recommendations(self):
        """Main method to get study recommendations"""
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
            
            # Generate AI insights
            ai_insight = self.generate_ai_insights(analysis)
            
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

# Test the simple AI coach
if __name__ == "__main__":
    coach = SimpleAIStudyCoach()
    
    print("\n🤖 Simple AI Study Coach Test")
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
            print(f"\n{i}. {rec['category']}")
            print(f"   💡 {rec['recommendation']}")
            print(f"   📝 {rec['explanation']}")
            if 'ai_insight' in rec:
                print(f"   🤖 AI: {rec['ai_insight']}")
                
        print(f"\n🤖 AI Insight: {result['ai_insight']}")
        
    else:
        print(f"❌ Error: {result['error']}")
    
    coach.close()
    print("\n✅ Test complete!")
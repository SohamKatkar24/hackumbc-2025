import os
from neo4j import GraphDatabase
from transformers import pipeline, GPT2LMHeadModel, GPT2Tokenizer
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import json

class AIStudyCoach:
    def __init__(self):
        # Neo4j connection
        self.driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "yourpassword"))
        
        # Initialize local AI model for text generation
        print("Loading AI model... (this may take a moment)")
        self.tokenizer = GPT2Tokenizer.from_pretrained("microsoft/DialoGPT-small")
        self.model = GPT2LMHeadModel.from_pretrained("microsoft/DialoGPT-small")
        
        # Add padding token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Initialize text generation pipeline
        self.text_generator = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_length=150,
            num_return_sequences=1,
            temperature=0.7,
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id
        )
        
        print("AI model loaded successfully!")

    def get_student_profile(self, student_id=None):
        """Get a student's profile and performance data"""
        with self.driver.session() as session:
            if student_id:
                query = """
                MATCH (s:Student {id: $student_id})-[c:COMPLETED]->(course:Course)
                RETURN s.name as name, s.learningStyle as learningStyle, 
                       s.preferredPace as preferredPace, s.preferredCourseLoad as preferredCourseLoad,
                       collect({course: course.name, grade: c.grade, 
                               difficulty: toFloat(c.difficulty), timeSpent: toFloat(c.timeSpent), 
                               enjoyment: toFloat(c.enjoyment)}) as courses
                """
                result = session.run(query, student_id=student_id)
            else:
                # Get a random student for demo
                query = """
                MATCH (s:Student)-[c:COMPLETED]->(course:Course)
                WITH s, count(c) as courseCount
                WHERE courseCount >= 3
                WITH s ORDER BY rand() LIMIT 1
                MATCH (s)-[c:COMPLETED]->(course:Course)
                RETURN s.id as id, s.name as name, s.learningStyle as learningStyle, 
                       s.preferredPace as preferredPace, s.preferredCourseLoad as preferredCourseLoad,
                       collect({course: course.name, grade: c.grade, 
                               difficulty: toFloat(c.difficulty), timeSpent: toFloat(c.timeSpent),
                               enjoyment: toFloat(c.enjoyment)}) as courses
                """
                result = session.run(query)
                
            record = result.single()
            if record:
                return dict(record)
            return None

    def find_similar_successful_students(self, target_student):
        """Find students similar to target who performed better"""
        with self.driver.session() as session:
            query = """
            // Find similar students with better performance
            MATCH (target:Student)-[sim:SIMILAR_LEARNING_STYLE]->(peer:Student)
            WHERE target.learningStyle = $learningStyle
            AND sim.similarity > 0.7
            
            // Get their course performance
            MATCH (peer)-[pc:COMPLETED]->(course:Course)
            WITH peer, 
                 AVG(CASE pc.grade
                     WHEN 'A' THEN 4.0 WHEN 'A-' THEN 3.7
                     WHEN 'B+' THEN 3.3 WHEN 'B' THEN 3.0 WHEN 'B-' THEN 2.7
                     WHEN 'C+' THEN 2.3 WHEN 'C' THEN 2.0 WHEN 'C-' THEN 1.7
                     WHEN 'D+' THEN 1.3 WHEN 'D' THEN 1.0
                     ELSE 0 END) AS avgGPA,
                 AVG(toFloat(pc.difficulty)) AS avgPerceivedDifficulty,
                 AVG(toFloat(pc.timeSpent)) AS avgTimeSpent,
                 AVG(toFloat(pc.enjoyment)) AS avgEnjoyment,
                 COUNT(pc) as totalCourses,
                 collect({course: course.name, grade: pc.grade, 
                         difficulty: toFloat(pc.difficulty), timeSpent: toFloat(pc.timeSpent),
                         enjoyment: toFloat(pc.enjoyment)}) as courses
                 
            // Filter for better performers
            WHERE avgGPA >= $minGPA
            
            RETURN peer.id as id, peer.name as name, peer.learningStyle as learningStyle,
                   peer.preferredPace as preferredPace,
                   avgGPA, avgPerceivedDifficulty, avgTimeSpent, avgEnjoyment, totalCourses,
                   courses
            ORDER BY avgGPA DESC
            LIMIT 5
            """
            
            # Calculate target student's GPA for comparison
            target_gpa = self.calculate_gpa(target_student.get('courses', []))
            
            result = session.run(query, 
                                learningStyle=target_student['learningStyle'],
                                minGPA=target_gpa + 0.2)  # Find students with at least 0.2 GPA higher
            
            return [dict(record) for record in result]

    def calculate_gpa(self, courses):
        """Calculate GPA from course list"""
        if not courses:
            return 0.0
            
        grade_points = {
            'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7,
            'C+': 2.3, 'C': 2.0, 'C-': 1.7, 'D+': 1.3, 'D': 1.0, 'F': 0.0
        }
        
        total_points = sum(grade_points.get(course['grade'], 0.0) for course in courses)
        return total_points / len(courses) if courses else 0.0

    def analyze_behavioral_patterns(self, target_student, similar_students):
        """Analyze differences between target and successful similar students"""
        if not similar_students:
            return {}
            
        target_gpa = self.calculate_gpa(target_student.get('courses', []))
        target_courses = len(target_student.get('courses', []))
        target_difficulty = np.mean([c.get('difficulty', 3.0) for c in target_student.get('courses', [])]) if target_student.get('courses') else 3.0
        target_time_spent = np.mean([c.get('timeSpent', 0.0) for c in target_student.get('courses', [])]) if target_student.get('courses') else 0.0
        target_enjoyment = np.mean([c.get('enjoyment', 3.0) for c in target_student.get('courses', [])]) if target_student.get('courses') else 3.0
        
        # Aggregate successful students' data
        successful_gpa = np.mean([s['avgGPA'] for s in similar_students])
        successful_courses = np.mean([s['totalCourses'] for s in similar_students])
        successful_difficulty = np.mean([s['avgPerceivedDifficulty'] for s in similar_students])
        successful_time_spent = np.mean([s['avgTimeSpent'] for s in similar_students])
        successful_enjoyment = np.mean([s['avgEnjoyment'] for s in similar_students])
        
        analysis = {
            'gpa_gap': successful_gpa - target_gpa,
            'course_load_gap': successful_courses - target_courses,
            'difficulty_perception_gap': target_difficulty - successful_difficulty,
            'time_spent_gap': successful_time_spent - target_time_spent,
            'enjoyment_gap': successful_enjoyment - target_enjoyment,
            'successful_students_count': len(similar_students),
            'target_learning_style': target_student['learningStyle'],
            'target_pace': target_student['preferredPace'],
            'successful_pace_distribution': [s['preferredPace'] for s in similar_students],
            'target_gpa': target_gpa,
            'successful_gpa': successful_gpa,
            'target_time_spent': target_time_spent,
            'successful_time_spent': successful_time_spent
        }
        
        return analysis

    def generate_ai_recommendations(self, target_student, analysis):
        """Use local AI to generate personalized study recommendations"""
        
        # Create a structured prompt based on analysis
        context = self.create_recommendation_context(target_student, analysis)
        
        # Generate recommendations using local AI
        try:
            prompt = f"Study advice for {target_student['learningStyle']} learner: {context}"
            
            # Use the text generation pipeline
            generated = self.text_generator(
                prompt,
                max_length=min(len(prompt.split()) + 50, 150),
                num_return_sequences=1,
                temperature=0.7
            )
            
            ai_text = generated[0]['generated_text'].replace(prompt, '').strip()
            
            # Combine AI output with data-driven insights
            recommendations = self.create_structured_recommendations(analysis, ai_text)
            
            return recommendations
            
        except Exception as e:
            print(f"AI generation error: {e}")
            # Fallback to rule-based recommendations
            return self.create_rule_based_recommendations(analysis)

    def create_recommendation_context(self, target_student, analysis):
        """Create context for AI prompt"""
        context_parts = []
        
        if analysis['gpa_gap'] > 0.3:
            context_parts.append(f"has {analysis['gpa_gap']:.1f} GPA gap to close")
            
        if analysis['course_load_gap'] > 2:
            context_parts.append(f"should take {analysis['course_load_gap']:.1f} more courses")
            
        if analysis['difficulty_perception_gap'] > 0.5:
            context_parts.append("finds courses harder than successful peers")
            
        context_parts.append(f"prefers {target_student['preferredPace']} learning pace")
        
        return ", ".join(context_parts)

    def create_structured_recommendations(self, analysis, ai_text):
        """Create structured recommendations combining AI and data"""
        recommendations = []
        
        # GPA Improvement Recommendation
        if analysis['gpa_gap'] > 0.2:
            recommendations.append({
                'category': 'Academic Performance',
                'priority': 'high',
                'recommendation': f"Focus on improving grades - there's a {analysis['gpa_gap']:.1f} GPA gap to close",
                'explanation': f"Similar successful students have an average GPA of {analysis['successful_gpa']:.2f} compared to your {analysis['target_gpa']:.2f}",
                'ai_insight': ai_text[:100] + "..." if ai_text else "Consider study groups and office hours"
            })
        
        # Time Spent Recommendation
        if analysis['time_spent_gap'] > 5:
            recommendations.append({
                'category': 'Study Time',
                'priority': 'high',
                'recommendation': f"Increase study time by {analysis['time_spent_gap']:.1f} hours per week",
                'explanation': f"Successful similar students spend {analysis['time_spent_gap']:.1f} more hours per week on courses",
                'ai_insight': "Consistent, dedicated study sessions lead to better outcomes"
            })
        
        # Course Load Recommendation
        if analysis['course_load_gap'] > 1:
            recommendations.append({
                'category': 'Course Planning',
                'priority': 'medium',
                'recommendation': f"Consider taking {analysis['course_load_gap']:.0f} more courses to match successful peers",
                'explanation': f"Successful similar students have completed {analysis['course_load_gap']:.0f} more courses on average",
                'ai_insight': "Gradual increase in course load can improve academic momentum"
            })
        
        # Difficulty Perception
        if analysis['difficulty_perception_gap'] > 0.3:
            recommendations.append({
                'category': 'Study Strategy',
                'priority': 'medium',
                'recommendation': "Seek additional support - you perceive courses as more difficult than successful peers",
                'explanation': f"You rate course difficulty {analysis['difficulty_perception_gap']:.1f} points higher than successful peers",
                'ai_insight': "Breaking down complex topics into smaller parts can help"
            })
        
        # Enjoyment Gap
        if analysis['enjoyment_gap'] < -0.5:
            recommendations.append({
                'category': 'Course Satisfaction',
                'priority': 'medium',
                'recommendation': "Find ways to increase course enjoyment and engagement",
                'explanation': f"Successful peers enjoy their courses {abs(analysis['enjoyment_gap']):.1f} points more than you do",
                'ai_insight': "Higher enjoyment often correlates with better academic performance"
            })
        
        # Learning Style Optimization
        learning_style = analysis['target_learning_style']
        if learning_style:
            style_advice = {
                'Visual': 'Use diagrams, charts, and visual aids in your study materials',
                'Auditory': 'Try study groups, recorded lectures, and explaining concepts aloud',
                'Kinesthetic': 'Use hands-on practice, labs, and real-world applications',
                'Reading-Writing': 'Focus on note-taking, reading, and written practice problems'
            }
            
            recommendations.append({
                'category': 'Learning Style Optimization',
                'priority': 'medium',
                'recommendation': f"Leverage your {learning_style} learning style more effectively",
                'explanation': style_advice.get(learning_style, 'Adapt study methods to your learning preferences'),
                'ai_insight': f"Successful {learning_style} learners often use specialized techniques"
            })
        
        return recommendations

    def create_rule_based_recommendations(self, analysis):
        """Fallback rule-based recommendations if AI fails"""
        recommendations = []
        
        if analysis['gpa_gap'] > 0.2:
            recommendations.append({
                'category': 'Academic Performance',
                'priority': 'high',
                'recommendation': f"Focus on improving grades - there's a {analysis['gpa_gap']:.1f} GPA gap to close",
                'explanation': f"Similar successful students perform {analysis['gpa_gap']:.1f} GPA points better"
            })
            
        if analysis['course_load_gap'] > 1:
            recommendations.append({
                'category': 'Course Planning',
                'priority': 'medium',
                'recommendation': f"Consider taking {analysis['course_load_gap']:.0f} more courses",
                'explanation': f"Successful peers take more courses on average"
            })
            
        return recommendations

    def get_study_recommendations(self, student_id=None):
        """Main method to get AI-powered study recommendations"""
        try:
            # Get student profile
            target_student = self.get_student_profile(student_id)
            if not target_student:
                return {"error": "Student not found or no course data available"}
            
            # Find similar successful students
            similar_students = self.find_similar_successful_students(target_student)
            if not similar_students:
                return {"error": "No similar successful students found for comparison"}
            
            # Analyze behavioral patterns
            analysis = self.analyze_behavioral_patterns(target_student, similar_students)
            
            # Generate AI recommendations
            recommendations = self.generate_ai_recommendations(target_student, analysis)
            
            return {
                'student': target_student,
                'similar_students_count': len(similar_students),
                'analysis': analysis,
                'recommendations': recommendations,
                'success': True
            }
            
        except Exception as e:
            print(f"Debug error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": f"Error generating recommendations: {str(e)}"}

    def close(self):
        """Close Neo4j connection"""
        self.driver.close()

# Test the AI Study Coach
if __name__ == "__main__":
    coach = AIStudyCoach()
    
    print("🤖 AI Study Coach initialized!")
    print("Generating recommendations for a sample student...\n")
    
    # Get recommendations for a random student
    result = coach.get_study_recommendations()
    
    if result.get('success'):
        print(f"📊 Analysis for {result['student']['name']}")
        print(f"Learning Style: {result['student']['learningStyle']}")
        print(f"Preferred Pace: {result['student']['preferredPace']}")
        print(f"Courses Completed: {len(result['student']['courses'])}")
        print(f"Similar Students Found: {result['similar_students_count']}")
        
        print(f"\n🎯 AI-Generated Recommendations:")
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"\n{i}. {rec['category']} ({rec['priority'].upper()} priority)")
            print(f"   💡 {rec['recommendation']}")
            print(f"   📈 {rec['explanation']}")
            if 'ai_insight' in rec:
                print(f"   🤖 AI Insight: {rec['ai_insight']}")
                
        print(f"\n📊 Performance Analysis:")
        analysis = result['analysis']
        print(f"   Current GPA: {analysis['target_gpa']:.2f}")
        print(f"   Successful Peers GPA: {analysis['successful_gpa']:.2f}")
        print(f"   GPA Gap: {analysis['gpa_gap']:.2f}")
        
    else:
        print(f"❌ Error: {result['error']}")
    
    coach.close()
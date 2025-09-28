import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { User, Brain, TrendingUp, BookOpen, Users, Lightbulb, AlertCircle } from 'lucide-react';
import './App.css';

const API_BASE = 'http://localhost:5000/api';

function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [students, setStudents] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState('');
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(false);
  const [learningStyles, setLearningStyles] = useState([]);

  useEffect(() => {
    loadStudents();
    loadLearningStyles();
  }, []);

  const loadStudents = async () => {
    try {
      const response = await axios.get(`${API_BASE}/students`);
      setStudents(response.data);
    } catch (error) {
      console.error('Failed to load students:', error);
    }
  };

  const loadLearningStyles = async () => {
    try {
      const response = await axios.get(`${API_BASE}/learning-styles`);
      setLearningStyles(response.data);
    } catch (error) {
      console.error('Failed to load learning styles:', error);
    }
  };

  const getRandomRecommendations = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/recommendations`);
      setRecommendations(response.data);
    } catch (error) {
      console.error('Failed to get recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  const analyzeStudent = async () => {
    if (!selectedStudent) return;
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/analyze`, {
        student_id: selectedStudent
      });
      setRecommendations(response.data);
    } catch (error) {
      console.error('Failed to analyze student:', error);
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority?.toLowerCase()) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-blue-600 bg-blue-100';
    }
  };

  const getLearningStyleIcon = (style) => {
    switch (style) {
      case 'Visual': return '👁️';
      case 'Auditory': return '👂';
      case 'Kinesthetic': return '🤲';
      case 'Reading-Writing': return '📝';
      default: return '🧠';
    }
  };

  const learningStyleData = learningStyles.map(style => ({
    name: style,
    value: students.filter(s => s.learningStyle === style).length,
    color: style === 'Visual' ? '#8884d8' : style === 'Auditory' ? '#82ca9d' : 
           style === 'Kinesthetic' ? '#ffc658' : '#ff7c7c'
  }));

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Brain className="h-8 w-8 text-blue-600 mr-3" />
              <h1 className="text-2xl font-bold text-gray-900">AI Study Coach</h1>
              <span className="ml-3 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                HackUMBC 2025
              </span>
            </div>
            <nav className="flex space-x-8">
              <button
                onClick={() => setCurrentView('dashboard')}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  currentView === 'dashboard' 
                    ? 'bg-blue-100 text-blue-700' 
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setCurrentView('analyze')}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  currentView === 'analyze' 
                    ? 'bg-blue-100 text-blue-700' 
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Analyze Student
              </button>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentView === 'dashboard' && (
          <div className="space-y-8">
            {/* Hero Section */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow-lg p-8 text-white">
              <div className="max-w-3xl">
                <h2 className="text-3xl font-bold mb-4">
                  AI-Powered Study Recommendations
                </h2>
                <p className="text-xl mb-6">
                  Using Neo4j graph database and local AI to find similar successful students 
                  and generate personalized study advice.
                </p>
                <button
                  onClick={getRandomRecommendations}
                  disabled={loading}
                  className="bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors disabled:opacity-50"
                >
                  {loading ? 'Analyzing...' : 'Try Demo - Get Random Student Analysis'}
                </button>
              </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <Users className="h-8 w-8 text-blue-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Total Students</p>
                    <p className="text-2xl font-semibold text-gray-900">{students.length}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <BookOpen className="h-8 w-8 text-green-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Learning Styles</p>
                    <p className="text-2xl font-semibold text-gray-900">{learningStyles.length}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <TrendingUp className="h-8 w-8 text-purple-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Avg Courses</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {students.length > 0 ? (students.reduce((sum, s) => sum + s.courseCount, 0) / students.length).toFixed(1) : '0'}
                    </p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <Brain className="h-8 w-8 text-red-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">AI Model</p>
                    <p className="text-2xl font-semibold text-gray-900">Local</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Learning Styles Distribution */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Learning Styles Distribution</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={learningStyleData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {learningStyleData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                {learningStyleData.map((style, index) => (
                  <div key={index} className="flex items-center">
                    <div 
                      className="w-3 h-3 rounded-full mr-2" 
                      style={{ backgroundColor: style.color }}
                    ></div>
                    <span className="text-sm text-gray-700">
                      {getLearningStyleIcon(style.name)} {style.name} ({style.value})
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {currentView === 'analyze' && (
          <div className="space-y-8">
            {/* Student Selection */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Select Student for Analysis</h3>
              <div className="flex gap-4">
                <select
                  value={selectedStudent}
                  onChange={(e) => setSelectedStudent(e.target.value)}
                  className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Choose a student...</option>
                  {students.map((student) => (
                    <option key={student.id} value={student.id}>
                      {student.name} ({student.learningStyle}, {student.courseCount} courses)
                    </option>
                  ))}
                </select>
                <button
                  onClick={analyzeStudent}
                  disabled={!selectedStudent || loading}
                  className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  {loading ? 'Analyzing...' : 'Analyze Student'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Recommendations Display */}
        {recommendations && (
          <div className="space-y-6">
            {/* Student Profile */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center mb-4">
                <User className="h-6 w-6 text-blue-600 mr-2" />
                <h3 className="text-lg font-semibold text-gray-900">Student Profile</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Name</p>
                  <p className="font-semibold">{recommendations.student.name}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Learning Style</p>
                  <p className="font-semibold">
                    {getLearningStyleIcon(recommendations.student.learningStyle)} {recommendations.student.learningStyle}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Preferred Pace</p>
                  <p className="font-semibold">{recommendations.student.preferredPace}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Courses Completed</p>
                  <p className="font-semibold">{recommendations.student.grades?.length || 0}</p>
                </div>
              </div>
            </div>

            {/* Performance Analysis */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center mb-4">
                <TrendingUp className="h-6 w-6 text-green-600 mr-2" />
                <h3 className="text-lg font-semibold text-gray-900">Performance Analysis</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <p className="text-3xl font-bold text-blue-600">
                    {recommendations.analysis.target_gpa?.toFixed(2)}
                  </p>
                  <p className="text-sm text-gray-500">Your GPA</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-green-600">
                    {recommendations.analysis.similar_avg_gpa?.toFixed(2)}
                  </p>
                  <p className="text-sm text-gray-500">Similar Students' Avg GPA</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-purple-600">
                    {recommendations.analysis.better_performers_count}/{recommendations.analysis.total_similar_count}
                  </p>
                  <p className="text-sm text-gray-500">Better Performers</p>
                </div>
              </div>
            </div>

            {/* AI Insight */}
            {recommendations.ai_insight && (
              <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg shadow-lg p-6 border border-purple-200">
                <div className="flex items-center mb-3">
                  <Lightbulb className="h-6 w-6 text-purple-600 mr-2" />
                  <h3 className="text-lg font-semibold text-gray-900">AI-Generated Insight</h3>
                </div>
                <p className="text-gray-700 italic">"{recommendations.ai_insight}"</p>
              </div>
            )}

            {/* Recommendations */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center mb-4">
                <AlertCircle className="h-6 w-6 text-red-600 mr-2" />
                <h3 className="text-lg font-semibold text-gray-900">Personalized Recommendations</h3>
              </div>
              <div className="space-y-4">
                {recommendations.recommendations?.map((rec, index) => (
                  <div key={index} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-gray-900">{rec.category}</h4>
                      {rec.priority && (
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(rec.priority)}`}>
                          {rec.priority.toUpperCase()}
                        </span>
                      )}
                    </div>
                    <p className="text-blue-600 font-medium mb-1">{rec.recommendation}</p>
                    <p className="text-gray-600 text-sm mb-2">{rec.explanation}</p>
                    {rec.ai_insight && (
                      <p className="text-purple-600 text-sm italic">AI: {rec.ai_insight}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-500">
            <p>AI Study Coach - HackUMBC 2025</p>
            <p className="text-sm mt-2">Powered by Neo4j Graph Database + Local AI</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
# UMBC Neo4j Academic Graph Database

This dataset contains synthetic academic data for UMBC, generated to model student degree pathways in Neo4j, with a focus on Computer Science and Biology departments.

## Data Model

The database follows this graph model:

- **Nodes**: Student, Course, Faculty, Degree, RequirementGroup, Term, Textbook
- **Relationships**:
  - Student-Course: COMPLETED, ENROLLED_IN
  - Student-Degree: PURSUING
  - Student-Student: SIMILAR_LEARNING_STYLE, SIMILAR_PERFORMANCE
  - Course-Course: PREREQUISITE_FOR, LEADS_TO, SIMILAR_CONTENT, SIMILAR_DIFFICULTY
  - Faculty-Course: TEACHES
  - RequirementGroup-Degree: PART_OF
  - Course-RequirementGroup: FULFILLS
  - Course-Term: OFFERED_IN
  - Course-Textbook: REQUIRES, RECOMMENDS
  - Student-Textbook: VIEWED_PAGE, INTERACTED_WITH

## Example Queries and Use Cases

### 1. Find Optimal Next Courses for a Student

```cypher
// Find optimal next courses based on learning style and prerequisites
MATCH (student:Student)-[:PURSUING]->(degree:Degree)
WHERE student.id = 'AB12345' // Replace with a real campus ID
MATCH (term:Term {id: 'Fall2023'}) // Update with appropriate term
MATCH (course:Course)-[:OFFERED_IN]->(term)
MATCH (course)-[:FULFILLS]->(:RequirementGroup)-[:PART_OF]->(degree)

// Ensure prerequisites are met
WHERE NOT EXISTS {
  MATCH (prereq:Course)-[:PREREQUISITE_FOR]->(course)
  WHERE NOT (student)-[:COMPLETED]->(prereq)
}

// Student hasn't already completed the course
AND NOT (student)-[:COMPLETED]->(course)

// Find similar students and their experiences with these courses
OPTIONAL MATCH (student)-[sim:SIMILAR_LEARNING_STYLE]->(similar:Student)-[comp:COMPLETED]->(course)
WHERE sim.similarity > 0.7

WITH student, course, term, degree,
     CASE WHEN COUNT(comp) > 0 
          THEN AVG(comp.difficulty) 
          ELSE course.avgDifficulty END AS predictedDifficulty,
     COUNT(comp) AS similarStudentsCount

// Check how many future courses this would unlock
OPTIONAL MATCH (course)-[:PREREQUISITE_FOR]->(futureCourse)
WHERE (futureCourse)-[:FULFILLS]->(:RequirementGroup)-[:PART_OF]->(degree)

RETURN course.id AS courseId,
       course.name AS courseName,
       course.credits AS credits,
       predictedDifficulty,
       COUNT(futureCourse) AS unlockedCourses,
       similarStudentsCount,
       course.instructionModes AS availableModes
ORDER BY predictedDifficulty ASC, unlockedCourses DESC, credits DESC
LIMIT 5
```

**Use Case**: Course Planning
- Helps students select courses that align with their learning style
- Considers prerequisite chains to optimize degree progress
- Predicts difficulty based on similar students' experiences
- Shows how many future courses each option unlocks

**Graph DB Advantage**: 
- Easily traverses prerequisite chains without complex joins
- Efficiently finds similar students and their course experiences
- Natural representation of course relationships and dependencies

### 2. Analyze Student Reading Patterns

```cypher
// Compare reading patterns between high and low performing students
MATCH (student:Student)-[comp:COMPLETED]->(course:Course)
MATCH (student)-[view:VIEWED_PAGE]->(textbook:Textbook)<-[:REQUIRES]-(course)
WITH student, course, textbook, comp,
     COUNT(view) AS totalPages,
     AVG(view.duration) AS avgTimePerPage,
     COLLECT(view.timestamp) AS viewTimes
WITH student, course, textbook,
     totalPages,
     avgTimePerPage,
     // Calculate reading pattern metrics
     CASE WHEN size(viewTimes) > 1
          THEN reduce(s = 0, i in range(0, size(viewTimes)-2) |
               s + duration.between(
                    datetime(replace(viewTimes[i], ' ', 'T') + 'Z'),
                    datetime(replace(viewTimes[i+1], ' ', 'T') + 'Z')
               ).days)
          ELSE 0 END AS totalGaps,
     size(viewTimes) AS totalSessions,
     comp.grade AS grade
WHERE comp.grade IN ['A', 'A-', 'B+', 'C', 'C-', 'D']
RETURN student.id,
       course.name,
       grade,
       totalPages,
       avgTimePerPage,
       totalGaps / totalSessions AS avgDaysBetweenSessions,
       CASE 
         WHEN grade IN ['A', 'A-', 'B+'] THEN 'High Performing'
         ELSE 'Low Performing'
       END AS performanceCategory
ORDER BY grade ASC
```

**Use Case**: Study Pattern Analysis
- Identifies effective reading patterns that correlate with success
- Helps advisors recommend study strategies
- Shows correlation between consistent reading and performance
- Enables early intervention for students with suboptimal reading patterns

**Graph DB Advantage**:
- Efficiently analyzes temporal patterns across multiple relationships
- Easy to correlate reading behavior with performance
- Natural representation of student-textbook-course relationships

### 3. Identify At-Risk Students Based on Textbook Usage

```cypher
// Find students who might be at risk based on textbook interaction patterns
MATCH (student:Student)-[comp:COMPLETED]->(course:Course)
MATCH (course)-[:REQUIRES]->(textbook:Textbook)
OPTIONAL MATCH (student)-[view:VIEWED_PAGE]->(textbook)
WITH student, course, textbook,
     COUNT(view) AS totalViews,
     COLLECT(view.timestamp) AS viewTimes
WITH student, course,
     AVG(totalViews) AS avgViewsPerTextbook,
     CASE WHEN size(viewTimes) > 0
          THEN reduce(s = 0, t in viewTimes |
               s + CASE WHEN duration.between(
                    datetime(replace(t, ' ', 'T') + 'Z'),
                    datetime(replace(course.endDate, ' ', 'T') + 'Z')
               ).days < 7
                    THEN 1 ELSE 0 END) / size(viewTimes)
          ELSE 0 END AS examWeekRatio
WHERE examWeekRatio > 0.7 OR avgViewsPerTextbook < 10
RETURN student.id,
       student.name,
       COUNT(DISTINCT course) AS coursesAtRisk,
       ROUND(AVG(avgViewsPerTextbook)) AS avgTextbookViews,
       ROUND(AVG(examWeekRatio) * 100) AS percentageLastMinuteReading
ORDER BY coursesAtRisk DESC, avgTextbookViews ASC
```

**Use Case**: Early Intervention
- Identifies students who might be struggling with study habits
- Detects cramming behavior vs. consistent reading
- Enables proactive academic support
- Helps advisors identify students needing study skills workshops

**Graph DB Advantage**:
- Complex pattern matching across multiple relationships
- Efficient temporal analysis of study behaviors
- Easy correlation of reading patterns with course performance

### 4. Analyze Textbook Effectiveness

```cypher
// Analyze textbook effectiveness by comparing student interactions and performance
MATCH (course:Course)-[:REQUIRES]->(textbook:Textbook)
MATCH (student:Student)-[comp:COMPLETED]->(course)
OPTIONAL MATCH (student)-[view:VIEWED_PAGE]->(textbook)
OPTIONAL MATCH (student)-[interact:INTERACTED_WITH]->(textbook)
WITH course, textbook,
     COUNT(DISTINCT student) AS totalStudents,
     AVG(CASE WHEN comp.grade IN ['A', 'A-', 'B+'] THEN 1 ELSE 0 END) AS successRate,
     AVG(CASE WHEN view IS NOT NULL THEN 1 ELSE 0 END) AS readingRate,
     AVG(CASE WHEN interact.interactionType = 'highlight' THEN 1 ELSE 0 END) AS highlightRate,
     AVG(CASE WHEN interact.interactionType = 'note' THEN 1 ELSE 0 END) AS noteRate
RETURN course.name,
       textbook.name,
       totalStudents,
       ROUND(successRate * 100) AS successPercentage,
       ROUND(readingRate * 100) AS readingPercentage,
       ROUND(highlightRate * 100) AS highlightPercentage,
       ROUND(noteRate * 100) AS notePercentage
ORDER BY successRate DESC
```

**Use Case**: Textbook Evaluation
- Evaluates textbook effectiveness based on student success
- Analyzes different types of engagement (reading, highlighting, notes)
- Helps departments make informed decisions about course materials
- Identifies which textbooks promote active learning

**Graph DB Advantage**:
- Easy aggregation of multiple interaction types
- Efficient correlation of textbook usage with performance
- Natural representation of different interaction relationships

### 5. Find Similar Students Based on Reading Patterns

```cypher
// Find students with similar reading patterns for study group recommendations
MATCH (student:Student {id: 'AB12345'})-[view1:VIEWED_PAGE]->(textbook:Textbook)
MATCH (other:Student)-[view2:VIEWED_PAGE]->(textbook)
WHERE other.id <> student.id
WITH student, other, textbook,
     COLLECT(view1.timestamp) AS student1Times,
     COLLECT(view2.timestamp) AS student2Times,
     COUNT(DISTINCT view1) AS student1Views,
     COUNT(DISTINCT view2) AS student2Views
WITH student, other, textbook,
     AVG(ABS(student1Views - student2Views)) AS viewDifference,
     AVG(CASE 
         WHEN size(student1Times) > 0 AND size(student2Times) > 0
         THEN duration.between(
              datetime(replace(student1Times[0], ' ', 'T') + 'Z'),
              datetime(replace(student2Times[0], ' ', 'T') + 'Z')
         ).hours
         ELSE 24 END) AS timingDifference
WHERE viewDifference < 10 AND timingDifference < 12
WITH other.id AS otherId,
     other.learningStyle AS learningStyle,
     viewDifference,
     timingDifference,
     COLLECT(DISTINCT textbook.name) AS commonTextbooks
RETURN otherId,
       learningStyle,
       ROUND(viewDifference) AS avgViewDifference,
       ROUND(timingDifference) AS avgTimingDifferenceHours,
       commonTextbooks
ORDER BY viewDifference ASC, timingDifference ASC
LIMIT 5
```

### 6. Generate Personalized Textbook Usage Insights

```cypher
// Find textbook consumption patterns of similar but higher-performing students
MATCH (target:Student {id: $studentId})
MATCH (target)-[comp:COMPLETED]->(course:Course)
WITH target, course, comp.grade AS grade

// Find similar students based on multiple criteria
MATCH (target)-[styleSim:SIMILAR_LEARNING_STYLE]->(similar:Student)
WHERE styleSim.similarity > 0.7  // High learning style similarity

// Ensure they're pursuing the same degree
MATCH (target)-[:PURSUING]->(degree:Degree)
MATCH (similar)-[:PURSUING]->(degree)

// Find students who performed better in the same courses
MATCH (similar)-[simComp:COMPLETED]->(course)
WHERE simComp.grade > grade  // Better grade in same course

// Get their textbook interactions for this course
MATCH (similar)-[view:VIEWED_PAGE]->(textbook:Textbook)
WHERE view.courseId = course.id

// Calculate reading patterns
WITH target, similar, course, textbook, view,
     duration.between(
       datetime(split(view.timestamp, ' ')[0] + 'T' + split(view.timestamp, ' ')[1] + 'Z'),
       datetime(split(view.timestamp, ' ')[0] + 'T' + split(view.timestamp, ' ')[1] + 'Z') + duration({minutes: view.duration})
     ) AS readingSession

// Group by student and course to analyze patterns
WITH target, similar, course,
     COUNT(DISTINCT view) AS totalPageViews,
     COUNT(DISTINCT date(datetime(split(view.timestamp, ' ')[0] + 'T' + split(view.timestamp, ' ')[1] + 'Z'))) AS uniqueReadingDays,
     AVG(view.duration) AS avgReadingDuration,
     MIN(view.timestamp) AS firstRead,
     MAX(view.timestamp) AS lastRead,
     duration.between(
       datetime(split(MIN(view.timestamp), ' ')[0] + 'T' + split(MIN(view.timestamp), ' ')[1] + 'Z'),
       datetime(split(MAX(view.timestamp), ' ')[0] + 'T' + split(MAX(view.timestamp), ' ')[1] + 'Z')
     ) AS readingSpan

// Calculate reading consistency and intensity
WITH target, similar, course,
     totalPageViews,
     uniqueReadingDays,
     avgReadingDuration,
     readingSpan,
     CASE 
       WHEN readingSpan.days > 0 
       THEN toFloat(uniqueReadingDays) / readingSpan.days 
       ELSE 0 
     END AS readingConsistency,
     CASE 
       WHEN readingSpan.days > 0 
       THEN toFloat(totalPageViews) / readingSpan.days 
       ELSE 0 
     END AS readingIntensity

// Get target student's patterns for comparison
MATCH (target)-[targetView:VIEWED_PAGE]->(targetTextbook:Textbook)
WHERE targetView.courseId = course.id
WITH target, similar, course,
     totalPageViews,
     uniqueReadingDays,
     avgReadingDuration,
     readingConsistency,
     readingIntensity,
     COUNT(DISTINCT targetView) AS targetPageViews,
     COUNT(DISTINCT date(datetime(split(targetView.timestamp, ' ')[0] + 'T' + split(targetView.timestamp, ' ')[1] + 'Z'))) AS targetReadingDays,
     AVG(targetView.duration) AS targetAvgDuration

// Calculate differences in reading patterns
WITH target, similar, course,
     totalPageViews - targetPageViews AS pageViewDiff,
     uniqueReadingDays - targetReadingDays AS readingDaysDiff,
     avgReadingDuration - targetAvgDuration AS durationDiff,
     readingConsistency,
     readingIntensity

// Aggregate insights across all similar students
WITH target, course,
     AVG(pageViewDiff) AS avgPageViewDiff,
     AVG(readingDaysDiff) AS avgReadingDaysDiff,
     AVG(durationDiff) AS avgDurationDiff,
     AVG(readingConsistency) AS avgReadingConsistency,
     AVG(readingIntensity) AS avgReadingIntensity,
     COUNT(DISTINCT similar) AS similarStudentCount

// Format recommendations
RETURN course.id AS courseId,
       course.name AS courseName,
       similarStudentCount AS numberOfSimilarStudents,
       CASE 
         WHEN avgPageViewDiff > 0 THEN 'Read more pages'
         ELSE 'Read fewer pages but more thoroughly'
       END AS pageViewRecommendation,
       CASE 
         WHEN avgReadingDaysDiff > 0 THEN 'Spread reading across more days'
         ELSE 'Consolidate reading into fewer, longer sessions'
       END AS readingScheduleRecommendation,
       CASE 
         WHEN avgDurationDiff > 0 THEN 'Spend more time per reading session'
         ELSE 'Take shorter, more focused reading breaks'
       END AS durationRecommendation,
       CASE 
         WHEN avgReadingConsistency > 0.5 THEN 'Maintain regular reading schedule'
         ELSE 'Establish more consistent reading habits'
       END AS consistencyRecommendation,
       CASE 
         WHEN avgReadingIntensity > 0.5 THEN 'Increase overall reading intensity'
         ELSE 'Focus on quality over quantity'
       END AS intensityRecommendation,
       avgPageViewDiff,
       avgReadingDaysDiff,
       avgDurationDiff,
       avgReadingConsistency,
       avgReadingIntensity
ORDER BY similarStudentCount DESC, avgPageViewDiff DESC
LIMIT 10
```

**Use Case**: Academic Advising
- Provides personalized textbook usage recommendations based on successful students
- Analyzes reading patterns across multiple dimensions (frequency, duration, consistency)
- Helps students optimize their study habits by comparing with similar but higher-performing peers
- Generates actionable insights for improving textbook engagement

**Graph DB Advantage**:
- Efficiently finds similar students based on learning style and degree program
- Natural representation of temporal reading patterns and relationships
- Easy comparison of reading behaviors between target and similar students
- Complex pattern matching across multiple relationship types (learning style, course completion, textbook usage)

**Key Metrics**:
- Page View Differences: Compares total pages read between target and similar students
- Reading Days: Analyzes how reading is distributed across time
- Session Duration: Examines typical reading session lengths
- Reading Consistency: Measures regularity of reading habits
- Reading Intensity: Evaluates overall reading engagement

**Returned Columns**:
- courseId/courseName: Identifies the course being analyzed
- numberOfSimilarStudents: Number of similar students used for comparison
- Various Recommendations: Personalized advice for improving reading habits
- Difference Metrics: Detailed comparisons with similar students' patterns
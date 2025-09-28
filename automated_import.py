import os
import glob
from neo4j import GraphDatabase

# Neo4j connection details
URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "yourpassword"

def import_cypher_files():
    # Connect to Neo4j
    driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
    
    try:
        with driver.session() as session:
            print("Creating constraints...")
            # Create constraints first
            constraints = [
                "CREATE CONSTRAINT student_id IF NOT EXISTS FOR (s:Student) REQUIRE s.id IS UNIQUE;",
                "CREATE CONSTRAINT course_id IF NOT EXISTS FOR (c:Course) REQUIRE c.id IS UNIQUE;",
                "CREATE CONSTRAINT faculty_id IF NOT EXISTS FOR (f:Faculty) REQUIRE f.id IS UNIQUE;",
                "CREATE CONSTRAINT degree_id IF NOT EXISTS FOR (d:Degree) REQUIRE d.id IS UNIQUE;",
                "CREATE CONSTRAINT requirement_id IF NOT EXISTS FOR (r:RequirementGroup) REQUIRE r.id IS UNIQUE;",
                "CREATE CONSTRAINT term_id IF NOT EXISTS FOR (t:Term) REQUIRE t.id IS UNIQUE;",
                "CREATE CONSTRAINT textbook_id IF NOT EXISTS FOR (tb:Textbook) REQUIRE s.id IS UNIQUE;"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                    print(f"✓ Constraint created")
                except Exception as e:
                    print(f"Constraint already exists or error: {e}")
            
            print("\nImporting Cypher files...")
            # Get all .cypher files in order
            cypher_files = glob.glob("umbc_data/cypher/*.cypher")
            cypher_files.sort()  # Import in order
            
            for file_path in cypher_files:
                print(f"Importing {file_path}...")
                with open(file_path, 'r', encoding='utf-8') as file:
                    cypher_content = file.read()
                    
                    # Split by semicolon and execute each statement
                    statements = [stmt.strip() for stmt in cypher_content.split(';') if stmt.strip()]
                    
                    for i, statement in enumerate(statements):
                        try:
                            session.run(statement)
                            if i % 100 == 0:  # Progress indicator
                                print(f"  Executed {i+1}/{len(statements)} statements...")
                        except Exception as e:
                            print(f"  Error in statement {i+1}: {e}")
                            continue
                
                print(f"✓ Completed {file_path}")
            
            # Verify import
            print("\nVerifying import...")
            result = session.run("MATCH (n) RETURN labels(n)[0] as NodeType, count(n) as Count")
            for record in result:
                print(f"  {record['NodeType']}: {record['Count']}")
                
    except Exception as e:
        print(f"Connection error: {e}")
        print("Make sure Neo4j is running and credentials are correct")
    
    finally:
        driver.close()

if __name__ == "__main__":
    import_cypher_files()
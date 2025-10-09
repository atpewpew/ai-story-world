"""Neo4j backend for knowledge graph with MERGE semantics and de-duplication."""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False


class Neo4jGraph:
    def __init__(self, uri: str = None, username: str = None, password: str = None):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        self.driver = None
        
        if NEO4J_AVAILABLE:
            try:
                self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
                # Test connection
                with self.driver.session() as session:
                    session.run("RETURN 1")
            except Exception as e:
                print(f"Neo4j connection failed: {e}")
                self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def upsert_fact(self, session_id: str, fact: Dict[str, Any]) -> bool:
        """Upsert a fact with MERGE semantics to avoid duplicates"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                fact_type = fact.get("type", "unknown")
                subject = fact.get("subject", "").strip()
                predicate = fact.get("predicate", "").strip()
                obj = fact.get("object", "").strip()
                certainty = fact.get("certainty", 0.5)
                
                if not all([subject, predicate, obj]):
                    return False
                
                if fact_type == "possession":
                    # MERGE character and item, then create OWNS relationship
                    query = """
                    MERGE (c:Character {name: $subject, session_id: $session_id})
                    MERGE (i:Item {name: $object, session_id: $session_id})
                    MERGE (c)-[r:OWNS {certainty: $certainty, created_at: datetime()}]->(i)
                    RETURN r
                    """
                    session.run(query, {
                        "subject": subject,
                        "object": obj,
                        "session_id": session_id,
                        "certainty": certainty
                    })
                
                elif fact_type == "location":
                    # MERGE character and location, then create IN_LOCATION relationship
                    query = """
                    MERGE (c:Character {name: $subject, session_id: $session_id})
                    MERGE (l:Location {name: $object, session_id: $session_id})
                    MERGE (c)-[r:IN_LOCATION {certainty: $certainty, created_at: datetime()}]->(l)
                    RETURN r
                    """
                    session.run(query, {
                        "subject": subject,
                        "object": obj,
                        "session_id": session_id,
                        "certainty": certainty
                    })
                
                elif fact_type == "relationship":
                    # MERGE two characters and create relationship
                    query = """
                    MERGE (c1:Character {name: $subject, session_id: $session_id})
                    MERGE (c2:Character {name: $object, session_id: $session_id})
                    MERGE (c1)-[r:HAS_RELATIONSHIP {type: $predicate, certainty: $certainty, created_at: datetime()}]->(c2)
                    RETURN r
                    """
                    session.run(query, {
                        "subject": subject,
                        "object": obj,
                        "predicate": predicate,
                        "session_id": session_id,
                        "certainty": certainty
                    })
                
                return True
                
        except Exception as e:
            print(f"Neo4j upsert failed: {e}")
            return False

    def get_session_snapshot(self, session_id: str) -> Dict[str, Any]:
        """Get complete KG snapshot for a session"""
        if not self.driver:
            return {"facts": []}
        
        try:
            with self.driver.session() as session:
                # Get all characters and their relationships
                query = """
                MATCH (c:Character {session_id: $session_id})
                OPTIONAL MATCH (c)-[r1:OWNS]->(i:Item {session_id: $session_id})
                OPTIONAL MATCH (c)-[r2:IN_LOCATION]->(l:Location {session_id: $session_id})
                OPTIONAL MATCH (c)-[r3:HAS_RELATIONSHIP]->(c2:Character {session_id: $session_id})
                RETURN c.name as character, 
                       collect(DISTINCT {item: i.name, certainty: r1.certainty}) as items,
                       collect(DISTINCT {location: l.name, certainty: r2.certainty}) as locations,
                       collect(DISTINCT {target: c2.name, type: r3.type, certainty: r3.certainty}) as relationships
                """
                
                result = session.run(query, {"session_id": session_id})
                characters = []
                
                for record in result:
                    char_data = {
                        "name": record["character"],
                        "items": [item for item in record["items"] if item["item"]],
                        "locations": [loc for loc in record["locations"] if loc["location"]],
                        "relationships": [rel for rel in record["relationships"] if rel["target"]]
                    }
                    characters.append(char_data)
                
                return {
                    "session_id": session_id,
                    "characters": characters,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"Neo4j snapshot failed: {e}")
            return {"facts": []}

    def query_characters_items(self, session_id: str, character_name: str) -> List[str]:
        """Get all items owned by a character"""
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (c:Character {name: $character, session_id: $session_id})-[:OWNS]->(i:Item {session_id: $session_id})
                RETURN i.name as item
                """
                result = session.run(query, {
                    "character": character_name,
                    "session_id": session_id
                })
                return [record["item"] for record in result]
        except Exception:
            return []

    def query_character_location(self, session_id: str, character_name: str) -> Optional[str]:
        """Get current location of a character"""
        if not self.driver:
            return None
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (c:Character {name: $character, session_id: $session_id})-[:IN_LOCATION]->(l:Location {session_id: $session_id})
                RETURN l.name as location
                ORDER BY l.created_at DESC
                LIMIT 1
                """
                result = session.run(query, {
                    "character": character_name,
                    "session_id": session_id
                })
                record = result.single()
                return record["location"] if record else None
        except Exception:
            return None

    def delete_session(self, session_id: str) -> bool:
        """Delete all nodes and relationships for a session"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (n {session_id: $session_id})
                DETACH DELETE n
                """
                session.run(query, {"session_id": session_id})
                return True
        except Exception as e:
            print(f"Neo4j delete failed: {e}")
            return False


# Global instance
_neo4j_graph: Optional[Neo4jGraph] = None

def get_neo4j_graph() -> Neo4jGraph:
    global _neo4j_graph
    if _neo4j_graph is None:
        _neo4j_graph = Neo4jGraph()
    return _neo4j_graph

"""JSON-based KG fallback with Neo4j option."""

import os
import json
from typing import Dict, Any, Optional
from .neo4j_graph import get_neo4j_graph


KG_DIR = os.path.join("data", "kg")
os.makedirs(KG_DIR, exist_ok=True)


def _path(session_id: str) -> str:
    return os.path.join(KG_DIR, f"{session_id}.json")


def load(session_id: str) -> Dict[str, Any]:
    p = _path(session_id)
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"facts": []}


def save(session_id: str, data: Dict[str, Any]) -> None:
    p = _path(session_id)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, p)


def upsert_fact(session_id: str, fact: Dict[str, Any]) -> None:
    """Upsert fact to Neo4j if available, otherwise JSON fallback"""
    neo4j_graph = get_neo4j_graph()
    
    # Try Neo4j first
    if neo4j_graph.driver:
        success = neo4j_graph.upsert_fact(session_id, fact)
        if success:
            return
    
    # Fallback to JSON
    kg = load(session_id)
    if fact not in kg["facts"]:
        kg["facts"].append(fact)
    save(session_id, kg)


def get_session_snapshot(session_id: str) -> Dict[str, Any]:
    """Get KG snapshot from Neo4j or JSON"""
    neo4j_graph = get_neo4j_graph()
    
    if neo4j_graph.driver:
        return neo4j_graph.get_session_snapshot(session_id)
    
    # Fallback to JSON
    return load(session_id)


def delete_session(session_id: str) -> bool:
    """Delete session from Neo4j or JSON"""
    neo4j_graph = get_neo4j_graph()
    
    if neo4j_graph.driver:
        return neo4j_graph.delete_session(session_id)
    
    # Fallback to JSON
    p = _path(session_id)
    if os.path.exists(p):
        os.remove(p)
        return True
    return False


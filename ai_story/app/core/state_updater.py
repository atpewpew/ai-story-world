from typing import Any, Dict, List


class StateUpdater:
    def __init__(self, session_manager) -> None:
        self.session_manager = session_manager

    def apply_facts(self, session_id: str, facts: List[Dict[str, Any]]) -> None:
        if not facts:
            return
        session = self.session_manager.load_session(session_id)
        if not session:
            return
        world = session.get("world", {"characters": {}, "items": {}, "locations": {}})

        for fact in facts:
            ftype = fact.get("type")
            if ftype == "possession":
                owner = fact.get("subject", "").strip() or "Player"
                item = fact.get("object", "").strip() or "item"
                # Ensure item exists and set owner
                items = world.setdefault("items", {})
                item_entry = items.setdefault(item, {"owner": None, "description": ""})
                item_entry["owner"] = owner
                # Add to character props
                characters = world.setdefault("characters", {})
                char = characters.setdefault(owner, {"location": None, "items": [], "props": {}})
                if item not in char["items"]:
                    char["items"].append(item)
            elif ftype == "location":
                subject = fact.get("subject", "").strip() or "Player"
                location = fact.get("object", "").strip() or "Somewhere"
                characters = world.setdefault("characters", {})
                char = characters.setdefault(subject, {"location": None, "items": [], "props": {}})
                char["location"] = location
                locations = world.setdefault("locations", {})
                loc = locations.setdefault(location, {"desc": "", "occupants": []})
                if subject not in loc["occupants"]:
                    loc["occupants"].append(subject)
            elif ftype == "relationship":
                subject = fact.get("subject", "").strip() or "Player"
                object_entity = fact.get("object", "").strip() or "someone"
                predicate = fact.get("predicate", "").strip() or "interacts with"
                
                # Add both characters to the world
                characters = world.setdefault("characters", {})
                
                # Add subject character
                char = characters.setdefault(subject, {"location": None, "items": [], "props": {}})
                
                # Add object character (if it's a person/character)
                if object_entity not in ["someone", "mysterious figure"]:
                    char_obj = characters.setdefault(object_entity, {"location": None, "items": [], "props": {}})
                    # Add relationship info
                    if "relationships" not in char:
                        char["relationships"] = []
                    if "relationships" not in char_obj:
                        char_obj["relationships"] = []
                    
                    relationship = f"{predicate} {object_entity}"
                    if relationship not in char["relationships"]:
                        char["relationships"].append(relationship)
                    
                    reverse_relationship = f"met by {subject}"
                    if reverse_relationship not in char_obj["relationships"]:
                        char_obj["relationships"].append(reverse_relationship)

        # Persist KG snapshot
        try:
            from ..memory import graph as kg
            for f in facts:
                kg.upsert_fact(session_id, f)
        except Exception:
            pass

        self.session_manager.update_world(session_id, world)



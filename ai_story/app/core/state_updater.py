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

        # Persist KG snapshot
        try:
            from ..memory import graph as kg
            for f in facts:
                kg.upsert_fact(session_id, f)
        except Exception:
            pass

        self.session_manager.update_world(session_id, world)



# scripts/sync_group_owners.py
import uuid
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime
# from utils.jsondb import JsonDB
class JsonDB:
    def __init__(self, file_path: str):
        self.file = Path(file_path)
        if not self.file.parent.exists():
            self.file.parent.mkdir(parents=True, exist_ok=True)
        if not self.file.exists():
            self.file.write_text("[]", encoding="utf-8")

    def read_all(self) -> List[Dict[str, Any]]:
        return json.loads(self.file.read_text(encoding="utf-8"))

    def write_all(self, data: List[Dict[str, Any]]):
        self.file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _serialize_datetime(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat() + "Z"
        raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
    
    def insert_or_replace(self, key: str, value: Any, new_doc: Dict[str, Any]):
        data = self.read_all()
        filtered = [doc for doc in data if doc.get(key) != value]
        filtered.append(new_doc)
        self.write_all(filtered)

    def find_one(self, key: str, value: Any) -> Dict[str, Any] | None:
        for doc in self.read_all():
            if doc.get(key) == value:
                return doc
        return None

groups_db = JsonDB("db/collection_groups.json")
group_members_db = JsonDB("db/collection_group_members.json")

def _format_datetime(dt: datetime) -> str:
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    else:
        return dt.isoformat().replace("+00:00", "Z")

def sync_owners():
    groups = groups_db.read_all()
    members = group_members_db.read_all()

    existing_wallets = {(m["group_id"], m["wallet_address"]) for m in members}

    new_members = []
    for g in groups:
        key = (g["group_id"], g["wallet_address"])
        if key not in existing_wallets:
            new_members.append({
                "_id": uuid.uuid4().hex,
                "group_id": g["group_id"],
                "wallet_address": g["wallet_address"],
                "role": "owner",
                "joined_at": _format_datetime(datetime.utcnow())
            })
            print(f"✅ Added owner {g['wallet_address']} to group {g['group_id']}")

    if new_members:
        group_members_db.write_all(members + new_members)
        print(f"✨ Synced {len(new_members)} owners into collection_group_members.json")
    else:
        print("👍 All owners already exist in collection_group_members.json")

if __name__ == "__main__":
    sync_owners()

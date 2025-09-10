import json
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

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
    
    def find_many(self, field: str, value):
        return [item for item in self.read_all() if item.get(field) == value]
    
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

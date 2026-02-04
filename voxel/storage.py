import json
import os
from typing import Any, Dict, Optional


class WorldStorage:
    def __init__(self, save_path: str) -> None:
        self.save_path = save_path
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

    def load(self) -> Optional[Dict[str, Any]]:
        if not os.path.exists(self.save_path):
            return None
        with open(self.save_path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def save(self, data: Dict[str, Any]) -> None:
        with open(self.save_path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)

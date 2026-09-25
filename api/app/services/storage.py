import hashlib
from pathlib import Path
from ..config import get_settings

class FileBodyStorage:
    def __init__(self): self.root = Path(get_settings().body_storage_path); self.root.mkdir(parents=True, exist_ok=True)
    def put(self, request_id: str, content: bytes) -> str:
        # Generated deterministic identifier only; never use client filenames.
        name = hashlib.sha256(request_id.encode()).hexdigest()
        path = self.root / name
        path.write_bytes(content)
        return name
    def get(self, name: str) -> bytes:
        if not name or Path(name).name != name: raise ValueError("Invalid storage key")
        return (self.root / name).read_bytes()
storage = FileBodyStorage()

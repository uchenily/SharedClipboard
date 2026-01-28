from dataclasses import dataclass, field
from threading import RLock
from typing import Dict, Optional, Tuple


@dataclass
class InMemoryCache:
    lock: RLock = field(default_factory=RLock)
    history_pages: Dict[Tuple[int, int], dict] = field(default_factory=dict)
    history_by_id: Dict[int, dict] = field(default_factory=dict)
    file_paths: Dict[str, Optional[str]] = field(default_factory=dict)

    def get_history_page(self, limit: int, offset: int) -> Optional[dict]:
        key = (limit, offset)
        with self.lock:
            return self.history_pages.get(key)

    def set_history_page(self, limit: int, offset: int, value: dict) -> None:
        key = (limit, offset)
        with self.lock:
            self.history_pages[key] = value

    def get_history_by_id(self, history_id: int) -> Optional[dict]:
        with self.lock:
            return self.history_by_id.get(history_id)

    def set_history_by_id(self, history_id: int, value: dict) -> None:
        with self.lock:
            self.history_by_id[history_id] = value

    def get_file_path(self, checksum: str) -> Tuple[bool, Optional[str]]:
        with self.lock:
            if checksum in self.file_paths:
                return True, self.file_paths[checksum]
            return False, None

    def set_file_path(self, checksum: str, path: Optional[str]) -> None:
        with self.lock:
            self.file_paths[checksum] = path

    def invalidate_history(self) -> None:
        with self.lock:
            self.history_pages.clear()
            self.history_by_id.clear()

    def invalidate_file_path(self, checksum: str) -> None:
        with self.lock:
            if checksum in self.file_paths:
                del self.file_paths[checksum]

    def clear_all(self) -> None:
        with self.lock:
            self.history_pages.clear()
            self.history_by_id.clear()
            self.file_paths.clear()


cache = InMemoryCache()

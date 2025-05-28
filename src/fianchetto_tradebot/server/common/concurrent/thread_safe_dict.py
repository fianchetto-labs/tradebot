import threading

class ThreadSafeDict:
    def __init__(self, normal_dict:dict):
        self._lock = threading.RLock()
        self._dict = normal_dict

    def __setitem__(self, key, value):
        with self._lock:
            self._dict[key] = value

    def __getitem__(self, key):
        with self._lock:
            return self._dict[key]

    def __delitem__(self, key):
        with self._lock:
            del self._dict[key]

    def get(self, key, default=None):
        with self._lock:
            return self._dict.get(key, default)

    def setdefault(self, key, default=None):
        with self._lock:
            return self._dict.setdefault(key, default)

    def update(self, *args, **kwargs):
        with self._lock:
            self._dict.update(*args, **kwargs)

    def items(self):
        with self._lock:
            return list(self._dict.items())  # Snapshot

    def keys(self):
        with self._lock:
            return list(self._dict.keys())

    def values(self):
        with self._lock:
            return list(self._dict.values())

    def __contains__(self, key):
        with self._lock:
            return key in self._dict

    def __len__(self):
        with self._lock:
            return len(self._dict)

    def __repr__(self):
        with self._lock:
            return repr(self._dict)
from concurrent.futures import ThreadPoolExecutor


class PersistentThreadPool:
    def __init__(self, max_workers=4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def submit(self, fn, *args, **kwargs):
        return self.executor.submit(fn, *args, **kwargs)

    def shutdown(self, wait=True):
        self.executor.shutdown(wait=wait)
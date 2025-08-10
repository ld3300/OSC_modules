import threading

class OSCHandler:
    def __init__(self, ...):
        self.batch = []
        self.batch_timer = None
        self.batch_timeout = 0.1  # seconds

    def _flush_batch(self):
        if self.batch:
            logger.info(f"Batch: {self.batch}")
            self.batch = []

    def _start_batch_timer(self):
        if self.batch_timer:
            self.batch_timer.cancel()
        self.batch_timer = threading.Timer(self.batch_timeout, self._flush_batch)
        self.batch_timer.start()

    def default_handler(self, address, *args):
        self.batch.append((address, args))
        self._start_batch_timer()
from threading import Thread
from queue import Queue


class Task(Thread):
    def __init__(self, callback=None, **kwargs):
        self.job_queue = Queue()
        self.callback = callback
        super(Task, self).__init__(**kwargs)
        self.daemon = True

    def run(self):
        while True:
            job = self.job_queue.get()
            self.process(job)
            if self.callback:
                self.callback(job)

    def submit_job(self, job):
        self.job_queue.put(job)

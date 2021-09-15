import multiprocessing
from time import sleep

from kgextractiontoolbox.util.multiprocessing.Worker import SHUTDOWN_SIGNAL
from kgextractiontoolbox.util.multiprocessing.WorkerProcess import WorkerProcess


class ProducerWorker(WorkerProcess):
    def __init__(self, task_queue: multiprocessing.Queue, produce, no_workers: int, max_tasks: int = 1000, ):
        """

        :param task_queue:
        :param produce:
        :param max_tasks:
        :param prepare:
        :param shutdown:
        """
        super().__init__()

        self.task_queue = task_queue
        self.produce = produce
        self.max_tasks = max_tasks
        self.no_workers = no_workers
        self.__running = True

    def run(self):
        task_iter = iter(self.produce())
        while self.__running:
            tasks_to_add = self.max_tasks - self.task_queue.qsize()
            for i in range(0, tasks_to_add):
                try:
                    task = next(task_iter)
                    self.task_queue.put(task)
                except StopIteration:
                    for n in range(0, self.no_workers):
                        self.task_queue.put(SHUTDOWN_SIGNAL)
                    self.__running = False
                    break
            sleep(0.01)

    def stop(self):
        self.__running = False

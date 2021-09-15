import multiprocessing
import queue
from time import sleep

from kgextractiontoolbox.util.multiprocessing.WorkerProcess import WorkerProcess

SHUTDOWN_SIGNAL = "shutdown_signal"


class Worker(WorkerProcess):
    def __init__(self, task_queue: multiprocessing.Queue, result_queue: multiprocessing.Queue,
                 do_task, prepare=None, shutdown=None):
        """

        :param task_queue:
        :param result_queue:
        :param do_task: Callable, takes task, returns result
        :param prepare: Callable, before worker loop
        :param shutdown: Callable, after worker loop
        """
        super().__init__()
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.__do_task = do_task
        self.__running = True
        self.__prepare = prepare
        self.__shutdown = shutdown

    def run(self):
        if self.__prepare:
            self.__prepare()
        while self.__running:
            try:
                task = self.task_queue.get(timeout=1)
                if task == SHUTDOWN_SIGNAL:
                    self.__running = False
                    self.result_queue.put(SHUTDOWN_SIGNAL)
                    continue
                res = self.__do_task(task)
                self.result_queue.put(res)
            except queue.Empty:
                sleep(0.1)
                continue
        if self.__shutdown:
            self.__shutdown()

    def stop(self):
        self.__running = False

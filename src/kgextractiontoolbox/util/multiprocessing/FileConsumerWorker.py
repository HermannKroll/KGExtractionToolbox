import multiprocessing
import queue
from time import sleep

from kgextractiontoolbox.util.multiprocessing.Worker import SHUTDOWN_SIGNAL
from kgextractiontoolbox.util.multiprocessing.WorkerProcess import WorkerProcess


class FileConsumerWorker(WorkerProcess):
    def __init__(self, result_queue: multiprocessing.Queue, out_path: str, no_workers):
        """

        :param result_queue:
        :param consume: Callable, gets result and consumes it
        :param prepare:
        :param shutdown:
        """
        super().__init__()

        self.result_queue = result_queue
        self.__file_name = out_path
        self.__running = True
        self.__no_workers = no_workers

    def run(self):
        shutdown_signal_count = 0

        with open(self.__file_name, "wt") as f:
            while self.__running:
                try:
                    res = self.result_queue.get(timeout=1)
                    if res == SHUTDOWN_SIGNAL:
                        shutdown_signal_count += 1
                        if shutdown_signal_count == self.__no_workers:
                            self.__running = False
                    else:
                        f.write(str(res))
                except queue.Empty:
                    sleep(0.1)
                    continue

    def stop(self):
        self.__running = False

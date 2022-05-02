import sys
from datetime import datetime, timedelta
from time import sleep
from typing import Optional, Callable, List

import multiprocessing
import random


class MultiProcessProgress(multiprocessing.Process):
    """
    This class can be used to log progress to the console. Features include a percentage and eta, if a start time stamp
    and a total number of items are given.
    The workflow looks like this:
    1. create Progress object
    2. call start_time() when starting the processing procedure
    3. call print_progress(index) after having processed each individual item
    4. call done() after having processed all items.
    """

    def __init__(self, total_task_sizes: List[multiprocessing.Value],
                 progress_values: List[multiprocessing.Value],
                 print_every_x_seconds=60,
                 text: str = "Progress",
                 print_fnc: Optional[Callable[[str], None]] = None):
        """
        Create a Progress object
        :param total: total number of items to process
        :type total: int
        :param print_every: update/print progress to terminal every k items
        :type print_every: int
        :param text: The text to be displayed before the progress
        :type text: str
        :param print_fnc: Can be a custom function for printing the progress string
        :type print_fnc: Optional[Callable[[str], None]]
        """
        multiprocessing.Process.__init__(self)
        self.start_time: Optional[datetime] = None
        self.total_task_sizes = total_task_sizes
        self.progress_values = progress_values
        self.print_every_x_seconds = print_every_x_seconds
        if len(total_task_sizes) != len(progress_values):
            raise ValueError('The number of task sizes must be equal to the number of progress values')

        self.text = text
        self.__shutdown: multiprocessing.Value = multiprocessing.Value('i', 0)
        self.__last_progress = None
        self.logging_fkt = print_fnc

    def start(self) -> None:
        """
        Call in order to start the timer
        """
        self.start_time = datetime.now()
        self.__last_progress = datetime.now()
        multiprocessing.Process.start(self)

    def done(self) -> None:
        """
        Call to display a finished message and total runtime
        """

        print_str = f"{self.text}: done"
        self.__shutdown.value = 1
        if self.start_time:
            elapsed_time = (datetime.now() - self.start_time)
            print_str = f"{print_str} in {elapsed_time}"
        else:
            print_str = f"{print_str}!"
        if self.logging_fkt:
            self.logging_fkt(f"{print_str}\n")
        else:
            sys.stdout.write(f"\r{print_str}\n")
            sys.stdout.flush()

    def run(self):
        while self.__shutdown.value == 0:
            elapsed_seconds = (datetime.now() - self.__last_progress).seconds + 1
            if elapsed_seconds > self.print_every_x_seconds:
                self._print_progress()
                self.__last_progress = datetime.now()
            sleep(0.1)

    def _print_progress(self) -> None:
        """
        Call after processing each individual item to update/print progress string
        :param number_of_items_done: How many items have already been processed.
        :type number_of_items_done: int
        """
        print_str = [f"{self.text} ["]
        elapsed_seconds = None
        if self.start_time:
            elapsed_seconds = (datetime.now() - self.start_time).seconds + 1

        progress_sum, total_sum = 0, 0
        for idx, (progress, total) in enumerate(zip(self.progress_values, self.total_task_sizes)):
            if idx > 0:
                print_str.append(' | ')
            percent = 100 * progress.value / total.value
            progress_sum += progress.value
            total_sum += total.value
            print_str.append(f"W{idx}: {percent:.1f}% ({progress.value}/{total.value})")

        if progress_sum == total_sum:
            self.__shutdown.value = 0
        print_str.append(']')

        percent = 100 * progress_sum / total_sum
        if percent and elapsed_seconds:
            sec_per_doc = elapsed_seconds / progress_sum
            remaining_seconds = (total_sum - progress_sum) * sec_per_doc
            eta = (datetime.now() + timedelta(seconds=remaining_seconds))
            print_str.append(f" eta: {eta:%Y-%m-%d %H:%M}")

        print_str = ''.join(print_str)
        if self.logging_fkt:
            self.logging_fkt(print_str)
        else:
            sys.stdout.write(f"\r{print_str}")
            sys.stdout.flush()


if __name__ == '__main__':
    task_size_values = [multiprocessing.Value("i", 10), multiprocessing.Value("i", 10), multiprocessing.Value("i", 10)]
    progress_size_values = [multiprocessing.Value("i", 0), multiprocessing.Value("i", 0), multiprocessing.Value("i", 0)]

    mp_progress = MultiProcessProgress(task_size_values, progress_size_values, print_every_x_seconds=1, text="Working")
    mp_progress.start()

    for i in range(0, 10):
        for j in range(0, 3):
            progress_size_values[j].value += 1
            sleep(0.5)

    mp_progress.done()

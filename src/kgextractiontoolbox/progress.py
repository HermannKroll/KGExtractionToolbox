import logging
import sys
import time
from datetime import datetime, timedelta
from typing import Optional, Callable


class Progress:
    """
    This class can be used to log progress to the console. Features include a percentage and eta, if a start time stamp
    and a total number of items are given.
    The workflow looks like this:
    1. create Progress object
    2. call start_time() when starting the processing procedure
    3. call print_progress(index) after having processed each individual item
    4. call done() after having processed all items.
    """

    def __init__(self, total: int = 0, print_every: int = 0, text: str = "Progress",
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
        self.start: Optional[datetime] = None
        self.total = total
        self.print_every = print_every
        self.text = text
        self.logging_fkt = print_fnc

    def start_time(self) -> None:
        """
        Call in order to start the timer
        """
        self.start = datetime.now()

    def done(self) -> None:
        """
        Call to display a finished message and total runtime
        """
        print_str = f"{self.text}: done"
        if self.start:
            elapsed_time = (datetime.now() - self.start)
            print_str = f"{print_str} in {elapsed_time}"
        else:
            print_str = f"{print_str}!"
        if self.logging_fkt:
            self.logging_fkt(f"{print_str}\n")
        else:
            sys.stdout.write(f"\r{print_str}\n")
            sys.stdout.flush()

    def print_progress(self, number_of_items_done: int) -> None:
        """
        Call after processing each individual item to update/print progress string
        :param number_of_items_done: How many items have already been processed.
        :type number_of_items_done: int
        """
        print_str = f"{self.text}..."
        elapsed_seconds = None
        if self.start:
            elapsed_seconds = (datetime.now() - self.start).seconds + 1
        if self.print_every and number_of_items_done % self.print_every:
            return
        if self.total:
            percent = 100 * number_of_items_done / self.total
            print_str = f"{print_str} {percent:.1f}% done ({number_of_items_done} of {self.total})"
            if percent and elapsed_seconds:
                sec_per_doc = elapsed_seconds / number_of_items_done
                remaining_seconds = (self.total - number_of_items_done) * sec_per_doc
                eta = (datetime.now() + timedelta(seconds=remaining_seconds))
                print_str = f"{print_str} eta: {eta:%Y-%m-%d %H:%M}"
        else:
            print_str = f"{print_str} {number_of_items_done} done"
        if self.logging_fkt:
            self.logging_fkt(print_str)
        else:
            sys.stdout.write(f"\r{print_str}")
            sys.stdout.flush()


def print_progress_with_eta(text, current_idx, size, start_time, print_every_k=1000, logger=None):
    """
    Print progress in percent with an estimated time until the process is done.
    Usually, this function is used when the set of objects to work on is finite.

    :param text: Caption of the task
    :param current_idx: Index of last processed objects. Negative if no object has been processed so far.
    :param size: Total number of objects
    :param start_time: Time of start
    :param print_every_k: Number of objects after which the output should be updated
    :param logger: A logging instance to output progress to
    :return:
    """
    if current_idx % print_every_k == 0:
        if current_idx < 0 or size == 0:
            percentage = 0
            eta = "--"
        else:
            try:
                percentage = (current_idx + 1.0) / size * 100.0
                elapsed_seconds = (datetime.now() - start_time).seconds + 1
                seconds_per_doc = elapsed_seconds / (current_idx + 1.0)
                remaining_seconds = (size - current_idx) * seconds_per_doc
                eta = (datetime.now() + timedelta(seconds=remaining_seconds)).strftime("%Y-%m-%d %H:%M")
            except:
                eta = "--"
        if not logger:
            sys.stdout.write("\r{} ... {:0.1f} % (ETA {})".format(text, percentage, eta))
            sys.stdout.flush()
        else:
            logger.info("{} ... {:0.1f} % (ETA {})".format(text, percentage, eta))


if __name__ == '__main__':
    logging.basicConfig(level="INFO")
    p = Progress(total=5, text="Total...")
    p.start_time()
    p.print_progress(0)
    for n in range(5):
        time.sleep(1)
        p.print_progress(n + 1)
    p.done()
    p = Progress(total=5, text="Total logging info", print_fnc=logging.info)
    p.start_time()
    p.print_progress(0)
    for n in range(5):
        time.sleep(1)
        p.print_progress(n + 1)
    p.done()
    p = Progress(text="without total")
    p.start_time()
    p.print_progress(0)
    for n in range(5):
        time.sleep(1)
        p.print_progress(n + 1)
    p.done()
    p = Progress(text="without time", total=5)
    p.print_progress(0)
    for n in range(5):
        time.sleep(1)
        p.print_progress(n + 1)
    p.done()

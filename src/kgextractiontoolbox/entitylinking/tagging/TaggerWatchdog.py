import logging
import subprocess
from collections.abc import Callable
from time import sleep


class TaggerWatchdog:
    def __init__(self, start_process: Callable[[], subprocess.Popen], get_progress: Callable[[], int],
                 ignore_last_file: Callable[[]], logger=logging):
        self.start_process = start_process
        self.get_progress = get_progress
        self.ignore_last_file: ignore_last_file
        self.logger = logger
        self.output_intervall = 30

    def run(self):
        keep_tagging = True
        while keep_tagging:
            process = self.start_process()
            self.logger.info(f"Starting {process.args}")
            old_progress = 0;
            while process.poll() is None:
                sleep(self.output_intervall)
                new_progress = self.get_progress()
                if new_progress > old_progress:
                    la

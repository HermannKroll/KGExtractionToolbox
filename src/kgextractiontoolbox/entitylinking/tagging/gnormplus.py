import os
import re
import signal
import subprocess
from datetime import datetime
from shutil import copyfile
from time import sleep

from kgextractiontoolbox.document.count import get_document_ids
from kgextractiontoolbox.entitylinking.tagging.external_base import ExternalTaggerBase
from kgextractiontoolbox.entitylinking.utils import get_document_id
from kgextractiontoolbox.progress import print_progress_with_eta


class GNormPlus(ExternalTaggerBase):
    TYPES = ("Gene", "Species")
    __name__ = "GNormPlus"
    __version__ = "unknown"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.out_dir = os.path.join(self.root_dir, "gnorm_out")
        self.log_file = os.path.join(self.log_dir, "gnorm.log")
        self.__last_print_by_x_percent = 0

    # TODO: Test if function works
    def get_exception_causing_file_from_log(self):
        with open(self.log_file) as f_log:
            content = f_log.read()
        processed_files = re.findall(r"/.*?\d+\.txt", content)
        if processed_files:
            last_file = processed_files[-1]
            return last_file
        else:
            return None

    def prepare(self, ):
        """
        Creates the GNormPlus output directory
        :return:
        """
        os.mkdir(self.out_dir)

    def get_tags(self):
        return self._get_tags(self.out_dir)

    def _delete_tagged_files_in_input(self):
        """
        Delete all already tagged input files for GNormPlus
        :return: the set of document ids to process
        """
        self.logger.info("Cleaning up GNormPlus input directory for the next run...")
        tagged_ids = self.get_successful_ids()
        to_process, removed_ids = set(), set()
        for fn in os.listdir(self.input_dir):
            fn = os.path.join(self.input_dir, fn)
            if fn.endswith('.txt'):
                document_id = get_document_id(fn)
                if document_id in tagged_ids:
                    os.remove(fn)
                    removed_ids.add(document_id)
                else:
                    to_process.add(document_id)
        self.logger.info(f'{len(removed_ids)} documents have been removed from input (already tagged)')
        return to_process

    def run(self):
        """
        Method starts a GNormPlus instance with all files from ``in_dir`` and writes the result back to ``out_dir``.
        Log files are written into the directory ``log_dir``.

        If an error occurs during the execution of GNormPlus, the exit code is evaluated. If it's 1 the last processed
        file is removed and the instance is going to be restarted. If no file was processed the thread is cancelled and
        a manual analysis is recommended (maybe an OutOfMemoryException?).
        """
        skipped_files = []
        keep_tagging = True
        files_total = len(os.listdir(self.input_dir))
        start_time = datetime.now()
        no_progress = False

        last_progress_timestamp = datetime.now()
        run = 0
        while keep_tagging:
            old_progress = 0
            if run > 0:
                ids_to_process = self._delete_tagged_files_in_input()
                # stop the process if there are no files to continue
                if len(ids_to_process) == 0:
                    self.logger.info('No files to process - stopping GNormPlus worker')
                    keep_tagging = False
                    continue
            run += 1
            with open(self.log_file, "w") as f_log:
                # Start GNormPlus
                sp_args = ["java", *self.config.gnorm_java_args, "-jar", self.config.gnorm_jar, self.input_dir,
                           self.out_dir, self.config.gnorm_setup]
                process = subprocess.Popen(sp_args, cwd=self.config.gnorm_root, stdout=f_log, stderr=f_log)
                self.logger.debug("Starting {}".format(process.args))

                # Wait until finished
                while process.poll() is None:
                    sleep(self.OUTPUT_INTERVAL)

                    new_progress = self.get_progress()
                    self.progress_value.value = new_progress
                    # print every 10%
                    if new_progress / len(self.files) > self.__last_print_by_x_percent:
                        print_progress_with_eta("GNormPlus tagging", new_progress, files_total, start_time,
                                                print_every_k=1, logger=self.logger)
                        self.__last_print_by_x_percent += 0.1
                    if new_progress > old_progress:
                        last_progress_timestamp = datetime.now()
                        old_progress = new_progress
                    elif (datetime.now() - last_progress_timestamp).total_seconds() \
                            > 60 * self.config.gnormplus_timeout:
                        os.kill(process.pid, signal.SIGKILL)
                        while process.poll() is None:
                            sleep(1)
                        self.logger.warn(f"No Progress in last {self.config.gnormplus_timeout} min")
                        no_progress = True
                        break
                self.logger.debug("Exited with code {}".format(process.poll()))

            if not process.poll() == 0 or no_progress:
                # Java Exception
                last_file = self.get_exception_causing_file_from_log()
                if last_file:
                    last_file_path = os.path.join(self.input_dir, last_file)
                    last_id = get_document_id(last_file_path)
                    skipped_files.append(last_file)
                    self.logger.debug("Exception in file {}".format(last_file))
                    try:
                        copyfile(self.log_file, os.path.join(os.path.dirname(self.log_file), f"gnorm.{last_id}.log"))
                    except:
                        self.logger.warn("Could not conserve logfile, continuing anyway")
                    self.logger.warning(f'No progress / exception. Deleting problematic file: {last_file}')
                    os.remove(last_file)
                # if there is no progress and we did not find a last file, we have to stop the process
                elif no_progress:
                    # No file processed, assume another error
                    keep_tagging = False
                    self.logger.error("No files processed. Assuming an unexpected exception.")
                    self.logger.error("GNormPlus exited with code {}".format(process.poll()))
                no_progress = False
            else:
                keep_tagging = False

        end_time = datetime.now()
        # print one time at the end
        new_progress = self.get_progress()
        print_progress_with_eta("GNormPlus tagging", new_progress, files_total, start_time,
                                print_every_k=1, logger=self.logger)
        self.logger.info("Finished in {} ({} files processed, {} files total, {} errors)".format(
            end_time - start_time,
            new_progress,
            files_total,
            len(skipped_files)))

    def get_progress(self):
        return len([f for f in os.listdir(self.out_dir) if f.endswith(".txt")])

    def get_successful_ids(self):
        processed_ids = set()
        # also include all logged ids
        with open(self.log_file) as f_log:
            content = f_log.read()
        processed_files = re.findall(r"(\d+)(\.txt)", content)
        for pf in processed_files:
            processed_ids.add(int(pf[0]))
        # get processed ids
        processed_ids.union(get_document_ids(self.out_dir))
        return processed_ids

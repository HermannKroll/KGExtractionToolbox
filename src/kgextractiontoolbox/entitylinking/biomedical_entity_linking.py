import datetime as dti
import logging
import multiprocessing
import os
import shutil
import signal
import sys
import tempfile
from argparse import ArgumentParser
from typing import List, Set

import psutil

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import DocTaggedBy
from kgextractiontoolbox.config import ENTITY_LINKING_CONFIG
from kgextractiontoolbox.document.distribute import distribute_workload, create_parallel_dirs, split_composites
from kgextractiontoolbox.document.extract import collect_ids_from_dir
from kgextractiontoolbox.document.load_document import document_bulk_load
from kgextractiontoolbox.document.sanitize import sanitize
from kgextractiontoolbox.entitylinking.entity_linking_config import Config
from kgextractiontoolbox.entitylinking.tagging.base import BaseTagger
from kgextractiontoolbox.entitylinking.tagging.gnormplus import GNormPlus
from kgextractiontoolbox.entitylinking.tagging.taggerone import TaggerOne
from kgextractiontoolbox.entitylinking.utils import get_untagged_doc_ids_by_ent_type, init_preprocess_logger, \
    init_sqlalchemy_logger
from kgextractiontoolbox.multi_process_progress import MultiProcessProgress


def get_tagger_by_ent_type(tag_types):
    tagger_by_ent_type = {}

    if "Gene" in tag_types and "Species" in tag_types:
        tagger_by_ent_type["Gene"] = GNormPlus
        tagger_by_ent_type["Species"] = GNormPlus
    if ("Gene" in tag_types) != ("Species" in tag_types):
        raise ValueError("GNormPlus does not support tagging of Species and Genes separately")
    if "Chemical" in tag_types and "Disease" in tag_types:
        tagger_by_ent_type["Chemical"] = TaggerOne
        tagger_by_ent_type["Disease"] = TaggerOne
    if ("Chemical" in tag_types) != ("Disease" in tag_types):
        raise ValueError("TaggerOne does not support Tagging of Chemicals or Diseases separately!")

    return tagger_by_ent_type


def get_untagged_doc_ids_by_tagger(collection, target_ids, tagger_cls, logger):
    session = Session.get()
    result = session.query(DocTaggedBy.document_id).filter(
        DocTaggedBy.document_collection == collection,
        DocTaggedBy.tagger_name == tagger_cls.__name__,
        DocTaggedBy.tagger_version == tagger_cls.__version__,
    ).distinct()
    present_ids = set(x[0] for x in result)
    logger.debug(
        "Retrieved {} ids (collection={},tagger={}/{})".format(
            len(present_ids), collection, tagger_cls.__name__, tagger_cls.__version__
        ))
    missing_ids = target_ids.difference(present_ids)
    return missing_ids


def compute_tagging_task_list(input_dir, collection, root_dir, logger, tag_types: Set[str]):
    """
    Computes the list of files to process. Files that have already been processed will be retrieved from
    the database
    :param input_dir: an input dir / file
    :param collection: the corresponding document collection
    :param root_dir: the rootdir (task list will be written to this root dir)
    :param logger: the logger instance
    :param tag_types: a set of tag types
    :return: a set of all document ids, a dict that maps a tag type to a set of files
    """
    logger.info("=== STEP 1 - Preparation ===")
    tag_type_2_missingfiles = dict()

    # Get tagger classes
    tagger_by_ent_type = get_tagger_by_ent_type(tag_types)

    # Gather target IDs
    target_ids, mapping_file_id, mapping_id_file = collect_ids_from_dir(input_dir, logger)
    logger.info("Checking {} documents against the database...".format(len(target_ids)))

    # Get input documents for each tagger
    all_missing_ids = set()
    for tag_type in tag_types:
        tagger_cls = tagger_by_ent_type[tag_type]
        missing_ids = get_untagged_doc_ids_by_ent_type(collection, target_ids, tag_type, tagger_cls, logger)
        all_missing_ids.update(missing_ids)
        tag_type_2_missingfiles[tag_type] = frozenset(mapping_id_file[x] for x in missing_ids)
        task_list_fn = os.path.join(root_dir, "tasklist_{}.txt".format(tag_type.lower()))
        with open(task_list_fn, "w") as f:
            f.write("\n".join(tag_type_2_missingfiles[tag_type]))
        logger.debug("Tasklist for {} written to: {}".format(tag_type, task_list_fn))
        logger.info("Tasklist for {} contains {} documents".format(tag_type, len(missing_ids)))
    return all_missing_ids, tag_type_2_missingfiles


def preprocess(files_to_process, collection, root_dir, input_dir, log_dir, logger, conf, progress_value,
               tag_types: Set[str]):
    # Get tagger classes
    tagger_by_ent_type = get_tagger_by_ent_type(tag_types)
    # Init taggers
    kwargs = dict(collection=collection, root_dir=root_dir, input_dir=input_dir, logger=logger,
                  log_dir=log_dir, config=conf)
    taggers: List[BaseTagger] = [tagger_cls(**kwargs) for tagger_cls in set(tagger_by_ent_type.values())]
    if len(taggers) > 1:
        raise ValueError("We only support a single tagger for a process")

    tagger = taggers[0]
    tagger.set_multiprocess_progress_value(progress_value)

    if len(files_to_process) > 0:
        tagger.base_insert_tagger()
        start = dti.datetime.now()
        logger.info("Preparing {}".format(tagger.name))
        tagger.add_files(files_to_process)
        tagger.prepare()
        preptime = dti.datetime.now() - start
        logger.info(f"{tagger.name} used {preptime} for preparation")

        logger.info("=== STEP 2 - Tagging ===")
        logger.info("Starting {}".format(tagger.name))
        tagger.start()
        tagger.join()

        logger.info("=== STEP 3 - Post-processing ===")
        logger.info("Finalizing {}".format(tagger.name))
        tagger.finalize()
    else:
        logger.info('No files need to be annotated - finished')
    logger.info("=== Finished ===")


def run_preprocess(input_file, collection, config, skip_load, tagger_one, gnormplus, loglevel=logging.INFO,
                   workdir=None, workers=1):
    # Create configuration wrapper
    conf = Config(config)
    # Prepare directories and logging
    root_dir = os.path.abspath(workdir) if workdir else tempfile.mkdtemp()
    ext_in_dir = input_file
    in_dir = os.path.join(root_dir, "input")
    log_dir = os.path.abspath(os.path.join(root_dir, "log"))
    if not os.path.exists(root_dir):
        os.makedirs(root_dir)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    if not os.path.exists(in_dir):
        os.makedirs(in_dir)
    logger = init_preprocess_logger(os.path.join(log_dir, "preprocessing.log"), loglevel)
    init_sqlalchemy_logger(os.path.join(log_dir, "sqlalchemy.log"), loglevel)
    logger.info("Project directory: {}".format(root_dir))
    logger.debug("Input directory: {}".format(in_dir))
    if not os.path.exists(in_dir):
        logger.error("Fatal: Input directory or file not found")
        sys.exit(1)

    logger.info(f"Splitting up composite files to: {in_dir}...")
    split_composites(ext_in_dir, in_dir, logger=logger)
    logger.info("done. Sanitizing files...")
    ignored, sanitized = sanitize(in_dir, delete_mismatched=True)
    logger.info(f"{len(ignored)} files ignored because of wrong format or missing abstract")
    logger.info(f"{len(sanitized)} files sanitized")
    # Add documents to database
    if skip_load:
        logger.info("Skipping bulk load")
    else:
        document_bulk_load(in_dir, collection, logger=logger)
    # Create list of tagging ent types
    tag_types = set()
    if tagger_one:
        tag_types.add("Chemical")
        tag_types.add("Disease")
    if gnormplus:
        tag_types.add("Species")
        tag_types.add("Gene")

    # compute task list
    all_missing_ids, type2files = compute_tagging_task_list(in_dir, collection, root_dir, logger=logger,
                                                            tag_types=tag_types)

    # files to process
    files_to_process = set()
    for tag_type in tag_types:
        files_to_process.update(type2files[tag_type])

    # delete all files that do not be processed
    logger.info('Removing files that do not need to be processed...')
    for fn in os.listdir(in_dir):
        fn = os.path.join(in_dir, fn)
        if os.path.isfile(fn) and fn not in files_to_process:
            os.remove(fn)

    # Run actual preprocessing
    if workers > 1:
        # Otherwise the session created above will be inherits to the forked processes
        session = Session.get()
        session.remove()

        logger.info('Splitting up workload for multiple threads')
        worker2files = distribute_workload(in_dir, os.path.join(root_dir, "inputDirs"), int(workers))
        create_parallel_dirs(root_dir, int(workers), "worker")
        create_parallel_dirs(log_dir, int(workers), "worker")
        processes = []
        output_paths = []

        task_size_values = list([multiprocessing.Value("i", 0) for n in range(int(workers))])
        progress_values = list([multiprocessing.Value("i", 0) for n in range(int(workers))])
        mp_progress = MultiProcessProgress(task_size_values, progress_values, print_every_x_seconds=5,
                                           text="Tagging...")

        for n in range(int(workers)):
            sub_in_dir = os.path.join(root_dir, "inputDirs", f"batch{n}")
            sub_root_dir = os.path.join(root_dir, f"worker{n}")
            sub_log_dir = os.path.join(log_dir, f"worker{n}")
            sub_logger = init_preprocess_logger(
                os.path.join(sub_log_dir, "preprocessing.log"),
                loglevel,
                worker_id=n,
                log_format='%(asctime)s %(levelname)s %(name)s %(module)s:%(lineno)d %(message)s')
            sub_logger.propagate = False
            sub_output = os.path.join(sub_root_dir, "output.txt")
            output_paths.append(sub_output)
            task_size_values[n].value = len(worker2files[n])
            process_kwargs = dict(
                files_to_process=worker2files[n], collection=collection, root_dir=sub_root_dir,
                input_dir=sub_in_dir, log_dir=sub_log_dir, logger=sub_logger,
                conf=conf, progress_value=progress_values[n], tag_types=tag_types
            )
            process = multiprocessing.Process(target=preprocess, kwargs=process_kwargs)
            processes.append(process)
            process.start()

        mp_progress.start()
        signal.signal(signal.SIGINT, int_handler)
        for process in processes:
            while process.is_alive():
                process.join(timeout=1)
        mp_progress.done()
        while mp_progress.is_alive():
            mp_progress.join(timeout=1)
    else:
        task_size = multiprocessing.Value("i", 0)
        task_size.value = len(files_to_process)
        progress_value = multiprocessing.Value("i", 0)
        mp_progress = MultiProcessProgress([task_size], [progress_value], print_every_x_seconds=5, text="Tagging...")
        mp_progress.start()
        preprocess(files_to_process=files_to_process, collection=collection, root_dir=root_dir, input_dir=in_dir,
                   log_dir=log_dir, logger=logger, conf=conf, progress_value=progress_value, tag_types=tag_types)
        mp_progress.done()
        while mp_progress.is_alive():
            mp_progress.join(timeout=1)
    if not workdir:
        logger.info("Done. Deleting tmp project directory.")
        shutil.rmtree(root_dir)


def main(arguments=None):
    parser = ArgumentParser(description="Tag given documents in pubtator format and insert tags into database")
    parser.add_argument("-c", "--collection", required=True)
    parser.add_argument("--tagger-one", action="store_true",
                        help='Enables Tagging of "Chemicals and "Diseases with TaggerOne')
    parser.add_argument("--gnormplus", action="store_true", help="Enables Tagging of Genes and Species with GNormPlus")
    group_settings = parser.add_argument_group("Settings")
    group_settings.add_argument("--config", default=ENTITY_LINKING_CONFIG,
                                help="Configuration file (default: {})".format(ENTITY_LINKING_CONFIG))
    group_settings.add_argument("--loglevel", default="INFO")
    group_settings.add_argument("--workdir", default=None)
    group_settings.add_argument("--skip-load", action='store_true',
                                help="Skip bulk load of documents on start (expert setting)")
    group_settings.add_argument("-w", "--workers", default=1, help="Number of processes for parallelized preprocessing",
                                type=int)

    parser.add_argument("input", help="Directory with PubTator files / PubTator file ", metavar="IN_DIR")
    args = parser.parse_args(arguments)

    if not args.tagger_one and not args.gnormplus:
        print("At least --tagger-one or --gnormplus must be specified for tagging")
        sys.exit(1)

    if args.tagger_one and args.gnormplus:
        print("Choose only one tagger - Pipeline does not support both taggers in parallel")
        sys.exit(1)

    run_preprocess(input_file=args.input, collection=args.collection, config=args.config,
                   skip_load=args.skip_load, tagger_one=args.tagger_one, gnormplus=args.gnormplus,
                   loglevel=args.loglevel.upper(), workdir=args.workdir, workers=args.workers)


def int_handler(sig, frame):
    print("Interrupt: received control-c")
    process = psutil.Process(os.getpid())
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()


if __name__ == "__main__":
    main()

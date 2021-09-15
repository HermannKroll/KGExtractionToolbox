import datetime as dti
import multiprocessing
import os
import psutil
import shutil
import signal
import sys
import tempfile
from argparse import ArgumentParser
from typing import List

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import DocTaggedBy
from kgextractiontoolbox.config import ENTITY_LINKING_CONFIG
from kgextractiontoolbox.document.distribute import distribute_workload, create_parallel_dirs, split_composites
from kgextractiontoolbox.document.extract import collect_ids_from_dir
from kgextractiontoolbox.document.load_document import document_bulk_load
from kgextractiontoolbox.document.sanitize import sanitize
from kgextractiontoolbox.entitylinking.entity_linking_config import Config
from kgextractiontoolbox.entitylinking.export_annotations import export
from kgextractiontoolbox.entitylinking.tagging.base import BaseTagger
from kgextractiontoolbox.entitylinking.tagging.gnormplus import GNormPlus
from kgextractiontoolbox.entitylinking.tagging.taggerone import TaggerOne
from kgextractiontoolbox.entitylinking.utils import get_untagged_doc_ids_by_ent_type, init_preprocess_logger, \
    init_sqlalchemy_logger


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
    result = session.query(DocTaggedBy).filter(
        DocTaggedBy.document_collection == collection,
        DocTaggedBy.tagger_name == tagger_cls.__name__,
        DocTaggedBy.tagger_version == tagger_cls.__version__,
    ).values(DocTaggedBy.document_id)
    present_ids = set(x[0] for x in result)
    logger.debug(
        "Retrieved {} ids (collection={},tagger={}/{})".format(
            len(present_ids), collection, tagger_cls.__name__, tagger_cls.__version__
        ))
    missing_ids = target_ids.difference(present_ids)
    return missing_ids


def preprocess(collection, root_dir, input_dir, log_dir, logger, output_filename, conf, *tag_types):
    """
    Method creates a single PubTator file with the documents from in ``in_dir`` and its tags.

    :param logger: Logger instance
    :param log_dir: Directory for logs
    :param root_dir: Root directory (i.e., working directory)
    :param input_dir: Input directory containing PubTator files to tag
    :param collection: Collection ID (e.g., PMC)
    :param output_filename: Filename of PubTator to create
    :param conf: config object
    be set accordingly)
    """
    logger.info("=== STEP 1 - Preparation ===")
    target_ids = set()
    mapping_id_file = dict()
    mapping_file_id = dict()
    missing_files_type = dict()

    # Get tagger classes
    tagger_by_ent_type = get_tagger_by_ent_type(tag_types)

    # Gather target IDs
    target_ids, mapping_file_id, mapping_id_file = collect_ids_from_dir(input_dir, logger)
    logger.info("Preprocessing {} documents".format(len(target_ids)))

    # Get input documents for each tagger
    all_missing_ids = set()
    for tag_type in tag_types:
        tagger_cls = tagger_by_ent_type[tag_type]
        missing_ids = get_untagged_doc_ids_by_ent_type(collection, target_ids, tag_type, tagger_cls, logger)
        all_missing_ids.update(missing_ids)
        missing_files_type[tag_type] = frozenset(mapping_id_file[x] for x in missing_ids)
        task_list_fn = os.path.join(root_dir, "tasklist_{}.txt".format(tag_type.lower()))
        with open(task_list_fn, "w") as f:
            f.write("\n".join(missing_files_type[tag_type]))
        logger.debug("Tasklist for {} written to: {}".format(tag_type, task_list_fn))
        logger.info("Tasklist for {} contains {} documents".format(tag_type, len(missing_ids)))

    # Init taggers
    kwargs = dict(collection=collection, root_dir=root_dir, input_dir=input_dir, logger=logger,
                  log_dir=log_dir, config=conf, mapping_id_file=mapping_id_file, mapping_file_id=mapping_file_id)
    taggers: List[BaseTagger] = [tagger_cls(**kwargs) for tagger_cls in set(tagger_by_ent_type.values())]

    for tagger in taggers:
        tagger.base_insert_tagger()
        start = dti.datetime.now()
        logger.info("Preparing {}".format(tagger.name))
        for target_type in tagger.get_types():
            tagger.add_files(*missing_files_type[target_type])
        tagger.prepare()
        preptime = dti.datetime.now() - start
        logger.info(f"{tagger.name} used {preptime} for preparation")
    if len(all_missing_ids) > 0:
        logger.info("=== STEP 2 - Tagging ===")
        for tagger in taggers:
            logger.info("Starting {}".format(tagger.name))
            tagger.start()
        for tagger in taggers:
            tagger.join()
    else:
        logger.info('No files need to be annotated - finished')
    logger.info("=== STEP 3 - Post-processing ===")
    for tagger in taggers:
        logger.info("Finalizing {}".format(tagger.name))
        tagger.finalize()
    if output_filename:
        export(output_filename, tag_types, target_ids, collection=collection, content=True, logger=logger)
    logger.info("=== Finished ===")


def main(arguments=None):
    parser = ArgumentParser(description="Perform entity linking on the given input using TaggerOne and/or GNormPlus")

    parser.add_argument("--composite", action="store_true", default=True,
                        help="Check for composite document files in input. Enabled by default.")

    parser.add_argument("-c", "--collection", required=True)
    parser.add_argument("--tagger-one", action="store_true",
                        help='Enables Tagging of Chemicals and Diseases with TaggerOne')
    parser.add_argument("--gnormplus", action="store_true", help="Enables Tagging of Genes and Species with GNormPlus")

    group_settings = parser.add_argument_group("Settings")
    group_settings.add_argument("--config", default=ENTITY_LINKING_CONFIG,
                                help="Configuration file (default: {})".format(ENTITY_LINKING_CONFIG))
    group_settings.add_argument("--loglevel", default="INFO")
    group_settings.add_argument("--workdir", default=None)
    group_settings.add_argument("--skip-load", action='store_true',
                                help="Skip bulk load of documents on start (expert setting)")
    group_settings.add_argument("-w", "--workers", default=1,
                                help="Number of processes for parallelized entity linking",
                                type=int)

    parser.add_argument("input", help="Directory with input files ")
    parser.add_argument("-o", "--output", help="export the tags in pubtator format after tagging")
    args = parser.parse_args(arguments)

    if not args.tagger_one and not args.gnormplus:
        print("At least --tagger-one or --gnormplus must be specified for tagging")
        sys.exit(1)

    # Create configuration wrapper
    conf = Config(args.config)

    # Prepare directories and logging
    root_dir = os.path.abspath(args.workdir) if args.workdir else tempfile.mkdtemp()
    ext_in_dir = args.input
    in_dir = os.path.join(root_dir, "input")
    log_dir = os.path.abspath(os.path.join(root_dir, "log"))
    if not os.path.exists(root_dir):
        os.makedirs(root_dir)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    if not os.path.exists(in_dir):
        os.makedirs(in_dir)
    logger = init_preprocess_logger(os.path.join(log_dir, "entitylinking.log"), args.loglevel.upper())

    init_sqlalchemy_logger(os.path.join(log_dir, "sqlalchemy.log"), args.loglevel.upper())
    logger.info("Project directory: {}".format(root_dir))
    logger.debug("Input directory: {}".format(in_dir))
    if not os.path.exists(in_dir):
        logger.error("Fatal: Input directory or file not found")
        sys.exit(1)

    if args.composite or os.path.isfile(ext_in_dir):
        logger.debug(f"Composite of single input file: created input directory at {in_dir}")
        logger.info(f"Composite enabled or single file as input. Splitting up composite files...")
        split_composites(ext_in_dir, in_dir, logger=logger)
        logger.info("done. Sanitizing files...")
        ignored, sanitized = sanitize(in_dir, delete_mismatched=True)
    else:
        ignored, sanitized = sanitize(ext_in_dir, output_dir=in_dir)
    logger.info(f"{len(ignored)} files ignored because of wrong format or missing abstract")
    logger.info(f"{len(sanitized)} files sanitized")

    # Add documents to database
    if args.skip_load:
        logger.info("Skipping bulk load")
    else:
        document_bulk_load(in_dir, args.collection, logger=logger)
    # Create list of tagging ent types

    tag_types = set()
    if args.tagger_one:
        tag_types.add("Chemical")
        tag_types.add("Disease")
    if args.gnormplus:
        tag_types.add("Species")
        tag_types.add("Gene")

    # Run actual entitylinking
    if args.workers > 1:
        logger.info('splitting up workload for multiple threads')
        distribute_workload(in_dir, os.path.join(root_dir, "inputDirs"), int(args.workers))
        create_parallel_dirs(root_dir, int(args.workers), "worker")
        create_parallel_dirs(log_dir, int(args.workers), "worker")
        processes = []
        output_paths = []
        for n in range(int(args.workers)):
            sub_in_dir = os.path.join(root_dir, "inputDirs", f"batch{n}")
            sub_root_dir = os.path.join(root_dir, f"worker{n}")
            sub_log_dir = os.path.join(log_dir, f"worker{n}")
            sub_logger = init_preprocess_logger(
                os.path.join(sub_log_dir, "entitylinking.log"),
                args.loglevel.upper(),
                worker_id=n,
                log_format='%(asctime)s %(levelname)s %(name)s %(module)s:%(lineno)d %(message)s')
            sub_logger.propagate = False
            sub_output = os.path.join(sub_root_dir, "output.txt")
            output_paths.append(sub_output)
            process_args = (
                args.collection, sub_root_dir, sub_in_dir, sub_log_dir, sub_logger,
                sub_output, conf, *tag_types
            )
            process = multiprocessing.Process(target=preprocess, args=process_args, kwargs=dict())
            processes.append(process)
            process.start()

        signal.signal(signal.SIGINT, int_handler)
        for process in processes:
            while process.is_alive():
                process.join(timeout=1)
        # merge output files
        if args.output:
            logger.info(f"merging sub output files to {args.output}")
            with open(args.output, "w+") as output_file:
                for sub_out_path in output_paths:
                    with open(sub_out_path) as sub_out_file:
                        for line in sub_out_file:
                            output_file.write(line)
                    os.remove(sub_out_path)
    else:
        preprocess(args.collection, root_dir, in_dir, log_dir, logger, args.output, conf, *tag_types)

    if not args.workdir:
        logger.info("Done. Deleting tmp project directory.")
        shutil.rmtree(root_dir)


def int_handler(sig, frame):
    print("Interrupt: received control-c")
    process = psutil.Process(os.getpid())
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()


if __name__ == "__main__":
    main()

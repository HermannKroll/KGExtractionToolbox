import multiprocessing
import os
import shutil
import tempfile
from argparse import ArgumentParser
from datetime import datetime
from typing import List

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.config import ENTITY_LINKING_CONFIG
from kgextractiontoolbox.document import count
from kgextractiontoolbox.document.document import TaggedDocument
from kgextractiontoolbox.document.extract import read_pubtator_documents
from kgextractiontoolbox.document.load_document import document_bulk_load
from kgextractiontoolbox.entitylinking.biomedical_entity_linking import get_untagged_doc_ids_by_tagger
from kgextractiontoolbox.entitylinking.entity_linking_config import Config
from kgextractiontoolbox.entitylinking.tagging.stanza import StanzaTagger
from kgextractiontoolbox.entitylinking.utils import init_preprocess_logger, init_sqlalchemy_logger
from kgextractiontoolbox.progress import print_progress_with_eta
from kgextractiontoolbox.util.multiprocessing.ConsumerWorker import ConsumerWorker
from kgextractiontoolbox.util.multiprocessing.ProducerWorker import ProducerWorker
from kgextractiontoolbox.util.multiprocessing.Worker import Worker


def main(arguments=None):
    parser = ArgumentParser(description="Tag given documents in document format and insert tags into database")
    parser.add_argument("-c", "--collection", required=True)
    group_settings = parser.add_argument_group("Settings")
    group_settings.add_argument("--config", default=ENTITY_LINKING_CONFIG,
                                help="Configuration file (default: {})".format(ENTITY_LINKING_CONFIG))
    group_settings.add_argument("--loglevel", default="INFO")
    group_settings.add_argument("--workdir", default=None)
    group_settings.add_argument("--skip-load", action='store_true',
                                help="Skip bulk load of documents on start (expert setting)")
    parser.add_argument("-y", "--yes_force", help="skip prompt for workdir deletion", action="store_true")
    parser.add_argument("--cpu", help="forces Stanza to run on CPU only (GPU is used by default)", default=False,
                        action="store_true")
    parser.add_argument("--sections", action="store_true", default=False,
                        help="Should the section texts be considered when tagging?")
    parser.add_argument("input", help="composite document file")
    args = parser.parse_args(arguments)

    conf = Config(args.config)

    # create directories
    root_dir = root_dir = os.path.abspath(args.workdir) if args.workdir else tempfile.mkdtemp()
    log_dir = log_dir = os.path.abspath(os.path.join(root_dir, "log"))
    in_file = args.input

    if args.workdir and os.path.exists(root_dir):
        if not args.yes_force:
            print(f"{root_dir} already exists, continue and delete?")
            resp = input("y/n")
            if resp not in {"y", "Y", "j", "J", "yes", "Yes"}:
                print("aborted")
                exit(0)
        else:
            shutil.rmtree(root_dir)
        # only create root dir if workdir is set
        os.makedirs(root_dir)
    # logdir must be created in both cases
    os.makedirs(log_dir)

    # create loggers
    logger = init_preprocess_logger(os.path.join(log_dir, "entitylinking.log"), args.loglevel.upper())
    init_sqlalchemy_logger(os.path.join(log_dir, "sqlalchemy.log"), args.loglevel.upper())
    logger.info(f"Project directory:{root_dir}")

    logger.info("Counting document ids...")
    in_ids = count.get_document_ids(in_file)
    logger.info(f"{len(in_ids)} given, checking against database...")
    document_ids = set()
    document_ids |= get_untagged_doc_ids_by_tagger(args.collection, in_ids, StanzaTagger, logger)
    number_of_docs = len(document_ids)

    if not args.skip_load:
        document_bulk_load(in_file, args.collection, logger=logger)
    else:
        logger.info("Skipping bulk load")

    kwargs = dict(collection=args.collection, root_dir=root_dir, input_dir=None, logger=logger,
                  log_dir=log_dir, config=conf, mapping_id_file=None, mapping_file_id=None)

    stanza_tagger = StanzaTagger(**kwargs)
    stanza_tagger.base_insert_tagger()
    batch_size = conf.stanza_document_batch_size

    consider_sections = args.sections
    logger.info(f'Consider sections: {consider_sections}')

    def generate_tasks():
        document_batch = []
        for doc in read_pubtator_documents(in_file):
            t_doc = TaggedDocument(doc, ignore_tags=True)
            if t_doc and t_doc.id in document_ids and t_doc.has_content():
                document_batch.append(t_doc)
            if len(document_batch) > batch_size:
                yield document_batch.copy()
                document_batch.clear()
        if len(document_batch) > 0:
            yield document_batch.copy()
            document_batch.clear()

    def init_stanza():
        stanza_tagger.prepare(use_gpu=not args.cpu)

    def do_task(in_docs: List[TaggedDocument]):
        tagged_docs = stanza_tagger.tag_document_batch(in_docs, sections=consider_sections)
        for tagged_doc in tagged_docs:
            tagged_doc.clean_tags()
        return tagged_docs

    docs_done = multiprocessing.Value('i', 0)
    docs_to_do = multiprocessing.Value('i', number_of_docs)
    start = datetime.now()

    def consume_task(out_docs: List[TaggedDocument]):
        docs_done.value += len(out_docs)
        print_progress_with_eta("Tagging...", docs_done.value, docs_to_do.value, start, print_every_k=1,
                                logger=logger)
        for out_doc in out_docs:
            if out_doc.tags:
                stanza_tagger.base_insert_tags(out_doc, auto_commit=False)

        if docs_done.value % 10000 == 0:
            Session.get().commit()

    def shutdown_consumer():
        Session.get().commit()

    task_queue = multiprocessing.Queue()
    result_queue = multiprocessing.Queue()
    # TODO: log does not work
    producer = ProducerWorker(task_queue, generate_tasks, 1)
    workers = [Worker(task_queue, result_queue, do_task, prepare=init_stanza)]
    consumer = ConsumerWorker(result_queue, consume_task, 1, shutdown=shutdown_consumer)

    producer.start()
    for w in workers:
        w.start()
    consumer.start()
    consumer.join()
    logger.info(f"finished in {(datetime.now() - start).total_seconds()} seconds")

    if not args.workdir:
        logger.info(f'Remove temp directory: {root_dir}')
        shutil.rmtree(root_dir)


if __name__ == '__main__':
    main()

import logging
import multiprocessing
import os
import shutil
import tempfile
from argparse import ArgumentParser
from datetime import datetime
from typing import List, Set

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import BULK_INSERT_AFTER_K, Document, DocTaggedBy
from kgextractiontoolbox.backend.retrieve import iterate_over_all_documents_in_collection
from kgextractiontoolbox.config import ENTITY_LINKING_CONFIG
from kgextractiontoolbox.document import count
from kgextractiontoolbox.document.document import TaggedDocument, TaggedEntity
from kgextractiontoolbox.document.extract import read_tagged_documents
from kgextractiontoolbox.document.load_document import document_bulk_load
from kgextractiontoolbox.entitylinking.entity_linking_config import Config
from kgextractiontoolbox.entitylinking.tagging.metadictagger import MetaDicTagger
from kgextractiontoolbox.entitylinking.tagging.vocabulary import Vocabulary
from kgextractiontoolbox.entitylinking.utils import get_untagged_doc_ids_by_ent_type, init_preprocess_logger, \
    init_sqlalchemy_logger
from kgextractiontoolbox.progress import Progress
from kgextractiontoolbox.util.multiprocessing.ConsumerWorker import ConsumerWorker
from kgextractiontoolbox.util.multiprocessing.ProducerWorker import ProducerWorker
from kgextractiontoolbox.util.multiprocessing.Worker import Worker


def find_untagged_ids(in_file: str, logger: logging.Logger,
                      collection: str, ent_types, skip_todo_check=False) -> Set[int]:
    if not os.path.exists(in_file):
        logger.error("Input file not found!")
        return {}
    logger.info("Counting document ids...")
    in_ids = count.get_document_ids(in_file)
    logger.info(f"{len(in_ids)} given")
    todo_ids = set()
    if skip_todo_check:
        todo_ids = in_ids
    else:
        logger.info(f"Checking against database...")
        for ent_type in ent_types:
            todo_ids |= get_untagged_doc_ids_by_ent_type(collection, in_ids, ent_type, MetaDicTagger, logger)
    return todo_ids


def add_doc_tagged_by_infos(document_ids: Set[int], collection: str, ent_types: List[str], tagger_name, tagger_version,
                            logger):
    # Add DocTaggedBy
    logger.info('Adding doc_tagged_by_info...')
    doc_tagged_by = []
    number_of_docs = len(document_ids)
    progress = Progress(total=number_of_docs * len(ent_types), print_every=1000, text="Compute insert...")
    progress.start_time()
    progress_i = 0
    for doc_id in document_ids:
        for ent_type in ent_types:
            progress_i += 1
            progress.print_progress(progress_i)
            doc_tagged_by.append(dict(
                document_id=doc_id,
                document_collection=collection,
                tagger_name=tagger_name,
                tagger_version=tagger_version,
                ent_type=ent_type,
                date_inserted=datetime.now()
            ))

    logger.info('Inserting...')
    session = Session.get()
    DocTaggedBy.bulk_insert_values_into_table(session, doc_tagged_by)
    logger.info('Finished')


def main(arguments=None):
    parser = ArgumentParser(description="Tag given documents in document format and insert tags into database")

    parser.add_argument("-c", "--collection", required=True)
    parser.add_argument("-v" "--vocabulary", required=True, help="tsv file containing vocabulary")

    group_settings = parser.add_argument_group("Settings")
    group_settings.add_argument("--config", default=ENTITY_LINKING_CONFIG,
                                help="Configuration file (default: {})".format(ENTITY_LINKING_CONFIG))
    group_settings.add_argument("--loglevel", default="INFO")
    group_settings.add_argument("--workdir", default=None)
    group_settings.add_argument("--skip-load", action='store_true',
                                help="Skip bulk load of documents on start (expert setting)")

    group_settings.add_argument("-w", "--workers", default=1, help="Number of processes for parallelized entitylinking",
                                type=int)
    parser.add_argument("-y", "--yes_force", help="skip prompt for workdir deletion", action="store_true")
    parser.add_argument("-f", "--force", help="skip checking for already tagged documents", action="store_true")
    parser.add_argument("--sections", action="store_true", default=False,
                        help="Should the section texts be considered when tagging?")
    parser.add_argument("-i", "--input", help="composite document file", required=False)
    args = parser.parse_args(arguments)

    conf = Config(args.config)

    # create directories
    root_dir = os.path.abspath(args.workdir) if args.workdir else tempfile.mkdtemp()
    log_dir = os.path.abspath(os.path.join(root_dir, "log"))
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


    logger.info('================== Preparation ==================')
    vocabs = Vocabulary(args.v__vocabulary)
    logging.info(f"reading vocabulary, this may take a while ...")
    vocabs.load_vocab()
    ent_types = vocabs.get_ent_types()

    input_file_given = True
    in_file = args.input
    if args.input:
        input_file_given = True
        if not args.force:
            document_ids = find_untagged_ids(in_file, logger, args.collection, ent_types=ent_types)  #
            number_of_docs = len(document_ids)
        else:
            document_ids = count.get_document_ids(in_file)
            number_of_docs = len(document_ids)

        if not args.skip_load:
            document_bulk_load(in_file, args.collection, logger=logger)
        else:
            logger.info("Skipping bulk load")

        session = Session.get()
        logger.info(f'Getting document ids from database for collection: {args.collection}...')
        document_ids_in_db = Document.get_document_ids_for_collection(session, args.collection)
        logger.info(f'{len(document_ids_in_db)} found')
        session.remove()
    else:
        session = Session.get()
        logger.info(f'Getting document ids from database for collection: {args.collection}...')
        document_ids_in_db = Document.get_document_ids_for_collection(session, args.collection)
        logger.info(f'{len(document_ids_in_db)} found')

        input_file_given = False
        logger.info('No input file given')
        logger.info(f'Retrieving document count for collection: {args.collection}')
        # compute the already tagged documents
        document_ids = document_ids_in_db
        todo_ids = set()
        logger.info('Retrieving documents that have been tagged before...')
        if not args.force:
            for ent_type in ent_types:
                todo_ids |= get_untagged_doc_ids_by_ent_type(args.collection, document_ids, ent_type, MetaDicTagger, logger)
            document_ids = todo_ids
        number_of_docs = len(document_ids)
        session.remove()

    logger.info(f'{number_of_docs} of documents have to be processed...')

    if number_of_docs == 0:
        logger.info('No documents to process - stopping')
        exit(0)
    else:
        logger.info(f"selected {number_of_docs} documents for processing")

    kwargs = dict(collection=args.collection, logger=logger, config=conf)

    logger.info('================== Init Tagger ==================')
    metatag = MetaDicTagger(vocabs, **kwargs)
    metatag.prepare()
    metatag.base_insert_tagger()
    session = Session.get()
    logger.info(f'Getting document ids from database for collection: {args.collection}...')
    document_ids_in_db = Document.get_document_ids_for_collection(session, args.collection)
    logger.info(f'{len(document_ids_in_db)} found')
    session.remove()

    consider_sections = args.sections
    logger.info(f'Consider sections: {consider_sections}')

    def generate_tasks():
        if input_file_given:
            for doc in read_tagged_documents(in_file):
                if doc and doc.id in document_ids and doc.has_content():
                    yield doc
        else:
            db_session = Session.get()
            logger.info('Retrieving documents from database...')
            for t_doc in iterate_over_all_documents_in_collection(db_session, args.collection,
                                                                  consider_sections=consider_sections):
                if t_doc.has_content():
                    yield t_doc
            db_session.remove()

    def do_task(in_doc: TaggedDocument):
        try:
            tagged_doc = metatag.tag_doc(in_doc, consider_sections=consider_sections)
            tagged_doc.clean_tags()
            return tagged_doc.tags
        except Exception as e:
            if in_doc:
                logger.error(f'Error when tagging {in_doc.id} ({str(e)})')
            else:
                logger.error('An error has occurred when tagging (document is None)')
            return []

    docs_done = multiprocessing.Value('i', 0)
    progress = Progress(total=number_of_docs, print_every=1000, text="Tagging...")
    progress.start_time()

    def consume_task(tags: List[TaggedEntity]):
        docs_done.value += 1
        progress.print_progress(docs_done.value)
        if len(tags) > 0:
            doc_id = tags[0].document
            if doc_id in document_ids_in_db and tags:
                metatag.base_insert_tags_partial(tags)

        if docs_done.value % BULK_INSERT_AFTER_K == 0:
            metatag.bulk_insert_partial_tags()

    def shutdown_consumer():
        metatag.bulk_insert_partial_tags()

    logger.info('================== Tagging ==================')
    task_queue = multiprocessing.Queue()
    result_queue = multiprocessing.Queue()
    producer = ProducerWorker(task_queue, generate_tasks, args.workers)
    workers = [Worker(task_queue, result_queue, do_task) for n in range(args.workers)]
    consumer = ConsumerWorker(result_queue, consume_task, args.workers, shutdown=shutdown_consumer)

    producer.start()
    for w in workers:
        w.start()
    consumer.start()
    consumer.join()

    logger.info('================== Finalizing ==================')
    # Finally add doc tagged by infos
    document_ids = document_ids.intersection(document_ids_in_db)
    add_doc_tagged_by_infos(document_ids, args.collection, ent_types, metatag.__name__, metatag.__version__, logger)

    if not args.workdir:
        logger.info(f'Remove temp directory: {root_dir}')
        shutil.rmtree(root_dir)

    progress.done()


if __name__ == '__main__':
    main()

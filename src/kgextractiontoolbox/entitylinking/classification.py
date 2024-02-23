import multiprocessing
import os
import shutil
import tempfile
from argparse import ArgumentParser

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import DocumentClassification, Document
from kgextractiontoolbox.backend.retrieve import iterate_over_all_documents_in_collection
from kgextractiontoolbox.document import count
from kgextractiontoolbox.document.document import TaggedDocument
from kgextractiontoolbox.document.extract import read_pubtator_documents
from kgextractiontoolbox.document.load_document import document_bulk_load
from kgextractiontoolbox.entitylinking.classifier import Classifier, BaseClassifier
from kgextractiontoolbox.entitylinking.utils import init_preprocess_logger, init_sqlalchemy_logger
from kgextractiontoolbox.progress import Progress
from kgextractiontoolbox.util.multiprocessing.ConsumerWorker import ConsumerWorker
from kgextractiontoolbox.util.multiprocessing.ProducerWorker import ProducerWorker
from kgextractiontoolbox.util.multiprocessing.Worker import Worker


def perform_classification(classifier: BaseClassifier, document_collection: str, input_file: str,
                           workdir: str, workers: int, consider_sections: bool = False, loglevel: str = "INFO",
                           skip_load: bool = True,
                           force: bool = False):
    """
    Basic script to classify documents
    :param classifier: The classifier object
    :param document_collection: the corresponding document collection
    :param input_file: a document input file (if none all documents of the collection will be used)
    :param workdir: specify workdir
    :param workers: number of parallel workers
    :param consider_sections: should sections be considered for the classification
    :param loglevel: current log level
    :param skip_load: should given documents be loaded first
    :param force: true removes the workdir if present
    :return:
    """
    # create directories
    root_dir = os.path.abspath(workdir) if workdir else tempfile.mkdtemp()
    log_dir = os.path.abspath(os.path.join(root_dir, "log"))
    in_file = input_file

    if workdir and os.path.exists(root_dir):
        if not force:
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
    logger = init_preprocess_logger(os.path.join(log_dir, "classification.log"), loglevel.upper())
    init_sqlalchemy_logger(os.path.join(log_dir, "sqlalchemy.log"), loglevel.upper())
    logger.info(f"Project directory:{root_dir}")

    input_file_given = True
    if in_file:
        logger.info("Reading input file and counting document ids...")
        in_ids = count.get_document_ids(in_file)
        number_of_docs = len(in_ids)

        if number_of_docs == 0:
            logger.info('No documents to process - stopping')
            exit(0)

        if not skip_load:
            document_bulk_load(in_file, document_collection, logger=logger)
        else:
            logger.info("Skipping bulk load")
    else:
        input_file_given = False
        logger.info('No input file given')
        logger.info(f'Counting documents for collection: {document_collection}')
        session = Session.get()
        number_of_docs = Document.count_documents_in_collection(session, document_collection)
        session.remove()

    session = Session.get()

    logger.info(f'Consider sections: {consider_sections}')

    def generate_tasks():
        if input_file_given:
            for doc in read_pubtator_documents(in_file):
                t_doc = TaggedDocument(doc, ignore_tags=True)
                if t_doc and t_doc.has_content():
                    yield t_doc
        else:
            db_session = Session.get()
            logger.info('Retrieving documents from database...')
            for t_doc in iterate_over_all_documents_in_collection(db_session, document_collection,
                                                                  consider_sections=consider_sections):
                if t_doc.has_content():
                    yield t_doc
            db_session.remove()

    def do_task(in_doc: TaggedDocument):
        classifier.classify_document(in_doc, consider_sections=consider_sections)
        return in_doc

    docs_done = multiprocessing.Value('i', 0)
    progress = Progress(total=number_of_docs, print_every=1000, text="Classifying...")
    progress.start_time()

    def consume_task(out_doc: TaggedDocument):
        docs_done.value += 1
        progress.print_progress(docs_done.value)
        if out_doc.classification:
            for classification, explanation in out_doc.classification.items():
                DocumentClassification.bulk_insert_values_into_table(session, [{
                    "document_id": out_doc.id,
                    "document_collection": document_collection,
                    "classification": classification,
                    "explanation": explanation
                }])

    task_queue = multiprocessing.Queue()
    result_queue = multiprocessing.Queue()
    producer = ProducerWorker(task_queue, generate_tasks, workers, max_tasks=100000)
    process_workers = [Worker(task_queue, result_queue, do_task) for n in range(workers)]
    consumer = ConsumerWorker(result_queue, consume_task, workers)

    producer.start()
    for w in process_workers:
        w.start()
    consumer.start()
    consumer.join()

    if not workdir:
        logger.info(f'Remove temp directory: {root_dir}')
        shutil.rmtree(root_dir)

    progress.done()


def add_classification_args(parser: ArgumentParser):
    parser.add_argument("-c", "--collection", required=True)
    parser.add_argument("--cls", required=True)
    group_settings = parser.add_argument_group("Settings")
    group_settings.add_argument("--loglevel", default="INFO")
    group_settings.add_argument("--workdir", default=None)
    group_settings.add_argument("--skip-load", action='store_true',
                                help="Skip bulk load of documents on start (expert setting)")

    group_settings.add_argument("-w", "--workers", default=1, help="Number of processes for parallelized preprocessing",
                                type=int)
    parser.add_argument("-y", "--yes_force", help="skip prompt for workdir deletion", action="store_true")

    parser.add_argument("-i", "--input", required=False, help="composite pubtator file", metavar="IN_DIR")
    parser.add_argument("--sections", action="store_true", default=False,
                        help="Should the section texts be considered when tagging?")


def main(arguments=None):
    parser = ArgumentParser(description="Classification script")
    add_classification_args(parser)
    parser.add_argument("-r", "--ruleset", required=True)
    args = parser.parse_args(arguments)

    classifier = Classifier(classification=args.cls, rule_path=args.ruleset)
    perform_classification(classifier=classifier, document_collection=args.collection,
                           input_file=args.input, workdir=args.workdir, workers=args.workers,
                           consider_sections=args.sections, loglevel=args.loglevel, skip_load=args.skip_load,
                           force=args.yes_force)


if __name__ == '__main__':
    main()

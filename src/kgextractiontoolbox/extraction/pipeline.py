import argparse
import json
import logging
import os
import shutil
import tempfile
from datetime import datetime
from typing import Optional, Set

from spacy.lang.en import English

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import DocProcessedByIE, Document
from kgextractiontoolbox.cleaning.relation_vocabulary import RelationVocabulary
from kgextractiontoolbox.config import NLP_CONFIG
from kgextractiontoolbox.document.count import count_documents
from kgextractiontoolbox.document.export import export
from kgextractiontoolbox.extraction.cosentences.main import run_co_occurrences_in_sentences
from kgextractiontoolbox.extraction.extraction_utils import filter_and_write_documents_to_tempdir
from kgextractiontoolbox.extraction.loading.load_openie_extractions import OpenIEEntityFilterMode, load_openie_tuples
from kgextractiontoolbox.extraction.loading.load_pathie_extractions import load_pathie_extractions
from kgextractiontoolbox.extraction.openie.main import run_corenlp_openie
from kgextractiontoolbox.extraction.openie51.main import openie51_run
from kgextractiontoolbox.extraction.openie6.main import openie6_run
from kgextractiontoolbox.extraction.pathie.main import pathie_run_corenlp, pathie_process_corenlp_output_parallelized
from kgextractiontoolbox.extraction.versions import PATHIE_EXTRACTION, OPENIE_EXTRACTION, PATHIE_STANZA_EXTRACTION, \
    OPENIE6_EXTRACTION, OPENIE51_EXTRACTION, COSENTENCE_EXTRACTION
from kgextractiontoolbox.util.helpers import chunks

DOCUMENTS_TO_PROCESS_IN_ONE_BATCH = 500000


def retrieve_document_ids_to_process(document_collection: str, extraction_type: str,
                                     document_id_filter: Optional[Set[int]] = None):
    """
    Computes the set of document that have not been processed yet
    Utilizes the ProcessedByIE table
    :param document_collection: the corresponding document collection
    :param extraction_type: the extraction type
    :param document_id_filter: Process only these document ids
    :return: a set of document ids that have not been processed yet
    """
    if document_id_filter:
        logging.info('{} ids retrieved from id file..'.format(len(document_id_filter)))
    session = Session.get()
    logging.info('Retrieving document ids from document table...')
    doc_ids_in_db = set()
    q = session.query(Document.id).filter(Document.collection == document_collection)
    for r in session.execute(q):
        doc_ids_in_db.add(r[0])
    document_id_filter = doc_ids_in_db if not document_id_filter else document_id_filter
    logging.info('{} document ids in Document table'.format(len(doc_ids_in_db)))
    logging.info('Retrieving already processed document ids from database...')
    q = session.query(DocProcessedByIE.document_id) \
        .filter_by(document_collection=document_collection) \
        .filter_by(extraction_type=extraction_type)
    processed_ids = set()
    for r in session.execute(q):
        processed_ids.add(r[0])
    logging.info('{} document ids are in the database'.format(len(processed_ids)))
    missing_ids = document_id_filter.intersection(doc_ids_in_db)
    missing_ids = missing_ids.difference(processed_ids)
    logging.info(
        '{} ids have already been processed and will be skipped'.format(len(document_id_filter) - len(missing_ids)))
    logging.info('{} remaining document ids to process...'.format(len(missing_ids)))
    return missing_ids


def mark_document_as_processed_by_ie(document_ids: [int], document_collection: str, extraction_type: str):
    """
    Insert a set of document ids into the ProcessedByIE table
    :param document_ids: a set of document ids
    :param document_collection: the corresponding document collection
    :param extraction_type: the extraction type
    :return: None
    """
    logging.info('Inserting processed document ids into database...')
    doc_inserts = []
    for doc_id in document_ids:
        doc_inserts.append(dict(document_id=doc_id,
                                document_collection=document_collection,
                                extraction_type=extraction_type,
                                date_inserted=datetime.now()))
    session = Session.get()
    DocProcessedByIE.bulk_insert_values_into_table(session, doc_inserts)
    logging.info(f'{len(doc_inserts)} document ids have been inserted')


def process_documents_ids_in_pipeline(ids_to_process: Set[int], document_collection, extraction_type, workers=1,
                                      corenlp_config=NLP_CONFIG,
                                      relation_vocab: RelationVocabulary = None,
                                      entity_filter: OpenIEEntityFilterMode = OpenIEEntityFilterMode.PARTIAL_ENTITY_FILTER,
                                      consider_sections=False):
    """
    Performs fact extraction for the given documents with the selected extraction type
    The document texts and tags will be exported automatically
    The extracted facts will be inserted into the predication table
    Stores the processed document ids in the ProcessedbyIE table
    :param ids_to_process: a set of document ids to process
    :param document_collection: the corresponding document collection
    :param extraction_type: the extraction type (e.g. PathIE)
    :param workers: the number of parallel workers (if extraction method is parallelized)
    :param corenlp_config: the nlp config
    :param relation_vocab: the relation vocabulary for PathIE (optional)
    :param entity_filter: the entity filter mode: Exact (IE arg must match entity str), Partial (entity is partially included), None = no entity checking
    :param consider_sections: Should document sections be considered for text generation?
    :return: None
    """
    # Read config
    with open(corenlp_config) as f:
        conf = json.load(f)
        core_nlp_dir = conf["corenlp"]

    time_start = datetime.now()
    working_dir = tempfile.mkdtemp()
    document_export_file = os.path.join(working_dir, 'document_export.pubtator')
    ie_input_dir = os.path.join(working_dir, 'ie')
    ie_filelist_file = os.path.join(working_dir, 'ie_filelist.txt')
    ie_output_file = os.path.join(working_dir, 'ie.output')
    if not os.path.exists(working_dir):
        os.mkdir(working_dir)
    if not os.path.exists(ie_input_dir):
        os.mkdir(ie_input_dir)

    logging.info('Process will work in: {}'.format(working_dir))
    export(document_export_file, export_tags=True, document_ids=ids_to_process, collection=document_collection,
           content=True, export_sections=consider_sections, export_format="json")
    time_exported = datetime.now()

    logging.info('Counting documents...')
    count_ie_files = count_documents(document_export_file)
    time_filtered = datetime.now()
    time_load = datetime.now()
    if count_ie_files == 0:
        logging.info('No files to process for IE - stopping')
    else:
        if extraction_type == PATHIE_EXTRACTION:
            logging.info('Init spacy nlp...')
            spacy_nlp = English()  # just the language with no model
            spacy_nlp.add_pipe("sentencizer")

            logging.info('Filtering documents...')
            count_ie_files, doc2tags = filter_and_write_documents_to_tempdir(len(ids_to_process), document_export_file,
                                                                             ie_input_dir, ie_filelist_file, spacy_nlp,
                                                                             workers,
                                                                             consider_sections=consider_sections)

            corenlp_output_dir = os.path.join(working_dir, 'corenlp_output')
            if not os.path.exists(corenlp_output_dir):
                os.mkdir(corenlp_output_dir)

            pathie_run_corenlp(core_nlp_dir, corenlp_output_dir, ie_filelist_file, worker_no=workers)

            logging.info("Processing output ...")
            start = datetime.now()

            pred_vocab = relation_vocab.relation_dict if relation_vocab else None
            # Process output
            pathie_process_corenlp_output_parallelized(corenlp_output_dir, count_ie_files, ie_output_file, doc2tags,
                                                       workers=workers, predicate_vocabulary=pred_vocab)
            logging.info((" done in {}".format(datetime.now() - start)))

            logging.info('Loading extractions into database...')
            time_load = datetime.now()
            load_pathie_extractions(ie_output_file, document_collection, PATHIE_EXTRACTION)
        elif extraction_type == PATHIE_STANZA_EXTRACTION:
            pred_vocab = relation_vocab.relation_dict if relation_vocab else None
            logging.info('Starting PathIE Stanza...')
            start = datetime.now()
            # only import stanze if required
            from kgextractiontoolbox.extraction.pathie_stanza.main import run_stanza_pathie
            run_stanza_pathie(document_export_file, ie_output_file, predicate_vocabulary=pred_vocab,
                              consider_sections=consider_sections)
            logging.info((" done in {}".format(datetime.now() - start)))
            load_pathie_extractions(ie_output_file, document_collection, PATHIE_STANZA_EXTRACTION)
        elif extraction_type == COSENTENCE_EXTRACTION:
            logging.info('Starting Co-Occurrence-based sentence extraction method...')
            start = datetime.now()
            run_co_occurrences_in_sentences(document_export_file, ie_output_file, consider_sections=consider_sections)
            logging.info((" done in {}".format(datetime.now() - start)))
            load_pathie_extractions(ie_output_file, document_collection, COSENTENCE_EXTRACTION)
        elif extraction_type in [OPENIE_EXTRACTION, OPENIE51_EXTRACTION, OPENIE6_EXTRACTION]:
            no_entity_filter = False
            if entity_filter == OpenIEEntityFilterMode.NO_ENTITY_FILTER:
                no_entity_filter = True
            logging.info(f'Starting {extraction_type}...')
            start = datetime.now()
            if extraction_type == OPENIE_EXTRACTION:
                run_corenlp_openie(document_export_file, ie_output_file, no_entity_filter=no_entity_filter,
                                   consider_sections=consider_sections)
            elif extraction_type == OPENIE51_EXTRACTION:
                openie51_run(document_export_file, ie_output_file, no_entity_filter=no_entity_filter,
                             consider_sections=consider_sections)
            elif extraction_type == OPENIE6_EXTRACTION:
                openie6_run(document_export_file, ie_output_file, no_entity_filter=no_entity_filter,
                            consider_sections=consider_sections)
            logging.info((" done in {}".format(datetime.now() - start)))
            load_openie_tuples(ie_output_file, document_collection, entity_filter=entity_filter,
                               extraction_type=extraction_type)

    time_open_ie = datetime.now()
    # add document as processed to database
    mark_document_as_processed_by_ie(ids_to_process, document_collection, extraction_type)
    logging.info('Process finished in {}s ({}s export, {}s filtering, {}s ie and {}s load)'
                 .format(time_open_ie - time_start, time_exported - time_start, time_filtered - time_exported,
                         time_open_ie - time_filtered, time_open_ie - time_load))

    logging.info('Removing temp directory...')
    shutil.rmtree(working_dir)
    logging.info('Finished')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--idfile", help="Document ID file (documents must be in database)")
    parser.add_argument("-et", "--extraction_type", required=True, help="the extraction method",
                        choices=list(
                            [OPENIE_EXTRACTION, OPENIE51_EXTRACTION, OPENIE6_EXTRACTION, PATHIE_EXTRACTION,
                             PATHIE_STANZA_EXTRACTION]))
    parser.add_argument("-c", "--collection", required=True, help="Name of the given document collection")
    parser.add_argument("--config", help="OpenIE / PathIE Configuration file", default=NLP_CONFIG)
    parser.add_argument("-w", "--workers", help="number of parallel workers", default=1, type=int)
    parser.add_argument("-bs", "--batch_size",
                        help="Batch size (how many documents should be processed and loaded in a batch)",
                        default=DOCUMENTS_TO_PROCESS_IN_ONE_BATCH, type=int)
    parser.add_argument('--relation_vocab', default=None, help='Path to a relation vocabulary (json file)')
    parser.add_argument("--entity_filter", default=OpenIEEntityFilterMode.PARTIAL_ENTITY_FILTER,
                        help="the entity filter mode", choices=OpenIEEntityFilterMode.to_str_list())
    parser.add_argument("--sections", action="store_true", default=False,
                        help="Should the section texts be considered in the extraction step?")
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)

    if args.relation_vocab:
        relation_vocab = RelationVocabulary()
        relation_vocab.load_from_json(args.relation_vocab)
    else:
        relation_vocab = None
    document_ids = set()
    if args.idfile:
        logging.info('Reading id file: {}'.format(args.idfile))
        with open(args.idfile, 'r') as f:
            document_ids = set([int(line.strip()) for line in f])
        logging.info(f'{len(document_ids)} documents in id file')
    else:
        logging.info(f'No id file given - query all known ids for document collection: {args.collection}')
        session = Session.get()
        for r in session.query(Document.id).filter(Document.collection == args.collection).distinct():
            document_ids.add(r[0])
        logging.info(f'{len(document_ids)} were found in db')
    document_ids_to_process = retrieve_document_ids_to_process(args.collection, args.extraction_type,
                                                               document_id_filter=document_ids)

    logging.info('Sorting document ids...')
    document_ids_to_process = sorted(list(document_ids_to_process))
    num_of_chunks = int(len(document_ids_to_process) / args.batch_size) + 1
    logging.info(f'Splitting task into {num_of_chunks} chunks...')
    for idx, batch_ids in enumerate(chunks(list(document_ids_to_process), args.batch_size)):
        logging.info('=' * 60)
        logging.info(f'       Processing chunk {idx+1}/{num_of_chunks}...')
        logging.info('=' * 60)
        process_documents_ids_in_pipeline(batch_ids, args.collection, args.extraction_type, corenlp_config=args.config,
                                          workers=args.workers, relation_vocab=relation_vocab,
                                          entity_filter=OpenIEEntityFilterMode(args.entity_filter),
                                          consider_sections=args.sections)


if __name__ == "__main__":
    main()

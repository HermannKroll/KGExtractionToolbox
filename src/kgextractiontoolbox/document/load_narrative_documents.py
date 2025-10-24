import argparse
import json
import logging
from pathlib import Path
from typing import Union

import kgextractiontoolbox.document.load_document as ld
from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import DocumentMetadata, Document
from kgextractiontoolbox.document.count import count_documents
from kgextractiontoolbox.document.extract import read_documents
from kgextractiontoolbox.document.narrative_document import NarrativeDocument
from kgextractiontoolbox.progress import Progress


def narrative_document_bulk_load(path: Union[Path, str], collection: str, tagger_mapping=None,
                                 logger=logging,
                                 artificial_document_ids: bool = False,
                                 replace_existing=False):
    """
    Loads a set of narrative document documents from a JSON into our database
    :param path: to a json file or directory of json files
    :param collection: the document collection to load
    :param tagger_mapping: tagger mapping if desired (optional)
    :param logger: logging class
    :param artificial_document_ids: Forces to generate artificial document ids (e.g. for non-int ids)
    :param bool replace_existing: If true, replaces existing documents in the database
    :return: None
    """

    # First call toolbox loading of document abstracts, tags, sections, etc
    ld.document_bulk_load(path, collection, tagger_mapping=tagger_mapping, logger=logger, ignore_tags=False,
                          replace_existing=replace_existing,
                          artificial_document_ids=artificial_document_ids)

    # we need to load the translation table from source ids to artificial db ids
    doc_source_id2art_id = {}
    if artificial_document_ids:
        session = Session.get()
        logger.info('Retrieving source id to art doc id table from database...')
        query = session.query(Document.source_id, Document.id).filter(Document.collection == collection)
        for row in query:
            if row.source_id:
                doc_source_id2art_id[row.source_id] = row.id

    # Load metadata stuff
    session = Session.get()
    n_docs = count_documents(path)
    progress = Progress(n_docs, print_every=1000, text="Loading narrative information")
    metadata_to_insert = []
    for idx, json_content in enumerate(read_documents(path)):
        progress.print_progress(idx)
        # if artificial document ids are generated, we need to set the generated id before loading from JSON
        if artificial_document_ids:
            json_data = json.loads(json_content)
            doc = NarrativeDocument(document_id=doc_source_id2art_id[json_data["source_id"]])
        else:
            doc = NarrativeDocument()

        doc.load_from_json(json_content)

        if doc.metadata:
            metadata_to_insert.append(dict(document_id=doc.id,
                                           document_collection=collection,
                                           authors=doc.metadata.authors,
                                           journals=doc.metadata.journals,
                                           publication_year=doc.metadata.publication_year,
                                           publication_month=doc.metadata.publication_month,
                                           publication_doi=doc.metadata.publication_doi,
                                           document_id_original=doc.metadata.document_id_original,
                                           ))

        if idx % ld.BULK_LOAD_COMMIT_AFTER == 0:
            DocumentMetadata.bulk_insert_values_into_table(session=session, values=metadata_to_insert)
            metadata_to_insert.clear()

    DocumentMetadata.bulk_insert_values_into_table(session=session, values=metadata_to_insert)
    logger.info('Finished insert')


def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("-c", "--collection", required=True, help="Document collection name")
    parser.add_argument("-t", "--tagger-map", help="JSON file containing mapping from entity type "
                                                   "to tuple with tagger name and tagger version")
    parser.add_argument("--logsql", action="store_true", help='logs sql statements')
    parser.add_argument("--artificial_document_ids", action="store_true", help="generates artifical document ids")
    parser.add_argument("--replace_existing", action="store_true",
                        help="Replace existing documents if found in the database")
    args = parser.parse_args(args)

    tagger_mapping = None
    if args.tagger_map:
        tagger_mapping = ld.read_tagger_mapping(args.tagger_map)
        tagger_list = list(tagger_mapping.values())
        tagger_list.append(ld.UNKNOWN_TAGGER)
        ld.insert_taggers(*tagger_list)

    if args.logsql:
        logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                            datefmt='%Y-%m-%d:%H:%M:%S',
                            level=logging.INFO)
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    else:
        logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                            datefmt='%Y-%m-%d:%H:%M:%S',
                            level=logging.INFO)

    narrative_document_bulk_load(args.input, args.collection, tagger_mapping,
                                 artificial_document_ids=args.artificial_document_ids,
                                 replace_existing=args.replace_existing)


if __name__ == "__main__":
    main()

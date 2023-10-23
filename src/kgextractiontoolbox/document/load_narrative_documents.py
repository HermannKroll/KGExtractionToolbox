import argparse
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Union

import kgextractiontoolbox.document.doctranslation as dc
import kgextractiontoolbox.document.load_document as ld
import kgextractiontoolbox.document.narrative_json_converter as jc
from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.document.count import count_documents
from kgextractiontoolbox.document.extract import read_pubtator_documents
from kgextractiontoolbox.progress import Progress
from kgextractiontoolbox.backend.models import DocumentMetadata
from kgextractiontoolbox.document.narrative_document import NarrativeDocument


def narrative_document_bulk_load(path: Union[Path, str], collection: str, tagger_mapping=None,
                                 logger=logging,
                                 artificial_document_ids: bool = False):
    """
    Loads a set of narrative document documents from a JSON into our database
    :param path: to a json file or directory of json files
    :param collection: the document collection to load
    :param tagger_mapping: tagger mapping if desired (optional)
    :param logger: logging class
    :param artificial_document_ids: Forces to generate artificial document ids (e.g. for non-int ids)
    :return: None
    """
    if artificial_document_ids:
        temp_dir = tempfile.mkdtemp()
        out = os.path.join(temp_dir, "outfile.json")
        dc.run_document_translation(path, out, jc.NarrativeJSONConverter, collection, load_function=narrative_document_bulk_load)
        shutil.rmtree(temp_dir)
    else:
        path_str = str(path).lower()
        if not path_str.endswith('.json'):
            raise ValueError(f'Only JSON format is supported: {path}')

        # First call toolbox loading of document abstracts, tags, sections, etc
        ld.document_bulk_load(path, collection, tagger_mapping=tagger_mapping, logger=logger, ignore_tags=False)

        # Load metadata stuff
        session = Session.get()
        n_docs = count_documents(path)
        progress = Progress(n_docs, print_every=1000, text="Loading narrative information")
        metadata_to_insert = []
        for idx, json_content in enumerate(read_pubtator_documents(path)):
            progress.print_progress(idx)
            doc = NarrativeDocument()
            doc.load_from_json(json_content)

            if doc.metadata:
                metadata_to_insert.append(dict(document_id=doc.id,
                                               document_collection=collection,
                                               authors=doc.metadata.authors,
                                               journals=doc.metadata.journals,
                                               publication_year=doc.metadata.publication_year,
                                               publication_month=doc.metadata.publication_month,
                                               publication_doi=doc.metadata.publication_doi))

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
    parser.add_argument("--artifical_document_ids", action="store_true", help="generates artifical document ids")
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
                                 artificial_document_ids=args.artificial_document_ids)


if __name__ == "__main__":
    main()

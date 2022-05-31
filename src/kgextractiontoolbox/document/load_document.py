import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, Union

import kgextractiontoolbox.document.doctranslation as dc
import kgextractiontoolbox.document.jsonconverter as jc
from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Document, Tag, Tagger, DocTaggedBy, DocumentSection, \
    DocumentClassification
from kgextractiontoolbox.document.count import count_documents
from kgextractiontoolbox.document.document import TaggedDocument
from kgextractiontoolbox.document.extract import read_pubtator_documents
from kgextractiontoolbox.progress import print_progress_with_eta
from kgtests import util

BULK_LOAD_COMMIT_AFTER = 50000
PRINT_ETA_EVERY_K_DOCUMENTS = 100
UNKNOWN_TAGGER = ["Unknown", "unknown"]


def read_tagger_mapping(filename: str) -> Dict[str, Tuple[str, str]]:
    """
    Reads the tagger mapping from `filename`.

    :param str filename: Path to tagger mapping JSON file.
    :return: Dict with entity type as key and tuple consisting of tagger name and tagger version as value
    """
    with open(filename) as f:
        content = f.read()
    mapping = json.loads(content)
    return mapping


def get_tagger_for_enttype(tagger_mapping, ent_type):
    if not tagger_mapping or ent_type not in tagger_mapping:
        return UNKNOWN_TAGGER[0], UNKNOWN_TAGGER[1]
    else:
        return tagger_mapping[ent_type][0], tagger_mapping[ent_type][1]


def insert_taggers(*tagger_list):
    """
    Inserts the taggers from the list.

    :param tagger_list: List consisting of Pairs with tagger name and tagger version
    :return:
    """
    session = Session.get()
    insert_values = []
    for tagger in tagger_list:
        insert_values.append(dict(
            name=tagger[0],
            version=tagger[1],
        ))
    Tagger.bulk_insert_values_into_table(session, insert_values, check_constraints=True)


def document_bulk_load(path: Union[Path, str], collection, tagger_mapping=None, logger=logging, ignore_tags=True,
                       artificial_document_ids=False):
    """
    Bulk load a file in PubTator/JSON Format or a directory of PubTator/JSON files into the database.
    Iterate over PubTator/JSON documents and add Document, Tag and DocTaggedBy objects.
    :param str path: Path to file or directory
    :param str collection: Identifier of the collection (e.g., PMC)
    :param dict tagger_mapping: Mapping from entity type to tuple (tagger name, tagger version)
    :param ignore_tags: if true no tags will be inserted
    :param logging logger: a logging instance to be used
    :param artificial_document_ids: Forces to generate artificial document ids (e.g. for non-int ids)
    :return:
    """
    if artificial_document_ids:
        out = util.tmp_rel_path("outfile.json")
        dc.run_document_translation(path, out, jc.JSONConverter, collection, load_function=document_bulk_load)
    else:
        session = Session.get()
        if tagger_mapping is None:
            logger.info("No tagger mapping provided.")
        logger.info('Bulk loading documents into database...')
        sys.stdout.write("Counting documents ...")
        sys.stdout.flush()
        n_docs = count_documents(path)
        sys.stdout.write("\rCounting documents ... found {}\n".format(n_docs))
        sys.stdout.flush()
        logger.info("Found {} documents".format(n_docs))

        logger.info('Retrieving document ids from database...')
        query = session.query(Document.id).filter_by(collection=collection)

        db_doc_ids = set()
        for r in session.execute(query):
            db_doc_ids.add(r[0])
        logger.info('{} documents are already inserted'.format(len(db_doc_ids)))
        start_time = datetime.now()

        document_inserts = []
        document_classification = []
        document_sections = []
        tag_inserts = []

        doc_tagged_by_inserts = []
        for idx, pubtator_content in enumerate(read_pubtator_documents(path)):
            doc = TaggedDocument(pubtator_content, ignore_tags=ignore_tags)
            tagged_ent_types = set()
            # Add document if its not already included
            if doc.id not in db_doc_ids and doc.has_content():
                db_doc_ids.add(doc.id)
                document_inserts.append(dict(
                    collection=collection,
                    id=doc.id,
                    title=doc.title,
                    abstract=doc.abstract,
                ))

            if doc.id not in db_doc_ids:
                logger.warning(
                    "Document {} {} is not inserted into DB (no title and no abstract)".format(collection, doc.id))

            if doc.classification:
                # add document classifications
                for d_class, d_explanation in doc.classification.items():
                    document_classification.append(dict(document_id=doc.id,
                                                        document_collection=collection,
                                                        classification=d_class,
                                                        explanation=d_explanation))

            if doc.sections:
                # add document sections
                for sec in doc.sections:
                    document_sections.append(dict(document_id=doc.id,
                                                  document_collection=collection,
                                                  position=sec.position,
                                                  title=sec.title,
                                                  text=sec.text))

            if doc.tags and not ignore_tags and doc.id in db_doc_ids:
                # Add tags
                for tag in doc.tags:
                    tagged_ent_types.add(tag.ent_type)

                    tag_inserts.append(dict(
                        ent_type=tag.ent_type,
                        start=tag.start,
                        end=tag.end,
                        ent_id=tag.ent_id,
                        ent_str=tag.text,
                        document_id=tag.document,
                        document_collection=collection,
                    ))

                # Add DocTaggedBy
                for ent_type in tagged_ent_types:
                    tagger_name, tagger_version = get_tagger_for_enttype(tagger_mapping, ent_type)
                    doc_tagged_by_inserts.append(dict(
                        document_id=doc.id,
                        document_collection=collection,
                        tagger_name=tagger_name,
                        tagger_version=tagger_version,
                        ent_type=ent_type,
                    ))

            if (idx + 1) % BULK_LOAD_COMMIT_AFTER == 0:
                Document.bulk_insert_values_into_table(session, document_inserts)
                Tag.bulk_insert_values_into_table(session, tag_inserts)
                DocTaggedBy.bulk_insert_values_into_table(session, doc_tagged_by_inserts)
                DocumentSection.bulk_insert_values_into_table(session, document_sections)
                DocumentClassification.bulk_insert_values_into_table(session, document_classification)

                document_inserts = []
                tag_inserts = []
                doc_tagged_by_inserts = []
                document_sections = []
                document_classification = []

            print_progress_with_eta("Adding documents", idx, n_docs, start_time,
                                    print_every_k=PRINT_ETA_EVERY_K_DOCUMENTS)

        Document.bulk_insert_values_into_table(session, document_inserts)
        Tag.bulk_insert_values_into_table(session, tag_inserts)
        DocTaggedBy.bulk_insert_values_into_table(session, doc_tagged_by_inserts)
        DocumentSection.bulk_insert_values_into_table(session, document_sections)
        DocumentClassification.bulk_insert_values_into_table(session, document_classification)

        sys.stdout.write("\rAdding documents ... done in {}\n".format(datetime.now() - start_time))
        logger.info("Added {} documents in {}".format(n_docs, datetime.now() - start_time))


def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("-c", "--collection", required=True, help="Document collection name")
    parser.add_argument("-t", "--tagger-map", help="JSON file containing mapping from entity type "
                                                   "to tuple with tagger name and tagger version")
    parser.add_argument("--ignore_tags", action="store_true", help="Will ignore all tags in this document")
    parser.add_argument("--logsql", action="store_true", help='logs sql statements')
    parser.add_argument("--artificial_document_ids", action="store_true", help="generates artificial document ids")
    args = parser.parse_args(args)

    tagger_mapping = None
    if args.tagger_map:
        tagger_mapping = read_tagger_mapping(args.tagger_map)
        tagger_list = list(tagger_mapping.values())
        tagger_list.append(UNKNOWN_TAGGER)
        insert_taggers(*tagger_list)

    if args.logsql:
        logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                            datefmt='%Y-%m-%d:%H:%M:%S',
                            level=logging.INFO)
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    else:
        logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                            datefmt='%Y-%m-%d:%H:%M:%S',
                            level=logging.INFO)

    document_bulk_load(args.input, args.collection, tagger_mapping, ignore_tags=args.ignore_tags,
                       artificial_document_ids=args.artificial_document_ids)


if __name__ == "__main__":
    main()

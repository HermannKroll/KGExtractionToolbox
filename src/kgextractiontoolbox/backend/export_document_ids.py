import argparse
import logging

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Document


def export_document_ids_to_file(output_file: str, document_collection: str, source_ids: bool = False):
    """
    Exports all database document ids for the given collection and writes them to the output file
    :param output_file: the output file (each line will contain a document id)
    :param document_collection: the corresponding document collection
    :param source_ids: whether to export source_ids rather than collection ids
    :return: None
    """
    session = Session.get()
    logging.info(f'Querying document ids for document collection: {document_collection}')
    if source_ids:
        doc_ids = list(Document.get_source_document_ids_for_collection(session=session, collection=document_collection))
    else:
        doc_ids = list(Document.get_document_ids_for_collection(session=session, collection=document_collection))

    doc_ids = sorted(doc_ids)
    logging.info(f'{len(doc_ids)} found')
    logging.info(f'Writing to file: {output_file}')
    with open(output_file, 'wt') as f:
        f.write('\n'.join([str(d) for d in doc_ids]))
    logging.info('Finished')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", help="Document ids will be written to this file")
    parser.add_argument("-c", "--collection", required=True, help="The document collection")
    parser.add_argument("--source-ids", required=False, help="Export source document ids",
                        action='store_true')
    args = parser.parse_args()
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)

    export_document_ids_to_file(args.output, args.collection, source_ids=args.source_ids)


if __name__ == "__main__":
    main()

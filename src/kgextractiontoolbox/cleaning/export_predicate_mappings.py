import argparse
import csv
import logging
from datetime import datetime

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Predication
from kgextractiontoolbox.progress import print_progress_with_eta


def export_predicate_mapping(output_file: str, document_collection: str = None):
    """
    Exports the predicate relation mappings with their corresponding count to a TSV file
    :param output_file: output will be written to this path
    :param document_collection: optional query predicate mappings only for a document collection
    :return: None
    """
    logging.info('Querying predicate relation mappings...')
    session = Session.get()
    mappings = Predication.query_predicates_with_mapping_and_count(session, document_collection)
    mapping_count = len(mappings)
    start_time = datetime.now()
    with open(output_file, 'wt') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['predicate', 'count', 'relation'])
        for idx, (predicate, relation, count) in enumerate(mappings):
            print_progress_with_eta('exporting statistics...', idx, mapping_count, start_time, print_every_k=100)
            writer.writerow([predicate, count, relation])
    logging.info(f'Export to {output_file} finished.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", help='Statistics will be written to this file')
    parser.add_argument("-c", "--collection", required=False, help="Count predicates only in document collection")
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)

    export_predicate_mapping(args.output, args.collection)


if __name__ == "__main__":
    main()

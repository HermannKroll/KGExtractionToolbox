import argparse
import json
import logging

from kgextractiontoolbox.backend.models import Document
from kgextractiontoolbox.backend.retrieve import retrieve_narrative_documents_from_database
from narraint.backend.database import SessionExtended


def export_narrative_documents(out_fn, collection=None, format="jsonl"):
    """
    Exports tagged documents in the database as a single PubTator file
    :param out_fn: path of file
    :param collection: document collection which should be exported, None = All
    :param format: export format (json or jsonl are supported)
    :return:
    """
    session = SessionExtended.get()

    doc_ids = set([row.id for row in session.query(Document.id).filter(Document.collection == collection)])
    print(f'found: {len(doc_ids)}')
    docs = retrieve_narrative_documents_from_database(session, doc_ids, document_collection=collection)
    docs_dict = [nd.to_dict() for nd in docs]

    if format == "json":
        with open(out_fn, 'wt') as f:
            json.dump(docs_dict, f, indent=2)
    elif format == "jsonl":
        with open(out_fn, 'wt') as f:
            f.write('\n'.join(json.dumps(doc_json.replace('\n', '')) for doc_json in docs_dict))
    else:
        raise ValueError(f'Invalid export format: {format}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("-c", "--collection", help="Collection(s)", default=None)
    parser.add_argument("--format", "-f", help='export format', choices=['json', 'jsonl'], default='jsonl')

    parser.add_argument("--sqllog", action="store_true", help='logs sql commands')
    args = parser.parse_args()

    export_narrative_documents(args.output, collection=args.collection, format=args.format)
    logging.info('Finished')


if __name__ == "__main__":
    main()

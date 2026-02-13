import logging

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Document, BULK_MAX_NO_OF_IN_VALUES
from kgextractiontoolbox.backend.retrieve import iterate_over_all_documents_in_collection
from kgextractiontoolbox.util.helpers import chunks
from kgextractiontoolbox.util.md5 import get_md5hash_from_str


def update_all_db_documents_with_md5_hash():
    logging.info("Updating documents with md5 hash ...")
    session = Session.get()
    logging.info("Getting available document collections...")
    document_collections = set([r[0] for r in session.query(Document.collection).distinct()])
    logging.info(f'{len(document_collections)} document collections found ...')
    for collection in document_collections:
        logging.info(f'Iterating over documents of collection {collection}...')
        docid2md5hash = {}
        # iterate over all documents of collection and compute the md5hash values (also consider fulltext if available)
        for doc in iterate_over_all_documents_in_collection(session, collection, consider_sections=True):
            docid2md5hash[doc.id] = get_md5hash_from_str(doc.get_text_content(sections=True))

        logging.info(f'{len(docid2md5hash)} document hashes were computed ...')
        updates = [dict(id=k, collection=collection, md5hash=v) for k, v in docid2md5hash.items()]
        for updates_to_perform in chunks(updates, BULK_MAX_NO_OF_IN_VALUES):
            session.bulk_update_mappings(Document, updates_to_perform)
            session.commit()
        logging.info('Update committed.')

    logging.info('Finished.')


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)
    update_all_db_documents_with_md5_hash()
import argparse
import logging

from sqlalchemy import delete

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Tag, Document, DocTaggedBy, DocProcessedByIE, Predication, Sentence, \
    DocumentTranslation, DocumentSection, DocumentClassification, DocumentMetadata


def delete_document_collection_from_database(document_collection: str):
    logging.info('Beginning deletion of document collection: {}'.format(document_collection))
    session = Session.get()

    logging.info('Deleting doc_processed_by_ie entries...')
    session.execute(delete(DocProcessedByIE).where(DocProcessedByIE.document_collection == document_collection))

    logging.info('Deleting predication entries...')
    session.execute(delete(Predication).where(Predication.document_collection == document_collection))

    logging.info('Deleting sentences entries...')
    session.execute(delete(Sentence).where(Sentence.document_collection == document_collection))

    logging.info('Deleting doc_tagged_by entries...')
    session.execute(delete(DocTaggedBy).where(DocTaggedBy.document_collection == document_collection))

    logging.info('Deleting tag entries...')
    session.execute(delete(Tag).where(Tag.document_collection == document_collection))

    logging.info('Deleting document translation entries...')
    session.execute(delete(DocumentTranslation).where(DocumentTranslation.document_collection == document_collection))

    logging.info('Deleting document section entries...')
    session.execute(delete(DocumentSection).where(DocumentSection.document_collection == document_collection))

    logging.info('Deleting document classification entries...')
    session.execute(delete(DocumentClassification).where(DocumentClassification.document_collection == document_collection))

    logging.info('Deleting document_metadata entries...')
    session.execute(delete(DocumentMetadata).where(DocumentMetadata.document_collection == document_collection))

    logging.info('Deleting document entries...')
    session.execute(delete(Document).where(Document.collection == document_collection))

    logging.info('Begin commit...')
    session.commit()
    logging.info('Commit complete - document collection deleted')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("collection")
    parser.add_argument("-f", "--force", help="skip user confirmation for deletion", action="store_true")

    args = parser.parse_args()
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)

    collection = args.collection
    logging.info('Counting documents for collection: {}'.format(collection))
    session = Session.get()
    doc_count = session.query(Document.id.distinct()).filter(Document.collection == collection).count()
    logging.info('{} documents found'.format(doc_count))
    answer = None;
    if not args.force:
        print('{} documents are found'.format(doc_count))
        print('Are you really want to delete all documents? This will also delete all corresponding tags (Tag), '
              'tagging information (doc_taggedb_by), facts (Predication) and extraction information (doc_processed_by_ie)')
        answer = input('Enter y(yes) to proceed the deletion...')
    if args.force or (answer and (answer.lower() == 'y' or answer.lower() == 'yes')):
        delete_document_collection_from_database(collection)
        logging.info('Finished')
    else:
        print('Canceled')


if __name__ == "__main__":
    main()

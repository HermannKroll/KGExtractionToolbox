import logging
from argparse import ArgumentParser

from sqlalchemy import func, and_

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Tag


def delete_short_entity_mentions(number_of_characters: int, document_collection: str = None):
    """
    Deletes all entities with mentions that are shorter than a certain number of characters
    :param number_of_characters: The number of characters (mentions with less are deleted)
    :param document_collection: the document collection for that deletion (if none all tags are considered)
    :return:
    """
    session = Session.get()

    count_query = session.query(Tag).filter(func.length(Tag.ent_str) < number_of_characters)
    if document_collection:
        count_query = count_query.filter(Tag.document_collection == document_collection)
    count = count_query.count()
    logging.info(f'Delete {count} entities with less than {number_of_characters} characters')

    delete_query = session.query(Tag).filter(func.length(Tag.ent_str) < number_of_characters)
    if document_collection:
        delete_query = delete_query.filter(Tag.document_collection == document_collection)
    delete_query.delete(synchronize_session='fetch')
    session.commit()
    logging.info('Committed')


def main():
    parser = ArgumentParser(description="Delete entities with short mentions")
    parser.add_argument("shorter_than", help="Entities with mentions less than this number are deleted",
                        type=int)
    parser.add_argument("-c", "--collection", help="Only perform the delete operation in this document collection")
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)

    args = parser.parse_args()
    delete_short_entity_mentions(args.shorter_than, args.collection)


if __name__ == '__main__':
    main()

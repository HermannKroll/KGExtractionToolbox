import argparse
import json
import logging

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Document, Tag
from kgextractiontoolbox.document.document import TaggedDocument, TaggedEntity

CONTENT_BUFFER_SIZE = 10000
TAG_BUFFER_SIZE = 100000


def export(out_fn, export_tags=True, document_ids=None, collection=None, content=True, logger=logging,
           content_buffer=CONTENT_BUFFER_SIZE, tag_buffer=TAG_BUFFER_SIZE, export_format="document"):
    """
    Exports tagged documents in the database as a single PubTator file
    :param out_fn: path of file
    :param export_tags: if true document tags will be exported
    :param document_ids: set of document ids which should be exported, None = All
    :param collection: document collection which should be exported, None = All
    :param content: if true, title and abstract are exported as well, if false only tags are exported
    :param logger: logging class
    :param content_buffer: buffer how much document contents should be retrieved from the database in one chunk
    :param tag_buffer: buffer how much tags should be retrieved from the database in one chunk
    :return:
    """
    logger.info("Beginning export...")
    if document_ids is None:
        document_ids = []
    else:
        logger.info('Using {} ids for a filter condition'.format(len(document_ids)))

    session = Session.get()

    if content:
        document_query = create_document_query(session, collection, document_ids, content_buffer)
    if export_tags:
        tag_query = create_tag_query(session, collection, document_ids, tag_buffer)

    if content and not export_tags:
        with open(out_fn, "w") as f:
            if export_format == "json":
                f.write("[\n")
                first_doc = True
                for document in document_query:
                    doc = TaggedDocument(id=document.id, title=document.title, abstract=document.abstract)
                    write_doc(doc, export_format, f, first_doc, export_content=content, export_tags=export_tags)
                    first_doc = False
                f.write("\n]\n")
            else:
                for document in document_query:
                    f.write(Document.create_pubtator(document.id, document.title, document.abstract) + "\n")

    elif not content and export_tags:
        with open(out_fn, "w") as f:
            if export_format == "json":
                f.write("[\n")
                first_doc = True
                current_doc = None

                for tag in tag_query:
                    # flush if new document_id is reached
                    if not current_doc or tag.document_id != current_doc.id:
                        if current_doc:
                            write_doc(current_doc, export_format, f, first_doc, export_content=content,
                                      export_tags=export_tags)
                            first_doc = False
                        current_doc = TaggedDocument(id=tag.document_id)

                    current_doc.tags.append(TaggedEntity(document=tag.document_id, start=tag.start, end=tag.end,
                                                         text=tag.ent_str, ent_type=tag.ent_type, ent_id=tag.ent_id))
                write_doc(current_doc, export_format, f, first_doc, export_content=content, export_tags=export_tags)
                f.write("\n]\n")
            else:
                for tag in tag_query:
                    f.write(
                        Tag.create_pubtator(tag.document_id, tag.start, tag.end, tag.ent_str, tag.ent_type, tag.ent_id))

    elif content and export_tags:
        content_iter = iter(document_query)
        current_document = None
        document_builder: TaggedDocument = None
        first_doc = True
        with open(out_fn, "w") as f:
            if export_format == "json":
                f.write("[\n")
            for tag in tag_query:
                # skip to tagged document
                while not current_document or not (
                        tag.document_id == current_document.id
                        and tag.document_collection == current_document.collection):
                    if document_builder:
                        write_doc(document_builder, export_format, f, first_doc)
                        first_doc = False
                    current_document = next(content_iter)
                    document_builder = TaggedDocument(id=current_document.id,
                                                      title=current_document.title,
                                                      abstract=current_document.abstract)
                document_builder.tags.append(TaggedEntity(document=document_builder.id,
                                                          start=tag.start,
                                                          end=tag.end,
                                                          text=tag.ent_str,
                                                          ent_type=tag.ent_type,
                                                          ent_id=tag.ent_id))

            if document_builder:
                write_doc(document_builder, export_format, f, first_doc)

            # Write tailing documents with no tags
            current_document = next(content_iter, None)
            while current_document:
                write_doc(TaggedDocument(id=current_document.id,
                                         title=current_document.title,
                                         abstract=current_document.abstract),
                          export_format, f, first_doc
                          )
                current_document = next(content_iter, None)
            # end export with a new line

            if export_format == "json":
                f.write("\n]\n")


def write_doc(document_builder, export_format, f, first_doc, export_content=True, export_tags=True):
    if export_format == "json":
        if not first_doc:
            f.write(",\n")
        json.dump(document_builder.to_dict(export_content=export_content, export_tags=export_tags), f, indent=1)
    elif export_format == "document":
        f.write(str(document_builder))


def create_tag_query(session, collection=None, document_ids=None, tag_buffer=TAG_BUFFER_SIZE):
    """
    returns a query for tags with specified parameters
    :param session: session to execute query on
    :param collection: filter by collection
    :param document_ids: filter by ids
    :param tag_buffer: yield per tag_buffer
    :return:
    """
    tag_query = session.query(Tag).yield_per(tag_buffer)
    if collection:
        tag_query = tag_query.filter_by(document_collection=collection)
    if document_ids:
        tag_query = tag_query.filter(Tag.document_id.in_(document_ids))
    tag_query = tag_query.order_by(Tag.document_collection, Tag.document_id, Tag.start, Tag.id)
    return tag_query


def create_document_query(session, collection=None, document_ids=None, content_buffer=CONTENT_BUFFER_SIZE):
    document_query = session.query(Document).yield_per(content_buffer)
    if collection:
        document_query = document_query.filter_by(collection=collection)
    if document_ids:
        document_query = document_query.filter(Document.id.in_(document_ids))
    document_query = document_query.order_by(Document.collection, Document.id)
    return document_query


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("--ids", nargs="*", metavar="DOC_ID")
    parser.add_argument("--idfile", help='file containing document ids (one id per line)')
    parser.add_argument("-c", "--collection", help="Collection(s)", default=None)
    parser.add_argument("-d", "--document", action="store_true", help="Export content of document")
    parser.add_argument("-t", "--tags", action="store_true", help="Export document tags")
    parser.add_argument("--format", "-f", help='export format', choices=['json', 'pubtator'], default='json')

    parser.add_argument("--sqllog", action="store_true", help='logs sql commands')
    args = parser.parse_args()

    # hack
    args.format = "document" if args.format == 'pubtator' else args.format

    if not (args.tags or args.document):
        parser.error('No action requested, add -d or -t')

    if args.ids and args.idfile:
        parser.error('Does not support a list of ids and an ids file')

    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)
    logger = logging.getLogger("export")
    if args.sqllog:
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    if args.ids:
        document_ids = [int(x) for x in args.ids]
    elif args.idfile:
        logger.info('reading id file: {}'.format(args.idfile))
        with open(args.idfile, 'r') as f:
            document_ids = list(set([int(line.strip()) for line in f]))
        logger.info('{} ids retrieved from id file..'.format(len(document_ids)))
    else:
        document_ids = None

    export(args.output, export_tags=args.tags, document_ids=document_ids, collection=args.collection,
           content=args.document, logger=logger,
           export_format=args.format)
    logging.info('Finished')


if __name__ == "__main__":
    main()

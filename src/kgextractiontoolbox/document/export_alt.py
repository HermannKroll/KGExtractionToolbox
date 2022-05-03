import argparse
import json
import logging
from typing import List

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Document, Tag, DocumentTranslation
from kgextractiontoolbox.document.document import TaggedDocument, TaggedEntity

CONTENT_BUFFER_SIZE = 10000
TAG_BUFFER_SIZE = 100000


def write_doc(doc: TaggedDocument, export_format: str, f, first_doc: bool, export_content=True, export_tags=True):
    """
    Writes a document to a file
    :param doc: the tagged document object
    :param export_format: the given export format
    :param f: the open file
    :param first_doc: true if its the first document
    :param export_content: content should be exported
    :param export_tags: tags should be exported
    :return: None
    """
    if export_format == "json":
        if not first_doc:
            f.write(",\n")
        json.dump(doc.to_dict(export_content=export_content, export_tags=export_tags), f, indent=1)
    elif export_format == "pubtator":
        f.write(str(doc))


def write_docs_as_json(f_obj, documents: List[TaggedDocument], export_content=True, export_tags=True):
    """
    Writes a list of tagged documents to a json file
    :param f_obj: open file pointer
    :param documents: a list of tagged documents
    :param export_content: should the content be exported
    :param export_tags: should tags be exported
    :return: None
    """
    f_obj.write('[\n')
    first_doc = True
    for doc in documents:
        write_doc(doc, first_doc=first_doc, export_format="json", export_content=export_content,
                  export_tags=export_tags, f=f_obj)
        first_doc = False
    f_obj.write('\n]')


def export(out_fn, export_tags=True, document_ids=None, collection=None, content=True, logger=logging,
           content_buffer=CONTENT_BUFFER_SIZE, tag_buffer=TAG_BUFFER_SIZE, export_format="pubtator",
           write_doc=write_doc, translate_document_ids: bool = False):
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
    :param export_format: json or pubtator
    :param write_doc: specify a export writing function
    :param translate_document_ids: if true document translations (source ids) from DocumentTranslation are queried
    :return:
    """
    logger.info("Beginning export...")
    if document_ids is None:
        document_ids = []
    else:
        logger.info('Using {} ids for a filter condition'.format(len(document_ids)))

    session = Session.get()
    doc_id_2_source_id = {}
    if translate_document_ids:
        logger.info('Querying DocumentTranslation source ids...')
        query = session.query(DocumentTranslation.document_id, DocumentTranslation.source_doc_id) \
            .filter(DocumentTranslation.document_collection == collection)
        for r in query:
            doc_id_2_source_id[r[0]] = r[1]
        logger.info(f'Found {len(doc_id_2_source_id)} id translations')

    if content:
        document_query = create_document_query(session, collection, document_ids, content_buffer)
    if export_tags:
        tag_query = create_tag_query(session, collection, document_ids, tag_buffer=tag_buffer)

    if content and not export_tags:
        with open(out_fn, "w") as f:
            if export_format == "json":
                f.write("[\n")
                first_doc = True
                for document in document_query:
                    doc = TaggedDocument(id=document.id, title=document.title, abstract=document.abstract)
                    if translate_document_ids:
                        doc.id = doc_id_2_source_id[doc.id]

                    write_doc(doc, export_format, f, first_doc, export_content=content, export_tags=export_tags)
                    first_doc = False
                f.write("\n]\n")
            else:
                for document in document_query:
                    doc_id = document.id
                    if translate_document_ids:
                        doc_id = doc_id_2_source_id[doc_id]
                    f.write(Document.create_pubtator(doc_id, document.title, document.abstract) + "\n")

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
                        if translate_document_ids:
                            current_doc.id = doc_id_2_source_id[current_doc.id]

                    if translate_document_ids:
                        current_doc.tags.append(TaggedEntity(document=doc_id_2_source_id[tag.document_id],
                                                             start=tag.start, end=tag.end,
                                                             text=tag.ent_str, ent_type=tag.ent_type,
                                                             ent_id=tag.ent_id))
                    else:
                        current_doc.tags.append(TaggedEntity(document=tag.document_id, start=tag.start, end=tag.end,
                                                             text=tag.ent_str, ent_type=tag.ent_type,
                                                             ent_id=tag.ent_id))

                write_doc(current_doc, export_format, f, first_doc, export_content=content, export_tags=export_tags)
                f.write("\n]\n")
            else:
                for tag in tag_query:
                    if translate_document_ids:
                        f.write(Tag.create_pubtator(doc_id_2_source_id[tag.document_id], tag.start, tag.end,
                                                    tag.ent_str, tag.ent_type, tag.ent_id))
                    else:
                        f.write(Tag.create_pubtator(tag.document_id, tag.start, tag.end,
                                                    tag.ent_str, tag.ent_type, tag.ent_id))

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
                        if translate_document_ids:
                            document_builder.id = doc_id_2_source_id[document_builder.id]
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
                if translate_document_ids:
                    document_builder.id = doc_id_2_source_id[document_builder.id]
                    for t in document_builder.tags:
                        t.document = document_builder.id
                write_doc(document_builder, export_format, f, first_doc)
                first_doc = False

            # Write tailing documents with no tags
            current_document = next(content_iter, None)
            while current_document:
                doc = TaggedDocument(id=current_document.id,
                                     title=current_document.title,
                                     abstract=current_document.abstract)
                if translate_document_ids:
                    doc.id = doc_id_2_source_id[doc.id]
                write_doc(doc, export_format, f, first_doc)
                first_doc = False
                current_document = next(content_iter, None)
            # end export with a new line

            if export_format == "json":
                f.write("\n]\n")


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
    parser.add_argument("-t", "--tag", action='store_true', help="export tags")
    parser.add_argument("--format", "-f", help='export format', choices=['json', 'pubtator'], default='json')
    parser.add_argument("--translate_ids", help="force the translation of document ids via DocumentTranslation",
                        required=False, action="store_true")

    parser.add_argument("--sqllog", action="store_true", help='logs sql commands')
    args = parser.parse_args()

    if not (args.tag or args.document):
        parser.error('No action requested, add -d or -t')

    if args.ids and args.idfile:
        parser.error('Does not support a list of ids and an ids file')

    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)
    logger = logging.getLogger("export")
    if args.sqllog:
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    export_tags = args.tag

    if args.ids:
        document_ids = [int(x) for x in args.ids]
    elif args.idfile:
        logger.info('reading id file: {}'.format(args.idfile))
        with open(args.idfile, 'r') as f:
            document_ids = list(set([int(line.strip()) for line in f]))
        logger.info('{} ids retrieved from id file..'.format(len(document_ids)))
    else:
        document_ids = None

    export(args.output, export_tags=export_tags,
           document_ids=document_ids, collection=args.collection, content=args.document,
           logger=logging, export_format=args.format, translate_document_ids=args.translate_ids)
    logging.info('Finished')


if __name__ == "__main__":
    main()

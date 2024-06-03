import argparse
import json
import logging

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import DocumentTranslation
from kgextractiontoolbox.document.document import TaggedDocument

from kgextractiontoolbox.backend.retrieve import iterate_over_all_documents_in_collection


def write_doc(doc: TaggedDocument, export_format: str, f, first_doc: bool, export_content=True, export_tags=True,
              export_sections=True, export_classification=True):
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
        json.dump(doc.to_dict(export_content=export_content, export_tags=export_tags, export_sections=export_sections,
                              export_classification=export_classification), f, indent=1)
    elif export_format == "jsonl":
        if not first_doc:
            f.write('\n')
        json.dump(doc.to_dict(export_content=export_content, export_tags=export_tags, export_sections=export_sections,
                              export_classification=export_classification), f)
    elif export_format == "pubtator":
        f.write(str(doc))


def export(out_fn, export_tags=True, export_sections=True, export_classification=False, document_ids=None,
           collection=None, content=True, logger=logging, export_format="json",
           write_doc=write_doc, translate_document_ids: bool = False):
    """
    Exports tagged documents in the database as a single PubTator file
    :param out_fn: path of file
    :param export_tags: if true document tags will be exported
    :param export_sections: if true document sections will be exported
    :param export_classification: if true document classifications will be exported
    :param document_ids: set of document ids which should be exported, None = All
    :param collection: document collection which should be exported, None = All
    :param content: if true, title and abstract are exported as well, if false only tags are exported
    :param logger: logging class
    :param export_format: json or pubtator
    :param write_doc: specify a export writing function
    :param translate_document_ids: if true document translations (source ids) from DocumentTranslation are queried
    :return:
    """
    if export_format not in ["pubtator", "json", "jsonl"]:
        raise ValueError(f"Export format {export_format} not supported (supported: pubtator, json, jsonl)")

    logger.info("Beginning export...")
    if export_format == "pubator" and export_sections and export_classification:
        raise ValueError("Pubtator format does not support document sections and classifications")
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

    t_docs = iterate_over_all_documents_in_collection(session, collection=collection, document_ids=document_ids,
                                                      consider_tag=export_tags, consider_sections=export_sections,
                                                      consider_classification=export_classification)

    first_doc = True
    with open(out_fn, "w") as f:
        if export_format == "json":
            f.write("[\n")
        for idx, res in enumerate(t_docs):
            if idx > 0:
                first_doc = False
            if translate_document_ids:
                res.id = doc_id_2_source_id[res.id]
            write_doc(res, export_format, f, first_doc, export_content=content, export_tags=export_tags,
                      export_sections=export_sections, export_classification=export_classification)
        if export_format == "json":
            f.write("\n]\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("--ids", nargs="*", metavar="DOC_ID")
    parser.add_argument("--idfile", help='file containing document ids (one id per line)')
    parser.add_argument("-c", "--collection", help="Collection(s)", default=None)
    parser.add_argument("-d", "--document", action="store_true", help="Export content of document")
    parser.add_argument("-t", "--tag", action='store_true', help="export tags")
    parser.add_argument("--format", "-f", help='export format', choices=['json', 'pubtator', 'jsonl'], default='jsonl')
    parser.add_argument("--translate_ids", help="force the translation of document ids via DocumentTranslation",
                        required=False, action="store_true")
    parser.add_argument("-dc", "--classification", help="export classification", required=False, action="store_true")


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

    export(args.output, export_tags=export_tags, export_classification= args.classification,
           document_ids=document_ids, collection=args.collection, content=args.document,
           logger=logging, export_format=args.format, translate_document_ids=args.translate_ids)
    logging.info('Finished')


if __name__ == "__main__":
    main()

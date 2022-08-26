import logging
import os.path
from argparse import ArgumentParser
from pathlib import Path
from typing import Union, Iterator

import kgextractiontoolbox.document.count as c
from kgextractiontoolbox.document.doctranslation import DocumentTranslationLoader, SourcedDocument, \
    run_document_translation

from kgextractiontoolbox.document.document import TaggedDocument
from kgextractiontoolbox.document.extract import read_pubtator_documents


class JSONConverter(DocumentTranslationLoader):

    def read_sourced_documents(self, file: Union[Path, str]) -> Iterator[SourcedDocument]:
        for content in read_pubtator_documents(file):
            doc = TaggedDocument(content)
            basename = os.path.basename(file)
            yield SourcedDocument(doc.id, basename, doc)

    def count_documents(self, file: Union[Path, str]):
        return c.count_documents(file)


def main():
    parser = ArgumentParser(description="Tool to convert JSON file to Pubtator format")
    parser.add_argument("input", help="Input file", metavar="INPUT_FILE_OR_DIR")
    parser.add_argument("output", help="Output file", metavar="OUTPUT_FILE")
    parser.add_argument("-c", "--collection", required=True, help="document collection")
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)

    run_document_translation(args.input, args.output, JSONConverter, collection=args.collection)


if __name__ == "__main__":
    main()

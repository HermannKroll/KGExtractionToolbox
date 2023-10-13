import logging
import os.path
from argparse import ArgumentParser
from pathlib import Path
from typing import Union, Iterator

import kgextractiontoolbox.document.count as c
import kgextractiontoolbox.document.doctranslation as dt
import kgextractiontoolbox.document.narrative_document as nd
from kgextractiontoolbox.document.extract import read_pubtator_documents


class NarrativeJSONConverter(dt.DocumentTranslationLoader):

    def read_sourced_documents(self, file: Union[Path, str]) -> Iterator[dt.SourcedDocument]:
        for content in read_pubtator_documents(file):
            doc = nd.NarrativeDocument()
            doc.load_from_json(content)
            basename = os.path.basename(file)
            yield dt.SourcedDocument(doc.id, basename, doc)

    def count_documents(self, file: Union[Path, str]):
        return c.count_documents(file)


def main():
    parser = ArgumentParser(description="Translates a narrative document json by using artificial ids")
    parser.add_argument("input", help="Input file", metavar="INPUT_FILE_OR_DIR")
    parser.add_argument("output", help="Output file", metavar="OUTPUT_FILE")
    parser.add_argument("-c", "--collection", required=True, help="document collection")
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)

    import kgextractiontoolbox.document.load_narrative_documents as lnd
    dt.run_document_translation(args.input, args.output, NarrativeJSONConverter, collection=args.collection,
                                load_function=lnd.narrative_document_bulk_load)


if __name__ == "__main__":
    main()

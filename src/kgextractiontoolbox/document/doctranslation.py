import argparse
import datetime
import hashlib
import json
import logging
from dataclasses import dataclass
from operator import and_
from pathlib import Path
from typing import Union, Type, List, Iterator

from sqlalchemy import select, func

import kgextractiontoolbox.backend.database as db
import kgextractiontoolbox.backend.models as kgmodels
from kgextractiontoolbox.document.document import TaggedDocument
from kgextractiontoolbox.progress import Progress


@dataclass
class SourcedDocument:
    """
    A dataclass for attacing a Tagged document to a uid of a third-party corpus as well as a reference to the source document
    """
    source_id: str
    source: str
    doc: TaggedDocument


class DocumentTranslationLoader:
    """
    An abstract class for loading a third-party corpus while keeping track of the original uids. The script is also
    able to detect changes in the documents in comparison to older versions of the same corpus by using an md5 sum over
    title and abstract, thus enabeling incremental loading.
    When creating a new Translation subclass, the abstract methods read_sourced_docuemnts and count_documents need to be
    overwritten.
    """

    def __init__(self, collection: str, loader_kwargs=None):
        """
        superconstructor to be called by subclass. The class instance is bound to a single document collection value for
        the document collection column in the databse
        :param collection: the document collection to be considered by the class
        :type collection: str
        """
        self.session = db.Session.get()
        self.collection = collection
        self.current_art_id = self.poll_hightest_art_id() + 1
        self.insertion_time = datetime.datetime.now()

    def poll_hightest_art_id(self) -> int:
        """
        retrieve the highest present document_id present in the document_translation_table
        :return: The lowest document_id in the document_id_collumn of the document_translation_table. 0 if empty.
        :rtype: int
        """
        result = self.session.execute(
            select(
                func.max(kgmodels.DocumentTranslation.document_id)
            ).where(kgmodels.DocumentTranslation.document_collection == self.collection)
        )
        return [r for r in result][0][0] or 0

    # TODO: it is an utterly bad idea to send one query per document. query all hashes at the start, than expand.
    def check_md5_changed(self, doc: SourcedDocument) -> str:
        """
        calculate the hexadecimal representation of md5 sum of a sourced document using its title and abstract
        :param doc: the document to calculate the md5 sum for
        :type doc: SourcedDocument
        :return: hex-repr. of the md5 sum
        :rtype: str
        """
        result = self.session.execute(
            select(
                kgmodels.DocumentTranslation.md5
            ).where(and_(
                kgmodels.DocumentTranslation.document_collection == self.collection,
                kgmodels.DocumentTranslation.source_doc_id == doc.source_id
            ))
        )
        result = [r for r in result]
        if not result:
            return True
        else:
            return result[0][0] != self.get_md5(doc)

    def create_translation_entry(self, sdoc: SourcedDocument):
        """
        from a Sourced document create a new translation entry by generating a new document_id
        :param sdoc: the sourced doc to create the doc_translation for. The id of the doc will be set
        :type sdoc: SourcedDocument
        :return: a dictionary containing the values of the translation entry
        :rtype: dict
        """
        sdoc.doc.id = self.current_art_id
        self.current_art_id += 1
        return {
            "document_id": sdoc.doc.id,
            "document_collection": self.collection,
            "source_doc_id": sdoc.source_id,
            "md5": self.get_md5(sdoc),
            "source": sdoc.source,
            "date_inserted": self.insertion_time
        }

    def translate(self, infile: Union[Path, str], outfile: Union[Path, str], insert_every: int = 1000,
                  diff: bool = False, prog_logger: Progress = None, limit: int = None) -> int:
        """
        Iteratively poll SourcedDocuments from read_sourced_documents and translate them. If diff is set to true, the
        documents will be checked against the md5 sums present in the database and will only be processed if new or changed.
        The resulting translation entries will be inserted into the document_translation_table and the documents will be written
        into the outfile in json format. The progress can be printed to the console if a prog_logger is given.
        :param infile: input file readable by the overwritten read_sourced_documents
        :param outfile: json output file for the processed docs
        :param insert_every: Bulk insert is called after insert_every documents have been processed
        :param diff: check md5 sums against database
        :param prog_logger: display progress using a Progress logger
        :return: The number of actually processed (new or changed) docs.
        """
        translations = []
        processed_docs = 0
        with open(outfile, "w+") as outf:
            prog_logger.start_time()
            outf.write("[")
            first = True
            for n, sdoc in enumerate(self.read_sourced_documents(infile)):
                if limit and processed_docs > limit:
                    break
                if not diff or self.check_md5_changed(sdoc):
                    translations.append(self.create_translation_entry(sdoc))
                    if not first:
                        outf.write(",\n")
                    else:
                        first = False
                    outf.write(json.dumps(sdoc.doc.to_dict()))
                    processed_docs += 1
                    if len(translations) > insert_every:
                        self.flush(translations)
                        translations = []
                prog_logger.print_progress(processed_docs)
            self.flush(translations)
            outf.write("]")
            prog_logger.done()
            return processed_docs

    def flush(self, translations):
        """
        Bulk insert a number of translations into the document_translation table
        :param translations: a list of translation entry dictionaries
        :return: None
        """
        kgmodels.DocumentTranslation.bulk_insert_values_into_table(self.session, translations)

    @staticmethod
    def get_md5(sdoc: SourcedDocument) -> str:
        """
        Calculate the md5 sum of a SourcedDocument over its title and abstract
        :param sdoc: the document to hash
        :return: the hexadecimal representation of the md5 sum
        """
        return hashlib.md5((sdoc.doc.title + sdoc.doc.abstract).encode('unicode_escape')).hexdigest()

    def read_sourced_documents(self, file: Union[Path, str]) -> Iterator[SourcedDocument]:
        """
        This abstract method is responsible for reading a third party document format and yielding its contained sourced
        documents
        :param file: the third-party input file
        :return: an Iterator over the SourcedDocuments contained in the input file
        :rtype:
        """
        raise NotImplementedError()

    def count_documents(self, file: Union[Path, str]) -> int:
        """
        This abstract method is responsible for counting the documents contained in a third-party input file
        :param file: the tird-party input file
        :return: the number of documents contained within the file
        """
        raise NotImplementedError()


def run_document_translation(input: Union[Path, str], output: Union[Path, str],
                             doctranslation_subclass: Type[DocumentTranslationLoader], collection: str,
                             loader_kwargs=None, convert_difference_only=False,
                             document_limit=None, load_function=None):
    loader = doctranslation_subclass(collection, loader_kwargs)
    logging.info("Document translation loader init...")
    logging.debug(f"Input file: {input}")
    logging.debug(f"Output file: {output}")
    logging.info("Counting documents...")
    count = loader.count_documents(input)
    logging.info(f"Found {count} documents.")
    prog = Progress(total=(document_limit or count), text="Translating", print_every=1000)
    proc_docs = loader.translate(input, output, diff=convert_difference_only, prog_logger=prog, limit=document_limit)
    logging.info(f"Processed {proc_docs} new or changed documents.")
    if load_function:
        load_function(output, collection)
    else:
        import kgextractiontoolbox.document.load_document as ld
        ld.document_bulk_load(output, collection)


def main(doctranslation_subclass: Type[DocumentTranslationLoader], doctrans_args=None, args: List[str] = None,
         parser=None, loader_kwargs=None):
    """
    Run the document translation, insert translation entries into the document_translation table,
    export documents to a json file and load them into the database if -l flag is set.
    :param doctrans_args: keyword arguments for doctranslation
    :param doctranslation_subclass: The subclass of the DocumentTranlationLoader capable of reading SourcedDocuments from
    the used third-party format
    :param args: command line arguments
    :return: None
    """
    if doctrans_args is None:
        doctrans_args = {}
    parser = parser or argparse.ArgumentParser("load pollux documents")
    parser.add_argument("input", help="ijson input file")
    parser.add_argument("output", help="output json file")
    parser.add_argument("-c", "--collection", required=True, help="document collection")
    parser.add_argument("-d", "--diff", action="store_true", help="only process documents with new/changed md5 hash")
    parser.add_argument("-l", "--load", action="store_true", help="load document contents into document table")
    parser.add_argument("-n", "--limit", type=int, help="Only exctract that many documents from source doc")
    args = parser.parse_args(args)

    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)

    run_document_translation(args.input, args.output, doctranslation_subclass, args.collection,
                             loader_kwargs=loader_kwargs, convert_difference_only=args.diff,
                             document_limit=args.limit)

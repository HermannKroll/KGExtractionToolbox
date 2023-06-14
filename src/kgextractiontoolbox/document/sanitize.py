import logging
import os
from argparse import ArgumentParser
from shutil import copy

from kgextractiontoolbox.backend.models import Document
from kgextractiontoolbox.document.document import TaggedDocument, get_doc_format, DocFormat
from kgextractiontoolbox.document.extract import read_pubtator_documents, read_tagged_documents
from kgextractiontoolbox.document.regex import ILLEGAL_CHAR


def filter_and_sanitize(in_file: str, out_file: str, filter_ids, logger=logging, ignore_tags=True):
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w+") as f:
        for n, doc in enumerate(read_pubtator_documents(in_file)):
            try:
                tdoc = TaggedDocument(doc, ignore_tags=ignore_tags)
            except:
                logger.debug(f"ignored {n}th document, unable to parse")
                continue
            if tdoc.id in filter_ids:
                f.write(Document.create_pubtator(tdoc.id, tdoc.title, tdoc.abstract) + "\n")


def sanitize(input_dir_or_file, output_dir=None, delete_mismatched=False, logger=logging):
    """
    Removes all "|" characters from document files and cast out files lacking abstracts.
    :param input_dir_or_file: Input directory containing document files or single document file
    :param output_dir: Directory to output the sanitized files to. Default: operate on input_dir
    :param delete_mismatched: If set to true, files without abstract will be deleted from input_dir
    :return: (list of ignored files, list of sanitized files)
    """
    ignored_files = []
    sanitized_files = []
    if not output_dir:
        output_dir = os.path.dirname(input_dir_or_file) if os.path.isfile(input_dir_or_file) else input_dir_or_file

    for path, file in read_tagged_documents(input_dir_or_file, yield_paths=True):
        if not file or not file.abstract:
            ignored_files.append(path)
            if delete_mismatched:
                os.remove(path)
        else:
            new_filename = os.path.join(output_dir, os.path.basename(path))
            if not ".txt" == new_filename[-4:]:
                new_filename += ".txt"
                sanitized_files.append(path)
            if ILLEGAL_CHAR.search(file.title + file.abstract) or get_doc_format(open(path), path) != DocFormat.PUBTATOR:
                sanitized_files.append(path)
                with open(new_filename, "w+") as nf:
                    nf.write(Document.create_pubtator(file.id, file.title, file.abstract) + "\n")
            else:
                if not input_dir_or_file == output_dir:
                    copy(path, new_filename)
    return ignored_files, sanitized_files


def main():
    parser = ArgumentParser(description="Sanitize Pubtator documents removing illegal characters and removing "
                                        "misformatted")
    parser.add_argument("input", help="Directory with PubTator files or PubTator file", metavar="IN_DIR")
    parser.add_argument("-o", "--output", help="Output directory. Works on Input directory if not set.")
    parser.add_argument("-d", "--delete-misform", help="Delete misformatted files in input directory",
                        action='store_true')
    args = parser.parse_args()
    sanitize(args.input, args.output if args.output else None, args.delete_misform)


if __name__ == "__main__":
    main()

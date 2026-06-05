import json
import os
from argparse import ArgumentParser

from kgextractiontoolbox.document.document import get_doc_format, DocFormat, is_doc_file
from kgextractiontoolbox.document.regex import DOCUMENT_ID, TAG_DOCUMENT_ID


def get_document_ids(path: str):
    ids = set()
    if os.path.isdir(path):
        for fn in os.listdir(path):
            if is_doc_file(fn):
                ids.update(get_document_ids(os.path.join(path, fn)))
    else:
        with open(path) as f:
            docformat = get_doc_format(f, path)
            if docformat == DocFormat.PUBTATOR:
                for line in f:
                    ids.update(int(x) for x in DOCUMENT_ID.findall(line))
                    # search only for tag ids if no title lines were found before
                    if len(ids) == 0:
                        ids.update(int(x) for x in TAG_DOCUMENT_ID.findall(line))
            elif docformat == DocFormat.SINGLE_JSON:
                json_data = json.loads(f.read())
                if "id" in json_data:
                    ids.add(json_data["id"])
                elif "source_id" in json_data:
                    ids.add(json_data["source_id"])
                else:
                    raise ValueError('JSON documents must contain "id" or "source_id"')
            elif docformat == DocFormat.COMPOSITE_JSON:
                ids |= {doc["id"] if "id" in doc else doc["source_id"] for doc in json.load(f)}
            elif docformat == DocFormat.JSON_LINE:
                for line in f:
                    if not line.strip():
                        continue
                    json_data = json.loads(line)
                    ids.add(json_data["id"] if "id" in json_data else json_data["source_id"])
    return ids


def count_documents(path):
    """
    Count PubTator documents in a directory or in a file.
    :param path: Path to directory or file
    :return: Number of distinct document IDs
    """
    return len(get_document_ids(path))


def main():
    parser = ArgumentParser()
    parser.add_argument("input", help="PubTator file", metavar="FILE")
    args = parser.parse_args()
    print("Found {} documents".format(count_documents(args.input)))


if __name__ == "__main__":
    main()

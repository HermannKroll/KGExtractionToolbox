import logging
from argparse import ArgumentParser

from spacy.lang.en import English

from kgextractiontoolbox.document.count import count_documents
from kgextractiontoolbox.document.document import TaggedDocument
from kgextractiontoolbox.document.extract import read_pubtator_documents
from kgextractiontoolbox.extraction.extraction_utils import filter_document_sentences_without_tags


def count_document_sentences(file: str):
    logging.info(f'Analyzing documents in: {file}')
    spacy_nlp = English()  # just the language with no model
    spacy_nlp.add_pipe("sentencizer")
    # Prepare files

    doc_count = count_documents(file)
    logging.info('{} documents counted'.format(doc_count))

    tagged_docs = []
    for doc_content in read_pubtator_documents(file):
        doc = TaggedDocument(doc_content, spacy_nlp=spacy_nlp)
        tagged_docs.append(doc)

    sentence_count = sum([len(doc.sentence_by_id) for doc in tagged_docs])
    logging.info(f'Found {sentence_count} sentences')

    doc2sentences, doc2tags = filter_document_sentences_without_tags(doc_count, file, spacy_nlp)
    tag_count = sum([len(tags) for doc_id, tags in doc2tags.items()])
    sentence_count = sum([len(sents) for doc_id, sents in doc2sentences.items()])
    logging.info(f'Found {tag_count} tags')
    logging.info(f'Found {sentence_count} sentences with at least two entities')


def main():
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)

    parser = ArgumentParser()
    parser.add_argument("input", help="Document input file", metavar="FILE")
    args = parser.parse_args()

    count_document_sentences(file=args.input)


if __name__ == "__main__":
    main()

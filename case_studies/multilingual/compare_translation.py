import logging
import re
from argparse import ArgumentParser

from spacy.lang.en import English

from kgextractiontoolbox.document.count import count_documents
from kgextractiontoolbox.document.document import TaggedDocument
from kgextractiontoolbox.document.extract import read_pubtator_documents
from kgextractiontoolbox.extraction.extraction_utils import filter_document_sentences_without_tags

EN_ABSTRACT = "1"
DEEPL_ABSTRACT = "2"

COMPLEX_REGEX_PUNCTUATION = re.compile(r'[,.;|&:?!]+', re.IGNORECASE)
COMPLEX_REGEX_WORDS = re.compile(r'[^\w](and|or|that|which|who|what|because|de|thus|hence)+[^\w]', re.IGNORECASE)


def check_sent_is_complex(phrase: str):
    if not phrase:
        return False
    # remove tailing punctuation
    while COMPLEX_REGEX_PUNCTUATION.match(phrase[-1]):
        phrase = phrase[:-1]
        if not phrase:
            return False
    phrase = f' {phrase} '

    if COMPLEX_REGEX_PUNCTUATION.search(phrase) or COMPLEX_REGEX_WORDS.search(phrase):
        return True
    else:
        return False


def count_document_sentences(file: str):
    logging.info(f'Analyzing documents in: {file}')
    spacy_nlp = English()  # just the language with no model
    spacy_nlp.add_pipe("sentencizer")
    # Prepare files

    logging.info(f'Read file: {file}')
    doc_count = count_documents(file)
    logging.info('{} documents counted'.format(doc_count))

    english_docs, translated_docs = [], []
    for doc_content in read_pubtator_documents(file):
        doc = TaggedDocument(doc_content, spacy_nlp=spacy_nlp)
        if str(doc.id)[-1] == EN_ABSTRACT:
            english_docs.append(doc)
        else:
            translated_docs.append(doc)

    for label, tagged_docs in [("English", english_docs), ("Translated", translated_docs)]:
        doc_ids = set([d.id for d in tagged_docs])
        logging.info('==' * 60)
        logging.info(f'Document type: {label}')
        sentence_count = sum([len(doc.sentence_by_id) for doc in tagged_docs])
        logging.info(f'Found {len(doc_ids)} documents')
        logging.info(f'Found {sentence_count} sentences')

        doc2sentences, doc2tags = filter_document_sentences_without_tags(len(tagged_docs), file, spacy_nlp)
        # Only select sent and tags for these documents
        doc2sentences = {d: s for d, s in doc2sentences.items() if d in doc_ids}
        doc2tags = {d: s for d, s in doc2tags.items() if d in doc_ids}

        tag_count = sum([len(tags) for doc_id, tags in doc2tags.items()])
        sentence_w2e_count = sum([len(sents) for doc_id, sents in doc2sentences.items()])
        # NER tags are upper case (for Stanza) -> EL not
        ner_count = len([t for _, tags in doc2tags.items() for t in tags if t.ent_type == t.ent_type.upper()])
        el_count = len([t for _, tags in doc2tags.items() for t in tags if t.ent_type != t.ent_type.upper()])
        logging.info(f'Found {tag_count} tags in sum ({ner_count} NER + {el_count} EL)')
        logging.info(f'Found {sentence_w2e_count} sentences with at least two entities')
        complex_sent_count = len(
            [s for d in tagged_docs for s in d.sentence_by_id.values() if check_sent_is_complex(s.text.strip())])
        logging.info(f'Found {complex_sent_count} complex sentences ({complex_sent_count / sentence_count}%)')

    logging.info('==' * 60)


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

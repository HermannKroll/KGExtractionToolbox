import logging
import re
from argparse import ArgumentParser
from typing import List

from kgextractiontoolbox.extraction.loading.load_openie_extractions import read_stanford_openie_input, OPENIE_TUPLE

COMPLEX_REGEX_PUNCTUATION = re.compile(r'[,.;|&:?!]+', re.IGNORECASE)
COMPLEX_REGEX_WORDS = re.compile(r'[^\w](and|or|that|which|who|what|because|de|thus|hence)+[^\w]', re.IGNORECASE)
COMPLEX_NOUN_PHRASE_WORDS = re.compile(r'[^\w](of|for|as|on|in|from|to|by)+[^\w]', re.IGNORECASE)


def check_is_complex(phrase: str):
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


def check_is_noun_phrase_too_long(noun_phrase: str, sentence_len: int, sentence_complex: bool):
    if COMPLEX_NOUN_PHRASE_WORDS.search(noun_phrase):
        return True
    if sentence_complex and (len(noun_phrase) / sentence_len) >= 0.2:
        return True
    elif not sentence_complex and (len(noun_phrase) / sentence_len) >= 0.5:
        return True
    else:
        return False


def analyze_openie_tuples(tuples: List[OPENIE_TUPLE]):
    logging.info('Analyzing tuples...')
    doc_ids = set()
    complex_subjects, complex_objects, complex_sentences = 0, 0, 0
    tuple_count = 0
    for t in tuples:
        if not t.subj or not t.pred or not t.obj:
            continue
        tuple_count += 1
        doc_ids.add(t.doc_id)
        subj, pred_org, pred_lemma, obj, sent = t.subj, t.pred, t.pred_lemma, t.obj, t.sent
        sentence_len = len(sent)

        sentence_complex = check_is_complex(sent)
        if sentence_complex:
            complex_sentences += 1

        if check_is_complex(subj) or check_is_noun_phrase_too_long(subj, sentence_len, sentence_complex):
            complex_subjects += 1
        if check_is_complex(obj) or check_is_noun_phrase_too_long(obj, sentence_len, sentence_complex):
            complex_objects += 1

    logging.info('==' * 60)
    logging.info('Open IE Tuple Analysis Report:')
    logging.info(f'#Document IDs: {len(doc_ids)}')
    logging.info(f'#Tuples:       {tuple_count}')
    logging.info('--'*60)
    logging.info(f'#Complex subjects:  {complex_subjects} ({complex_subjects / tuple_count}%)')
    logging.info(f'#Complex objects:   {complex_objects} ({complex_objects / tuple_count}%)')
    logging.info(f'#Complex sentences: {complex_sentences} ({complex_sentences / tuple_count}%)')
    logging.info('==' * 60)


def main():
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)

    parser = ArgumentParser()
    parser.add_argument("input", help="OpenIE TSV output file", metavar="FILE")
    args = parser.parse_args()

    logging.info(f'Reading OpenIE TSV file: {args.input}')
    doc_ids, openie_tuples = read_stanford_openie_input(args.input)
    analyze_openie_tuples(openie_tuples)


if __name__ == "__main__":
    main()

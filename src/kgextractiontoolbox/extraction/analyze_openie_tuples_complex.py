import itertools
import logging
import multiprocessing
import re
from argparse import ArgumentParser
from collections import defaultdict
from typing import List
import nltk
import spacy

from kgextractiontoolbox.extraction.loading.load_openie_extractions import read_stanford_openie_input, OPENIE_TUPLE
from kgextractiontoolbox.progress import Progress
from kgextractiontoolbox.util.multiprocessing.ConsumerWorker import ConsumerWorker
from kgextractiontoolbox.util.multiprocessing.Worker import Worker, SHUTDOWN_SIGNAL

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


# See table:
# https://universaldependencies.org/u/pos/

def check_has_conjunction(phrase, tokens, sentence):
    for token in tokens:
        if token.pos_ in ["CCONJ"]:
            return True
    return False


def check_has_adposition(phrase, tokens, sentence):
    for token in tokens:
        if token.pos_ in ["ADP"]:
            return True
    return False


def check_only_nouns(phrase: str, tokens, sentence):
    for token in tokens:
        if token.pos_ not in ["NOUN", "PROPN", "PART", "DET", "NUM", "PUNCT"]:
            return False
    return True


def check_only_nouns_pronouns(phrase: str, tokens, sentence):
    for token in tokens:
        if token.pos_ not in ["NOUN", "PROPN", "PRON", "PART", "DET", "NUM", "PUNCT"]:
            return False
    return True


def check_only_nouns_pronouns_adjectives(phrase: str, tokens, sentence):
    for token in tokens:
        if token.pos_ not in ["NOUN", "PROPN", "PRON", "PART", "DET", "NUM", "PUNCT", "ADJ"]:
            return False
    return True


def check_has_verbs(phrase: str, tokens, sentence):
    for token in tokens:
        if token.pos_ in ["VERB"]:
            return True
    return False


def larger_than_20_of_sentence(phrase, tokens, sentence):
    if len(phrase) / len(sentence) > 0.2:
        return True
    return False


def larger_than_30_of_sentence(phrase, tokens, sentence):
    if len(phrase) / len(sentence) > 0.3:
        return True
    return False


def larger_than_40_of_sentence(phrase, tokens, sentence):
    if len(phrase) / len(sentence) > 0.4:
        return True
    return False


def larger_than_50_of_sentence(phrase, tokens, sentence):
    if len(phrase) / len(sentence) > 0.5:
        return True
    return False


def larger_than_60_of_sentence(phrase, tokens, sentence):
    if len(phrase) / len(sentence) > 0.6:
        return True
    return False


def larger_than_70_of_sentence(phrase, tokens, sentence):
    if len(phrase) / len(sentence) > 0.7:
        return True
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

    eval_functions = {
        "has_conjunction": check_has_conjunction,
        "has_adposition": check_has_adposition,
        "has_nouns_only": check_only_nouns,
        "has_nouns_pronouns_only": check_only_nouns_pronouns,
        "has_nouns_pronouns_adjectives_only": check_only_nouns_pronouns_adjectives,
        "has_verb": check_has_verbs,
        "lt_20_of_sentence": larger_than_20_of_sentence,
        "lt_30_of_sentence": larger_than_30_of_sentence,
        "lt_40_of_sentence": larger_than_40_of_sentence,
        "lt_50_of_sentence": larger_than_50_of_sentence,
        "lt_60_of_sentence": larger_than_60_of_sentence,
        "lt_70_of_sentence": larger_than_70_of_sentence,
    }
    sorted_eval_func = sorted(list([k for k in eval_functions]))
    count_dict = {k: {"s": 0, "o": 0} for k in eval_functions}
    count_dict["complex_arguments"] = {"s": 0, "o": 0}
    count_dict["complex_sentences"] = {"t": 0}

    # Todo needs: python3 -m spacy download en_core_web_sm
    nlp = spacy.load("en_core_web_sm")


    tuple_count = 0
    doc_ids = set()
    total = len(tuples)
    progress = Progress(total, print_every=10, text="Analysing OpenIE tuples")
    progress.start_time()

    for i, t in enumerate(tuples): 
        progress.print_progress(i)
        if not t.subj.strip() or not t.pred.strip() or not t.obj.strip():
            continue
        tuple_count += 1
        doc_ids.add(t.doc_id)

        subj, obj, sent = t.subj.strip(), t.obj.strip(), t.sent.strip()
        sentence_len = len(sent)
        subj_tokens = nlp(subj)
        obj_tokens = nlp(obj)

        # check all eval functions
        for k, func in eval_functions.items():
            if func(subj, subj_tokens, sent):
                count_dict[k]["s"] += 1
            if func(obj, obj_tokens, sent):
                count_dict[k]["o"] += 1

        sentence_complex = check_is_complex(sent)
        if sentence_complex:
            count_dict["complex_sentences"]["t"] += 1

        if check_is_complex(subj) or check_is_noun_phrase_too_long(subj, sentence_len, sentence_complex):
            count_dict["complex_arguments"]["s"] += 1
        if check_is_complex(obj) or check_is_noun_phrase_too_long(obj, sentence_len, sentence_complex):
            count_dict["complex_arguments"]["o"] += 1

    logging.info('==' * 60)
    logging.info('Open IE Tuple Analysis Report:')
    logging.info(f'#Document IDs: {len(doc_ids)}')
    logging.info(f'#Tuples:       {tuple_count}')
    logging.info('--' * 60)
    logging.info(
        f'#Complex subjects:  {count_dict["complex_arguments"]["s"]} ({count_dict["complex_arguments"]["s"] / tuple_count}%)')
    logging.info(
        f'#Complex objects:   {count_dict["complex_arguments"]["o"]} ({count_dict["complex_arguments"]["o"] / tuple_count}%)')
    logging.info(
        f'#Complex sentences: {count_dict["complex_sentences"]["t"]} ({count_dict["complex_sentences"]["t"] / tuple_count}%)')
    logging.info('--' * 60)

    for k in sorted_eval_func:
        logging.info('--' * 60)
        logging.info(f'{k} subjects: {count_dict[k]["s"]} ({count_dict[k]["s"] / tuple_count}%)')
        logging.info(f'{k} objects: {count_dict[k]["o"]} ({count_dict[k]["o"] / tuple_count}%)')
    logging.info('--' * 60)

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

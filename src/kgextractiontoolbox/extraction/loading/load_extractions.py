import hashlib
import logging
from collections import namedtuple
from datetime import datetime
from typing import List

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Predication, Sentence
from kgextractiontoolbox.progress import print_progress_with_eta

MAX_SENTENCE_LENGTH = 1000

# A list of words to ignore in OpenIE extractions
TOKENS_TO_IGNORE = {'with', 'by', 'of', 'from', 'to', 'than', 'as', 'on', 'at', 'may', 'in', 'can', 'more', 'less',
                    'into', 'well', 'for'}

PRED = namedtuple('Predication', ['doc_id', 'subj', 'pred', 'pred_cleaned', 'obj', 'conf', 'sent', 's_id', 's_str',
                                  's_type', 'o_id', 'o_str', 'o_type'])


def text_to_md5hash(text: str) -> str:
    """
    Converts a arbitrary string to a md5 hash
    :param text: some string
    :return: a string consisting of md5 hexdigest
    """
    return hashlib.md5(text.encode()).hexdigest()


def load_sentences_with_hashes(document_collection: str):
    """
    Loads all sentences with the corresponding hashes from the database
    :param document_collection: the document collection
    :return: a dict mapping md5hashes to a sentence id
    """
    logging.info('Retrieving known sentences for collection...')
    session = Session.get()
    sentence_q = session.query(Sentence.id, Sentence.md5hash).filter(
        Sentence.document_collection == document_collection)
    hash2sentence = {}
    for sent in sentence_q:
        hash2sentence[sent[1]] = sent[0]
    logging.info(f'{len(hash2sentence)} sentences retrieved')
    return hash2sentence


def load_highest_sentence_id() -> int:
    """
    Finds the highest sentence id in the sentence table
    :return: highest used sentence id
    """
    session = Session.get()
    return Sentence.query_highest_sentence_id(session)


def clean_sentence_str(sentence: str) -> str:
    """
    Postgres is not able to handle sentences containing a null-terminating char or characters starting by backslash x
    This method cleans the sentences (replace all \ by \\)
    :param sentence: the sentence to clean
    :return: a cleaned version of the sentence
    """
    if len(sentence) > MAX_SENTENCE_LENGTH:
        sentence = sentence[0:MAX_SENTENCE_LENGTH]
    return sentence.replace('\t', ' ').replace('\n', ' ').replace('\\', '\\\\')


def clean_predications(tuples_cleaned: List[PRED], collection, extraction_type):
    """
    Cleans a list of predications based on a set of filters
    :param tuples_cleaned: a list of PRED tuples
    :param collection: the document collection
    :param extraction_type: extraction type like OpenIE or PathIE
    :return: a list of sentence objects to insert, a list of predication values to insert
    """
    hash2sentence = load_sentences_with_hashes(collection)
    sentid2hash = {v: k for k, v in hash2sentence.items()}
    inserted_sentence_ids = set([k for k in sentid2hash.keys()])

    last_highest_sentence_id = load_highest_sentence_id()
    logging.info(f'Last highest sentence_id was: {last_highest_sentence_id}')
    logging.info(f'Querying duplicates from database (collection: {collection} and extraction type: {extraction_type})')

    logging.info('Check duplicates only within this session...')
    duplicate_check = set()

    last_highest_sentence_id += 1
    len_tuples = len(tuples_cleaned)
    logging.info('Inserting {} tuples to database...'.format(len_tuples))
    start_time = datetime.now()
    predication_values = []
    sentence_values = []
    for i, p in enumerate(tuples_cleaned):
        sentence_txt = p.sent.replace('\n', '')
        # Todo: dirty fix here empty id or ner id
        if p.s_id == '-' or p.o_id == '-' or not p.s_id.strip() or not p.o_id.strip():
            continue
        # Clean dirty predicates (only one character)
        if len(p.pred_cleaned) < 2:
            continue

        sent_hash = text_to_md5hash(sentence_txt)
        key = (p.doc_id, p.s_id, p.s_type, p.pred_cleaned, p.o_id, p.o_type, sent_hash)
        if key in duplicate_check:
            continue
        duplicate_check.add(key)

        sentence_id = -1
        if sent_hash in hash2sentence:
            sentence_id = hash2sentence[sent_hash]
        # no sentence_id found
        else:
            sentence_id = last_highest_sentence_id
            hash2sentence[sent_hash] = sentence_id
            last_highest_sentence_id += 1

        predication_values.append(dict(
            document_id=p.doc_id,
            document_collection=collection,
            subject_id=p.s_id,
            subject_str=clean_sentence_str(p.s_str),
            subject_type=p.s_type,
            predicate_org=p.pred.strip(),
            predicate=p.pred_cleaned,
            object_id=p.o_id,
            object_str=clean_sentence_str(p.o_str),
            object_type=p.o_type,
            confidence=p.conf,
            sentence_id=sentence_id,
            extraction_type=extraction_type
        ))

        # check whether the sentence was inserted before
        if sentence_id not in inserted_sentence_ids:
            inserted_sentence_ids.add(sentence_id)
            sentence_values.append((dict(
                id=sentence_id,
                document_collection=collection,
                text=clean_sentence_str(sentence_txt),
                md5hash=sent_hash)))

        print_progress_with_eta("Preparing data...", i, len_tuples, start_time)
    return predication_values, sentence_values


def clean_and_load_predications_into_db(tuples_cleaned: List[PRED], collection, extraction_type):
    """
     insert a list of cleaned tuples into the database (bulk insert)
     does not check for collisions
     :param tuples_cleaned: a list of PRED tuples
     :param collection: the document collection
     :param extraction_type: extraction type like OpenIE or PathIE
     :return: Nothing
     """
    predication_values, sentence_values = clean_predications(tuples_cleaned, collection, extraction_type)
    logging.info(f'{len(predication_values)} predications and {len(sentence_values)} sentences to insert...')
    session = Session.get()
    Sentence.bulk_insert_values_into_table(session, sentence_values, check_constraints=False)
    Predication.bulk_insert_values_into_table(session, predication_values, check_constraints=False)

import argparse
import csv
import logging
from collections import namedtuple, defaultdict
from datetime import datetime
from enum import Enum
from itertools import islice
from typing import List, Tuple

import nltk
from nltk.corpus import wordnet

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Tag, Document
from kgextractiontoolbox.extraction.loading.load_extractions import PRED, TOKENS_TO_IGNORE, \
    clean_and_load_predications_into_db
from kgextractiontoolbox.extraction.versions import OPENIE_EXTRACTION
from kgextractiontoolbox.progress import print_progress_with_eta

OPENIE_TUPLE = namedtuple("OpenIETuple", ['doc_id', 'subj', 'pred', 'pred_lemma', 'obj', 'conf', 'sent'])


class OpenIEEntityFilterMode(Enum):
    NO_ENTITY_FILTER = "no_entity_filter"
    PARTIAL_ENTITY_FILTER = "partial_entity_filter"
    EXACT_ENTITY_FILTER = "exact_entity_filter"
    ONLY_SUBJECT_EXACT = "only_subject_exact"

    def __str__(self):
        return self.value

    @staticmethod
    def to_str_list():
        return list(map(str, OpenIEEntityFilterMode))


def read_stanford_openie_input(openie_file: str):
    """
    reads a OpenIE output file created by main.py and transforms the data into a list of
    OpenIE tuples
    :param openie_file: OpenIE output file created by main.py
    :return: a set of document ids, a list of OpenIE tuples
    """
    doc_ids = set()
    tuples_cached = []
    logging.info('Reading OpenIE input...')
    # open the input open ie file
    with open(openie_file, 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        # read all lines for a single doc
        for row in islice(reader, 1, None):
            c = row
            o_t = OPENIE_TUPLE(int(c[0].strip()), c[1].strip(), c[2].strip(), c[3].strip(), c[4].strip(), c[5].strip(),
                               clean_sentence(c[6]).strip())
            doc_ids.add(o_t.doc_id)
            tuples_cached.append(o_t)
    return doc_ids, tuples_cached


def clean_sentence(sentence: str):
    """
    Clean OpenIE sentences by replacing the bracket shortcuts back to valid brackets
    :param sentence: a sentence
    :return: cleaned sentence
    """
    s = sentence.replace('-LRB- ', '(')
    s = s.replace('-LSB- ', '(')
    s = s.replace(' -RRB-', ')')
    s = s.replace(' -RSB-', ')')
    return s


def get_subject_and_object_entities(doc_tags, ie_sub: str, ie_obj: str, entity_filter: OpenIEEntityFilterMode):
    """
    Computes a list of entities which are included in the subject as well as a list of entities
    included in the object
    :param doc_tags: a dictionary mapping a doc_id to tags
    :param ie_sub: the subject
    :param ie_obj: the object
    :param entity_filter: the entity filter mode: Exact (IE arg must match entity str), Partial (entity is partially included), None = no entity checking
    :return: a list of entities (ent_str, ent_id, ent_type) included in subj, list of entities in obj
    """
    if entity_filter == OpenIEEntityFilterMode.NO_ENTITY_FILTER:
        return [(ie_sub, ie_sub, "Unknown")], [(ie_obj, ie_obj, "Unknown")]

    # default not hit
    subs_included = []
    objs_included = []

    if not ie_sub or not ie_obj:
        return [], []

    # compute lower case with empty spaces
    if ie_sub[-1].isalpha():
        sub_text = ' {} '.format(ie_sub.lower())
    else:
        sub_text = ' {} '.format(ie_sub.lower()[0:-1])

    if ie_obj[-1].isalpha():
        obj_text = ' {} '.format(ie_obj.lower())
    else:
        obj_text = ' {} '.format(ie_obj.lower()[0:-1])

    # check if an entity occurs within the sentence
    for ent_id, ent_str, ent_type in doc_tags:
        # skip empty mesh ids
        if ent_id == '-1' or ent_id == '':
            continue

        if entity_filter == OpenIEEntityFilterMode.PARTIAL_ENTITY_FILTER:
            if ent_str in sub_text:
                s_t = (ent_str, ent_id, ent_type)
                subs_included.append(s_t)
            if ent_str in obj_text:
                o_t = (ent_str, ent_id, ent_type)
                objs_included.append(o_t)
        elif entity_filter == OpenIEEntityFilterMode.EXACT_ENTITY_FILTER:
            if ent_str.strip() == sub_text.strip():
                s_t = (ent_str, ent_id, ent_type)
                subs_included.append(s_t)
            if ent_str.strip() == obj_text.strip():
                o_t = (ent_str, ent_id, ent_type)
                objs_included.append(o_t)
        elif entity_filter == OpenIEEntityFilterMode.ONLY_SUBJECT_EXACT:
            if ent_str.strip() == sub_text.strip():
                s_t = (ent_str, ent_id, ent_type)
                subs_included.append(s_t)

    if entity_filter == OpenIEEntityFilterMode.ONLY_SUBJECT_EXACT:
        objs_included = [(ie_obj, ie_obj, "Unknown")]

    return subs_included, objs_included


def load_tags_for_doc_ids(doc_ids: List[int], collection: str) -> {str: List[Tuple[str, str, str]]}:
    """
    loads the database entity tags for a list of doc_ids
    :param doc_ids: sequence of doc_ids
    :param collection: document collection
    :return: a dict mapping document ids to tuples (ent_id, ent_str, ent_type)
    """
    session = Session.get()
    # get all tags for the given doc_ids
    query = session.query(Tag.document_id, Tag.ent_id, Tag.ent_str, Tag.ent_type)
    query = query.filter(Tag.document_collection == collection)
    query = query.filter(Tag.document_id.in_(doc_ids))

    doc2tags = defaultdict(list)
    results = session.execute(query)
    counter = 0
    for row in results:
        ent_str = ' {} '.format(row[2]).strip().lower()
        t = (row[1], ent_str, row[3])
        doc2tags[int(row[0])].append(t)
        counter += 1
    logging.info('{} tags load from db'.format(counter))
    return doc2tags


def clean_tuple_predicate_based(t: PRED, keep_original_predicate=False, filter_predicate_str=False,
                                swap_passive_voice=False, keep_be_and_have=True):
    """
    cleans the tuple based on predicate rules
    1. remove unnecessary tokens
    2. passive voice -> active voice
    3. remove be and have predicates
    4. apply stripping to all fields
    :param t: a tuple (named tuple PRED expected, PRED.pred_cleaned is expected to be the a lemmatized predicate)
    :param keep_original_predicate: if true the original predicate of the OpenIE method is used without further cleaning
    :param filter_predicate_str: should the predicate str be cleaned to only keep verb phrases?
    :param swap_passive_voice: should passive voice be swapped to active voice?
    :param keep_be_and_have: should be and have predicates be kept?
    :return: a cleaned tuple (PRED)
    """
    if keep_original_predicate and (filter_predicate_str or swap_passive_voice or not keep_be_and_have):
        raise ValueError('If keep_original_predicate is set, then no verb phrase filter options are available')

    if keep_original_predicate:
        return PRED(t.doc_id, t.subj.strip(), t.pred.strip(), t.pred.strip(), t.obj.strip(), t.conf, t.sent,
                    t.s_id, t.s_str.strip(), t.s_type.strip(), t.o_id, t.o_str.strip(), t.o_type.strip())

    # no cleaning is required
    if not filter_predicate_str and not swap_passive_voice and keep_be_and_have:
        return t

    # pred_lemma is stored in the pred_cleaned field
    pred_lemma = t.pred_cleaned
    tokens = pred_lemma.split(' ')

    if keep_be_and_have:
        # ignore tuples containing just 'be' and 'have'
        if pred_lemma == 'be' or pred_lemma == 'have':
            return None

    if not filter_predicate_str:
        pred_cleaned = ' '.join(pred_lemma.split())
    else:
        pred_cleaned = ''
        # remove be and have if multiple tokens are included
        tokens_remain = []
        for tok in tokens:
            # remove unnecessary phrases
            if tok in TOKENS_TO_IGNORE:
                continue

            # do not keep be and have if not desired
            if not keep_be_and_have and (tok == "be" or tok == "have"):
                continue

            # allow the not token
            if tok != "not":
                # remove adjectives and adverbs
                syns = wordnet.synsets(tok)
                if len(syns) > 0 and syns[0].pos() in ['a', 's', 'r']:
                    continue

            tokens_remain.append(tok)
        pred_cleaned = ' '.join([str(tok.strip()) for tok in tokens_remain])

    if swap_passive_voice:
        fact_sentence = '{} {} {}.'.format(t.subj, t.pred, t.obj)
        fact_sentence_tokens = nltk.word_tokenize(fact_sentence)
        pos_tags = nltk.pos_tag(fact_sentence_tokens)

        # check if particpe past was detected
        participe_past_detected = len([p_t for p_t in pos_tags if p_t[1] == "VBN"]) > 0

        # check for active and passive voice
        if ('be' in tokens and participe_past_detected) or ('by' in t.pred and participe_past_detected):
            pred_cleaned = pred_cleaned.replace('be', '').replace('by', '')
            # passive means we have to change the direction of the tuple
            t_sub, t_s_txt, t_s_id, t_s_type = t.subj, t.s_str, t.s_id, t.s_type
            subj, s_txt, s_id, s_type = t.obj, t.o_str, t.o_id, t.o_type
            obj, o_txt, o_id, o_type = t_sub, t_s_txt, t_s_id, t_s_type

            return PRED(t.doc_id, subj.strip(), t.pred.strip(), pred_cleaned.strip(), obj.strip(), t.conf, t.sent,
                        s_id, s_txt.strip(), s_type.strip(), o_id, o_txt.strip(), o_type.strip())

    return PRED(t.doc_id, t.subj.strip(), t.pred.strip(), pred_cleaned.strip(), t.obj.strip(), t.conf, t.sent,
                t.s_id, t.s_str.strip(), t.s_type.strip(), t.o_id, t.o_str.strip(), t.o_type.strip())


def clean_open_ie(doc_ids, openie_tuples: [OPENIE_TUPLE], collection,
                  entity_filter: OpenIEEntityFilterMode,
                  extraction_type=OPENIE_EXTRACTION,
                  keep_original_predicate=False,
                  filter_predicate_str=False, swap_passive_voice=False, keep_be_and_have=True):
    """
    cleans the open ie tuples by:
    1. applying an entity filter (keep only facts about entities)
    2. cleaning predicates (remove be and have & change passive voice to active voice & remove tokens see above)
    :param doc_ids: a set of document ids
    :param openie_tuples: a list of openie tuples
    :param collection: document collection where the id's stem from (to retrieve entities from the database)
    :param entity_filter: the entity filter mode: Exact (IE arg must match entity str), Partial (entity is partially included), None = no entity checking
    :param extraction_type: extraction type (OPENIE_EXTRACTION (default) or OPENIE6_EXTRACTION)
    :param keep_original_predicate: if true the original predicate of the OpenIE method is used without further cleaning
    :param filter_predicate_str: should the predicate str be cleaned to only keep verb phrases?
    :param swap_passive_voice: should passive voice be swapped to active voice?
    :param keep_be_and_have: should be and have predicates be kept?
    :return:
    """
    if keep_original_predicate and (filter_predicate_str or swap_passive_voice or not keep_be_and_have):
        raise ValueError('If keep_original_predicate is set, then no verb phrase filter options are available')

    logging.info('Beginning cleaning step...')
    tuples_cached = openie_tuples
    logging.info('{} OpenIE tuples read...'.format(len(tuples_cached)))
    if len(doc_ids) == 0:
        logging.info("No documents to check - stopping")
        return

    if entity_filter != OpenIEEntityFilterMode.NO_ENTITY_FILTER:
        logging.info("Retrieving tags from database for {} doc_ids...".format(len(doc_ids)))
        doc2tags = load_tags_for_doc_ids(doc_ids, collection)
        document_ids = set(doc2tags.keys())
    else:
        session = Session.get()
        document_ids = Document.get_document_ids_for_collection(session, collection)
        doc2tags = defaultdict()
    logging.info(f'{len(document_ids)} document ids are present for collection: {collection}')

    logging.info('Cleaning tuples...')
    i = 0
    len_tuples = len(tuples_cached)
    # tuples with just include tagged entities
    tuples_with_ent = []
    # don't include the same tuple twice for a single sentence
    already_included = set()
    # go trough all cached triples
    start_time = datetime.now()
    skipped_tuples_because_doc_missing = 0
    for openie_t in tuples_cached:
        if entity_filter != OpenIEEntityFilterMode.NO_ENTITY_FILTER:
            if openie_t.doc_id not in doc2tags:
                skipped_tuples_because_doc_missing += 1
                continue
            doc_tags = doc2tags[openie_t.doc_id]
        else:
            # skip tuple because document is not in document ids
            if openie_t.doc_id not in document_ids:
                skipped_tuples_because_doc_missing += 1
                continue
            doc_tags = []
        # go trough all detected entities in the subject and object part of the open ie triple
        sub_ents, obj_ents = get_subject_and_object_entities(doc_tags, openie_t.subj, openie_t.obj, entity_filter)
        for s_txt, s_id, s_type in sub_ents:
            for o_txt, o_id, o_type in obj_ents:
                # check if tuple is already extracted for sentence
                key = (openie_t.doc_id, s_id, s_type, o_id, o_type, openie_t.pred, openie_t.sent)
                if key not in already_included:
                    t = PRED(openie_t.doc_id, openie_t.subj, openie_t.pred, openie_t.pred_lemma, openie_t.obj,
                             openie_t.conf, openie_t.sent, s_id, s_txt, s_type, o_id, o_txt, o_type)
                    tuples_with_ent.append(t)
                    already_included.add(key)

        print_progress_with_eta(f"Applying filter {entity_filter} to tuples...", i, len_tuples, start_time)
        i += 1

    logging.info("{} facts remaining...".format(len(tuples_with_ent)))
    # now clean predicates
    tuples_cleaned = []
    len_tuples = len(tuples_with_ent)
    start_time = datetime.now()
    passive_changed = 0
    for i, t in enumerate(tuples_with_ent):
        t_cleaned = clean_tuple_predicate_based(t,
                                                keep_original_predicate=keep_original_predicate,
                                                filter_predicate_str=filter_predicate_str,
                                                swap_passive_voice=swap_passive_voice,
                                                keep_be_and_have=keep_be_and_have)
        # subject changed
        if t[1] != t_cleaned[1]:
            passive_changed += 1
        tuples_cleaned.append(t_cleaned)
        print_progress_with_eta("Cleaning (predicates)", i, len_tuples, start_time)

    if swap_passive_voice:
        logging.info('Changed {} times passive voices (subj <-> obj swapped)'.format(passive_changed))
    logging.warning(f'{skipped_tuples_because_doc_missing} tuples ignored because their documents are missing')
    logging.info('Cleaning finished...')

    clean_and_load_predications_into_db(tuples_cleaned, collection, extraction_type=extraction_type)


def load_openie_tuples(input_file: str, document_collection: str, entity_filter: OpenIEEntityFilterMode,
                       extraction_type: str = OPENIE_EXTRACTION, keep_original_predicate=False,
                       filter_predicate_str=False, swap_passive_voice=False, keep_be_and_have=True):
    """
    Load OpenIE tuples from a TSV file
    :param input_file: the path to the tsv file
    :param document_collection: the document collection
    :param entity_filter: the entity filter mode
    :param extraction_type: extraction type to load tuples into the db
    :param keep_original_predicate: if true the original predicate of the OpenIE method is used without further cleaning
    :param filter_predicate_str: should the predicate str be cleaned to only keep verb phrases?
    :param swap_passive_voice: should passive voice be swapped to active voice?
    :param keep_be_and_have: should be and have predicates be kept?
    :return: None
    """
    doc_ids, openie_tuples = read_stanford_openie_input(input_file)

    logging.info('==' * 60)
    logging.info('Settings:')
    logging.info(f'keep_original_predicate: {keep_original_predicate}')
    logging.info(f'filter_predicate_str: {filter_predicate_str}')
    logging.info(f'swap_passive_voice: {swap_passive_voice}')
    logging.info(f'keep_be_and_have: {keep_be_and_have}')
    logging.info('==' * 60)
    clean_open_ie(doc_ids, openie_tuples, document_collection, entity_filter, extraction_type=extraction_type,
                  keep_original_predicate=keep_original_predicate,
                  filter_predicate_str=filter_predicate_str, swap_passive_voice=swap_passive_voice,
                  keep_be_and_have=keep_be_and_have)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help='OpenIE export file (exported by main.py / pipeline.py')
    parser.add_argument("-c", "--collection", required=True,
                        help='document collection to which the document ids belong')
    parser.add_argument("-et", "--extraction_type", help=f"extraction type",
                        default=OPENIE_EXTRACTION)
    parser.add_argument("--entity_filter", default=OpenIEEntityFilterMode.PARTIAL_ENTITY_FILTER,
                        help="the entity filter mode", choices=OpenIEEntityFilterMode.to_str_list())
    parser.add_argument("--filter_predicate_str", default=False, action="store_true",
                        help="Should the predicate be filtered to retain only verb phrases?")
    parser.add_argument("--swap_passive_voice", default=False, action="store_true",
                        help="Swap passive voice to active voice")
    parser.add_argument("--ignore_be_and_have", default=False, action="store_true",
                        help="Ignore be and have verb phrases")
    parser.add_argument("--keep_original_predicate", default=False, action="store_true",
                        help="The original predicate is kept without further cleaning or lemmatizing")

    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)
    load_openie_tuples(args.input, args.collection, OpenIEEntityFilterMode(args.entity_filter), args.extraction_type,
                       keep_original_predicate=args.keep_original_predicate,
                       filter_predicate_str=args.filter_predicate_str,
                       swap_passive_voice=args.swap_passive_voice,
                       keep_be_and_have=not args.ignore_be_and_have)
    logging.info('finished')


if __name__ == "__main__":
    main()

import argparse
import logging
from collections import defaultdict
from datetime import datetime
from typing import List, Tuple

import fasttext
from scipy.spatial.distance import cosine
from sqlalchemy import update

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Predication
from kgextractiontoolbox.cleaning.relation_vocabulary import RelationVocabulary
from kgextractiontoolbox.progress import print_progress_with_eta


def transform_predicate(predicate: str):
    """
    Stems the predicate by two rules
    ends with s -> remove s
    ends with ed -> remove d
    :param predicate:
    :return:
    """
    if predicate.endswith('s'):
        return predicate[:-1]
    if predicate.endswith('ed'):
        return predicate[:-1]
    return predicate


def is_predicate_equal_to_vocab(predicate: str, vocab_term: str) -> bool:
    """
    fast regex check for vocab terms that starts or ends with a *
    Quickly checks, whether the predicate is a direct match to the vocab term
    :param predicate: the predicate
    :param vocab_term: a vocab term (may starting and/or ending with *)
    :return: true if both are equal
    """
    if vocab_term.startswith('*') and predicate.endswith(vocab_term[1:]):
        return True
    if vocab_term.endswith('*') and predicate.startswith(vocab_term[:-1]):
        return True
    if vocab_term.startswith('*') and vocab_term.endswith('*') and vocab_term[1:-1] in predicate:
        return True
    if vocab_term == predicate:
        return True
    return False


def filter_predicate_list(predicates_with_count, min_predicate_threshold):
    """
    Filters a list with predicates and counts by a minimum count threshold
    :param predicates_with_count: list of tuples (pred, count_of_pred)
    :param min_predicate_threshold: how often should a predicate occur at minimum (0.1 means that the predicate appears in at least 10% of all extractions)
    :return: a list of filtered predicates (pred_count >= min_predicate_threshold * all_count)
    """
    predicates = []
    pred_sum = sum([x[1] for x in predicates_with_count])
    min_count = int(min_predicate_threshold * pred_sum)
    logging.info(f'Minimum threshold for predicates is: {min_count}')
    for pred, count in predicates_with_count:
        if count >= min_count:
            predicates.append(pred)
    return predicates


def canonicalize_predicates_with_word2vec_model(model, predicates: [str], vocab_predicates: {str: [str]}) \
        -> (List[Tuple[str, str]], List[Tuple[str, str, float]]):
    """
    The distance between each predicate and all predicates of the vocabulary are computed. The predicate is assigned
    to the closed predicate in the room. Cosine Similarity is used.
    :param model: fasttext Word Embedding
    :param predicates: a list of predicates
    :param vocab_predicates: the vocabulary as a dict mapping predicates to their synonyms
    :return: a list of best matches, a list of mappings including the distances
    """
    output_results = []
    vocab_vectors = []
    for goal_relation, v_preds in vocab_predicates.items():
        k_os = goal_relation.replace('*', '')
        vocab_vectors.append((goal_relation, transform_predicate(goal_relation),
                              model.get_word_vector(transform_predicate(k_os))))
        for v_p in v_preds:
            v_p_os = v_p.replace('*', '')
            vocab_vectors.append((goal_relation, transform_predicate(v_p),
                                  model.get_word_vector(transform_predicate(v_p_os))))

    start_time = datetime.now()
    best_matches = {}
    i = 0
    task_size = len(predicates) * len(vocab_vectors)
    for p in predicates:
        p_transformed = transform_predicate(p)
        vec = model.get_word_vector(p_transformed)
        best_match = None
        min_distance = 1.0
        for p_v_idx, (goal_relation, p_pred, p_v) in enumerate(vocab_vectors):
            current_distance = abs(cosine(vec, p_v))
            output_results.append((p, p_pred, current_distance))
            if is_predicate_equal_to_vocab(p, p_pred):
                # identity is best match
                min_distance = 0.0
                best_match = (goal_relation, min_distance)
                break
            if not best_match or current_distance < min_distance:
                min_distance = current_distance
                best_match = (goal_relation, min_distance)

            print_progress_with_eta('computing distances...', i, task_size, start_time)
            i += 1

        if p in best_matches:
            raise ValueError('p should not be twice in predicates (duplicate found)')
        best_matches[p] = (best_match[0], best_match[1])

    return best_matches, output_results


def canonicalize_predicates_without_word2vec_model(predicates: [str], vocab_predicates: {str: [str]}) \
        -> (List[Tuple[str, str]], List[Tuple[str, str, float]]):
    """
    Canonicalize predicates based on the relation vocabulary only (no word2vec model is needed)
    :param predicates: a list of predicates
    :param vocab_predicates: the relation vocabulary
    :return: a list of best matches, a list of mappings including the distances (1.0 = fit, 0.0 = no match)
    """

    output_results = []
    start_time = datetime.now()
    best_matches = {}
    i = 0
    vocab_entries = []
    for goal_relation, v_preds in vocab_predicates.items():
        vocab_entries.append((goal_relation, goal_relation))
        for v_pred in v_preds:
            vocab_entries.append((goal_relation, transform_predicate(v_pred)))
    task_size = len(predicates) * len(vocab_entries)
    for p in predicates:
        best_match = None

        for p_v_idx, (goal_relation, p_pred) in enumerate(vocab_entries):
            if is_predicate_equal_to_vocab(p, p_pred):
                output_results.append((p, p_pred, 1.0))
                # identity is best match
                min_distance = 0.0
                best_match = (goal_relation, min_distance)
                break
            else:
                output_results.append((p, p_pred, 0.0))
            print_progress_with_eta('mapping predicates...', i, task_size, start_time)
            i += 1
        if p in best_matches:
            raise ValueError('p should not be twice in predicates (duplicate found)')

        if best_match:
            best_matches[p] = (best_match[0], best_match[1])
    return best_matches, output_results


def compute_mapping_plan(predicates: [str], vocab_predicates: {str: [str]}, output_file: str = None, model=None):
    """
    Compute the mapping plan for the predicate list against the relation vocabulary
    if a word2vec model is given, the procedure will compute the distances
    if no word2vec model is given, the mapping is produced by direct matches
    :param predicates: a list of predicates
    :param vocab_predicates: the relation vocabulary
    :param output_file: path to a file in which the distances and mapping will be written (optional)
    :param model: a fasttext word2vec model (optional)
    :return: the best matches as a list
    """
    if model:
        best_matches, output_results = canonicalize_predicates_with_word2vec_model(model, predicates, vocab_predicates)
    else:
        best_matches, output_results = canonicalize_predicates_without_word2vec_model(predicates, vocab_predicates)

    if output_file:
        with open(output_file, 'wt') as f:
            f.write('predicate\trelation\tdistance')
            output_results.sort(key=lambda x: (x[0], x[2]), reverse=True)
            for p, p_pred, current_distance in output_results:
                f.write('\n{}\t{}\t{}'.format(p, p_pred, current_distance))

    return best_matches


def canonicalize_predicates(best_matches: {str: (str, float)}, min_distance_threshold: float, document_collection: str,
                            predication_id_minimum: int = None):
    """
    Canonicalizes Predicates by resolving synonymous predicates. This procedure updates the database
    :param best_matches: dictionary which maps a predicate to a canonicalized predicate and a distance score
    :param min_distance_threshold: all predicates that have a match with a distance blow minimum threshold distance are canonicalized
    :param document_collection: the document collection to canonicalize
    :param predication_id_minimum: only predication ids above this will be updated (note: statistics will be computed on the whole table)
    :return: None
    """
    session = Session.get()
    start_time = datetime.now()

    logging.info('Finalizing update plan...')
    pred_can2preds = defaultdict(set)
    for pred, (pred_canonicalized, min_distance) in best_matches.items():
        if min_distance > min_distance_threshold:
            pred_canonicalized = None
        pred_can2preds[pred_canonicalized].add(pred)

    if document_collection:
        logging.info(f'Only updating predications from document collection: {document_collection}')

    if predication_id_minimum:
        logging.info(f'Only updating predications with ids >= {predication_id_minimum}')

    logging.info(f'Execute {len(pred_can2preds)} update jobs...')
    task_size = len(pred_can2preds)
    for i, (pred_canonicalized, preds) in enumerate(pred_can2preds.items()):
        print_progress_with_eta('updating...', i, task_size, start_time, print_every_k=1)
        stmt = update(Predication).where(Predication.predicate.in_(preds))
        if document_collection:
            stmt = stmt.where(Predication.document_collection == document_collection)
        if predication_id_minimum:
            stmt = stmt.where(Predication.id >= predication_id_minimum)
        stmt = stmt.values(relation=pred_canonicalized)
        session.execute(stmt)

    logging.info('Committing updates...')
    session.commit()


def canonicalize_predication_table(relation_vocabulary: RelationVocabulary, document_collection=None,
                                   word2vec_model_file=None,
                                   output_distances=None, min_distance_threshold=0.4, min_predicate_threshold=0.0001,
                                   predication_id_minimum: int = None):
    """
    Canonicalizes the predicates against the relation vocabulary and updates the database
    :param relation_vocabulary: the predicate vocabulary
    :param document_collection: the document collection to canonicalize
    :param word2vec_model_file: a Word2Vec model file
    :param output_distances: a file where the predicate mapping will be stored
    :param min_predicate_threshold: how often should a predicate occur at minimum (0.1 means that the predicate appears in at least 10% of all extractions)
    :param min_distance_threshold: all predicates that have a match with a distance blow minimum threshold distance are canonicalized
    :param predication_id_minimum: only predication ids above this will be updated (note: statistics will be computed on the whole table)
    :return: None
    """
    if word2vec_model_file:
        logging.info('Loading Word2Vec model...')
        model = fasttext.load_model(word2vec_model_file)
    else:
        model = None

    relation_vocabulary = relation_vocabulary.relation_dict
    logging.info('{} predicates in vocabulary'.format(len(relation_vocabulary)))
    logging.info('Retrieving predicates from db...')
    predicates_with_count = Predication.query_predicates_with_count(session=Session.get(),
                                                                    document_collection=document_collection)
    logging.info(f'{len(predicates_with_count)} predicates with count retrieved')
    logging.info('Filtering with minimum count...')
    predicates = filter_predicate_list(predicates_with_count, min_predicate_threshold)
    logging.info('{} predicates obtained'.format(len(predicates)))
    logging.info('Matching predicates...')
    best_matches = compute_mapping_plan(predicates, relation_vocabulary, output_distances, model=model)
    logging.info('Canonicalizing predicates...')
    canonicalize_predicates(best_matches, min_distance_threshold, document_collection,
                            predication_id_minimum=predication_id_minimum)
    logging.info('Finished')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--word2vec_model", required=False, help='fasttext word2vec model file')
    parser.add_argument("--output_distances", required=False, help='tsv export for mapping distances')
    parser.add_argument('--relation_vocab', required=True, help='Path to a relation vocabulary (json file)')
    parser.add_argument('--min_distance', required=False, help='Minimum distance in the vector space',
                        default=0.4, type=float)
    parser.add_argument('--min_predicate_threshold', required=False,
                        help='Minimum number of occurrences for predicates', default=0.0001, type=float)
    parser.add_argument("-c", "--collection", default=None, help="The document collection of interest")
    parser.add_argument("--predicate_id_minimum", default=None, type=int, required=False,
                        help="only predication ids above this will be updated (note: statistics will be computed on the whole table)")
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)

    relation_vocab = RelationVocabulary()
    relation_vocab.load_from_json(args.relation_vocab)
    canonicalize_predication_table(word2vec_model_file=args.word2vec_model,
                                   output_distances=args.output_distances,
                                   relation_vocabulary=relation_vocab,
                                   min_distance_threshold=args.min_distance,
                                   min_predicate_threshold=args.min_predicate_threshold,
                                   document_collection=args.collection,
                                   predication_id_minimum=args.predicate_id_minimum)


if __name__ == "__main__":
    main()

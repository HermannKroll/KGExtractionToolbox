import argparse
import logging
from collections import defaultdict
from datetime import datetime
from typing import List, Tuple

import fasttext
import numpy
import scipy.cluster.hierarchy
from scipy.spatial.distance import pdist
from sqlalchemy import update

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Predication
from kgextractiontoolbox.cleaning.canonicalize_predicates import filter_predicate_list, canonicalize_predicates
from kgextractiontoolbox.progress import print_progress_with_eta


def cluster_canonicalize_predicates_with_word2vec_model(model, predicates: [str], threshold: float) \
        -> (List[Tuple[str, str]], List[Tuple[str, str, float]]):
    """
    The distance between each predicate and all predicates of the vocabulary are computed. The predicate is assigned
    to the closed predicate in the room. Cosine Similarity is used.
    :param model: fasttext Word Embedding
    :param predicates: a list of predicates
    :param threshold: threshold for the clustering based method
    :return: a list of best matches, a list of mappings including the distances
    """
    start_time = datetime.now()

    task_size = len(predicates)
    print(predicates)
    logging.info(f'Embedding {task_size} predicates...')
    X = numpy.empty((len(predicates), len(model.get_word_vector(predicates[0]))), numpy.float32)

    for i, p in enumerate(predicates):
        X[i, :] = model.get_word_vector(p)
        print_progress_with_eta('computing distances...', i, task_size, start_time)

    logging.info('Performing clustering...')
    logging.info('--' * 60)
    dist = pdist(X, metric="cosine")
    cluster_data = scipy.cluster.hierarchy.linkage(dist)
    labels = scipy.cluster.hierarchy.fcluster(cluster_data, t=threshold, criterion='distance') - 1
    clusters = [[] for i in range(max(labels) + 1)]

    for i in range(len(labels)):
        clusters[labels[i]].append(predicates[i])

    logging.info(f'{len(clusters)} clusters computed for {len(predicates)} different verb phrases (t = {threshold})')
    logging.info(f'found: {clusters}')
    logging.info('--' * 60)

    best_matches = {}
    for cluster in clusters:
        # Always canonicalize predicates to the first predicate in the cluster
        for p in cluster:
            # 0.0 distance -> Gold match because same cluster
            best_matches[p] = (cluster[0], 0.0)

    return best_matches


def canonicalize_predication_table_with_clustering(threshold: float,
                                                   document_collection=None,
                                                   word2vec_model_file=None,
                                                   min_predicate_threshold=0.0001,
                                                   predication_id_minimum: int = None):
    """
    Canonicalizes the predicates against the relation vocabulary and updates the database
    :param document_collection: the document collection to canonicalize
    :param word2vec_model_file: a Word2Vec model file
    :param min_predicate_threshold: how often should a predicate occur at minimum (0.1 means that the predicate appears in at least 10% of all extractions)
    :param predication_id_minimum: only predication ids above this will be updated (note: statistics will be computed on the whole table)
    :param threshold: threshold for the clustering based method
    :return: None
    """
    logging.info(f'Loading Word2Vec model from {word2vec_model_file}')
    model = fasttext.load_model(word2vec_model_file)

    logging.info('Retrieving predicates from db...')
    predicates_with_count = Predication.query_predicates_with_count(session=Session.get(),
                                                                    document_collection=document_collection)
    logging.info(f'{len(predicates_with_count)} predicates with count retrieved')
    logging.info('Filtering with minimum count...')
    predicates = filter_predicate_list(predicates_with_count, min_predicate_threshold)
    logging.info('{} predicates obtained'.format(len(predicates)))
    logging.info('Clustering predicates...')
    best_matches = cluster_canonicalize_predicates_with_word2vec_model(model, predicates, threshold=threshold)

    logging.info('Canonicalizing predicates...')
    canonicalize_predicates(best_matches, min_distance_threshold=1.0, document_collection=document_collection,
                            predication_id_minimum=predication_id_minimum)
    logging.info('Finished')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--word2vec_model", required=True, help='fasttext word2vec model file')
    # 0.429 CESI default value
    parser.add_argument('--threshold', required=False, help='Threshold for the clustering based method',
                        default=0.429, type=float)
    parser.add_argument('--min_predicate_threshold', required=False,
                        help='Minimum number of occurrences for predicates', default=0.0001, type=float)
    parser.add_argument("-c", "--collection", default=None, help="The document collection of interest")
    parser.add_argument("--predicate_id_minimum", default=None, type=int, required=False,
                        help="only predication ids above this will be updated (note: statistics will be computed on the whole table)")
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)

    canonicalize_predication_table_with_clustering(threshold=args.threshold,
                                                   word2vec_model_file=args.word2vec_model,
                                                   min_predicate_threshold=args.min_predicate_threshold,
                                                   document_collection=args.collection,
                                                   predication_id_minimum=args.predicate_id_minimum)


if __name__ == "__main__":
    main()

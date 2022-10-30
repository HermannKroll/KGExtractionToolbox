import argparse
import logging
from datetime import datetime
from typing import List, Tuple

import fasttext
import numpy
import scipy.cluster.hierarchy
from scipy.spatial.distance import pdist

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Predication
from kgextractiontoolbox.cleaning.canonicalize_predicates import filter_predicate_list
from kgextractiontoolbox.progress import print_progress_with_eta


def analyze_cluster_canonicalize_predicates_with_word2vec_model(model, predicates: [str]) \
        -> (List[Tuple[str, str]], List[Tuple[str, str, float]]):
    """
    Analyze an unsupervised clustering based canonicalization procedure for verb phrases
    Therefore, thresholds between 0.1 and 1.0 are tested (and 0.429 - default in CESI)
    :param model: fasttext Word Embedding
    :param predicates: a list of predicates
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
    for t in [0.1, 0.2, 0.3, 0.4, 0.429, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        dist = pdist(X, metric="cosine")
        cluster_data = scipy.cluster.hierarchy.linkage(dist)
        labels = scipy.cluster.hierarchy.fcluster(cluster_data, t=t, criterion='distance') - 1
        clusters = [[] for i in range(max(labels) + 1)]

        for i in range(len(labels)):
            clusters[labels[i]].append(predicates[i])

        logging.info(f'{len(clusters)} clusters computed for {len(predicates)} different verb phrases (t = {t})')
        logging.info(f'found: {clusters}')
        logging.info('--' * 60)


def analyze_canonicalize_predication_table_with_clustering(document_collection=None,
                                                           word2vec_model_file=None,
                                                           min_predicate_threshold=0.0001):
    """
    Analyze a Clustering Approach for Verb Phrase Canonicalization
    :param document_collection: the document collection to canonicalize
    :param word2vec_model_file: a Word2Vec model file
    :param min_predicate_threshold: how often should a predicate occur at minimum (0.1 means that the predicate appears in at least 10% of all extractions)
    :return: None
    """
    logging.info('==' * 60)
    logging.info('==' * 60)
    logging.info(f'Used collection: {document_collection}')
    logging.info(f'Loading Word2Vec model from {word2vec_model_file}')
    model = fasttext.load_model(word2vec_model_file)

    logging.info('Retrieving predicates from db...')
    predicates_with_count = Predication.query_predicates_with_count(session=Session.get(),
                                                                    document_collection=document_collection)
    logging.info(f'{len(predicates_with_count)} predicates with count retrieved')
    logging.info('Filtering with minimum count...')
    predicates = filter_predicate_list(predicates_with_count, min_predicate_threshold)
    logging.info('{} predicates obtained'.format(len(predicates)))
    logging.info('Analyzing predicate cluters...')
    analyze_cluster_canonicalize_predicates_with_word2vec_model(model, predicates)
    logging.info('Finished')
    logging.info('==' * 60)
    logging.info('==' * 60)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--word2vec_model", required=True, help='fasttext word2vec model file')
    parser.add_argument('--min_predicate_threshold', required=False,
                        help='Minimum number of occurrences for predicates', default=0.0001, type=float)
    parser.add_argument("-c", "--collection", default=None, help="The document collection of interest")
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)

    analyze_canonicalize_predication_table_with_clustering(word2vec_model_file=args.word2vec_model,
                                                           min_predicate_threshold=args.min_predicate_threshold,
                                                           document_collection=args.collection)


if __name__ == "__main__":
    main()

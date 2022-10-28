import logging
from argparse import ArgumentParser

from kgextractiontoolbox.entitylinking.tagging.vocabulary import Vocabulary


def analyse_entity_linking_vocabulary(vocab: Vocabulary):
    """
    This function takes a vocabulary and prints statistics about it via Logging
    :param vocab: a vocabularry
    :return: None
    """

    logging.info('=='*60)
    logging.info('Vocabulary Analysis:')
    logging.info(f'{vocab.count_distinct_entities()} distinct entities')
    logging.info(f'{vocab.count_distinct_terms()} distinct terms')
    logging.info('=='*60)


def main():
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)

    parser = ArgumentParser()
    parser.add_argument("input", help="Vocabulary to analyse", metavar="FILE")
    args = parser.parse_args()

    logging.info(f'Loading vocabulary from: {args.input}')
    vocab = Vocabulary(args.input)
    vocab.load_vocab(expand_terms=False)
    analyse_entity_linking_vocabulary(vocab)


if __name__ == "__main__":
    main()

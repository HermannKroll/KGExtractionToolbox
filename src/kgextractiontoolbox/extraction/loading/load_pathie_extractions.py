import argparse
import csv
import logging
from itertools import islice

from kgextractiontoolbox.extraction.loading.load_extractions import PRED, clean_and_load_predications_into_db
from kgextractiontoolbox.extraction.versions import PATHIE_EXTRACTION, PATHIE_STANZA_EXTRACTION


def read_pathie_extractions_tsv(pathie_tsv_file: str, load_symmetric=True):
    """
    Reads data from a PathIE output file (created by main.py)
    :param pathie_tsv_file: PathIE output (is a tsv file)
    :param load_symmetric: should the extraction be loaded symmetricly (s,p,o) and (o,p,s)?
    :return: a list of PRED tuples
    """
    extractions = []
    with open(pathie_tsv_file, 'rt') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in islice(reader, 1, None):
            try:
                doc_id, e1_id, e1_str, e1_type, pred, pred_lemma, e2_id, e2_str, e2_type, conf, sentence = row
                p = PRED(doc_id, "", pred, pred_lemma, "", conf, sentence, e1_id, e1_str, e1_type, e2_id, e2_str,
                         e2_type)
                extractions.append(p)
                if load_symmetric:
                    # flip triple
                    p = PRED(doc_id, "", pred, pred_lemma, "", 1.0, sentence, e2_id, e2_str,
                             e2_type, e1_id, e1_str, e1_type)
                    extractions.append(p)

            except ValueError:
                logging.warning(f'skipping tuple: {row}')
    return extractions


def load_pathie_extractions(pathie_tsv_file: str, document_collection, extraction_type, load_symmetric=True):
    """
    Wrapper to load PathIE extractions into the database
    uses fast mode if postgres connection
    fallback: slower insertion
    :param pathie_tsv_file: PathIE tsv file extraction path
    :param document_collection: the document collection
    :param extraction_type: PathIE extraction type
    :param load_symmetric: should the extraction be loaded symmetricly (s,p,o) and (o,p,s)?
    :return:
    """
    logging.info(f'Reading extraction from {pathie_tsv_file}...')
    predications = read_pathie_extractions_tsv(pathie_tsv_file, load_symmetric=load_symmetric)
    logging.info('{} extractions read'.format(len(predications)))
    logging.info('Inserting {} predications'.format(len(predications)))
    clean_and_load_predications_into_db(predications, document_collection, extraction_type)
    logging.info('finished')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help='PathIE output file (created by main.py)')
    parser.add_argument("-c", "--collection", required=True, help='document collection to which the ids belong')
    parser.add_argument("-et", "--extraction_type", help="PathIE|PathIEStanza", choices=[PATHIE_EXTRACTION,
                                                                                         PATHIE_STANZA_EXTRACTION],
                        default=PATHIE_EXTRACTION)
    parser.add_argument("--not_symmetric", required=False, action="store_true",
                        help="PathIE extractions will be mirrored (s,p,o) to (o,p,s). "
                             "This option will disable the mirroring")

    args = parser.parse_args()
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)

    load_pathie_extractions(args.input, args.collection, args.extraction_type, args.not_symmetric)


if __name__ == "__main__":
    main()

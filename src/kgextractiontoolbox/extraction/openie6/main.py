import argparse
import csv
import json
import logging
import os
import subprocess
from datetime import datetime
from spacy.lang.en import English
from time import sleep
from typing import List

from kgextractiontoolbox.config import NLP_CONFIG
from kgextractiontoolbox.document.count import count_documents
from kgextractiontoolbox.document.document import TaggedDocument
from kgextractiontoolbox.document.extract import read_pubtator_documents
from kgextractiontoolbox.extraction.extraction_utils import filter_document_sentences_without_tags
from kgextractiontoolbox.extraction.loading.load_openie_extractions import OPENIE_TUPLE
from kgextractiontoolbox.progress import print_progress_with_eta


def openie6_read_extractions(openie6_output: str) -> List[OPENIE_TUPLE]:
    """
    Reads the OpenIE6 output format
    :param openie6_output: the OpenIE6 output file
    :return: a list of OpenIE tuples
    """
    tuples = []
    doc_ids = set()
    # nlp = spacy.load('en_core_web_sm', disable=['parser', 'ner'])
    spacy_nlp = English()  # just the language with no model
    spacy_nlp.add_pipe("lemmatizer", config={"mode": "lookup"})
    spacy_nlp.initialize()
    # open the input OpenIE6 file
    with open(openie6_output, 'r') as f:
        # read all lines for a single doc
        doc_id, sentence_txt = 0, ""
        for line in f:
            try:
                if not line or line == '\n':
                    continue
                if not line.startswith('0.') and not line.startswith('1.'):
                    doc_id, sentence_txt = line.split('.', maxsplit=1)
                    if doc_id == "0fake0":
                        doc_id = None
                        continue
                    doc_id = int(doc_id)
                    sentence_txt = sentence_txt.strip()
                else:
                    if not doc_id or not sentence_txt:
                        continue
                    confidence, extraction = line.strip().split(": (", maxsplit=1)
                    if extraction.count(';') < 2:
                        logging.info(f'Skip extraction because no object was found: {extraction}')
                    # split by ';'
                    subj_txt, pred_txt, obj_txt = extraction.split(';', maxsplit=2)
                    obj_txt = obj_txt.strip()[:-1] # remove closing bracket
                    pred_lemma = ' '.join([token.lemma_ for token in spacy_nlp(pred_txt)])
                    ex_tuple = OPENIE_TUPLE(int(doc_id), subj_txt, pred_txt, pred_lemma, obj_txt, confidence,
                                            sentence_txt)
                    tuples.append(ex_tuple)
                doc_ids.add(doc_id)
            except ValueError:
                logging.debug("Error during extraction")
    return tuples


def openie6_extract_tuples(openie6_output_file: str, extraction_output: str):
    """
    Extracts the OpenIE6 tuples from the original format to our OpenIE format
    :param openie6_output_file: the OpenIE6 output file
    :param extraction_output: path to our OpenIE output file
    :return: None
    """
    logging.info('Converting OpenIE6 output...')
    tuples = openie6_read_extractions(openie6_output_file)

    with open(extraction_output, 'wt') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['document id',
                         'subject',
                         'predicate',
                         'predicate lemmatized',
                         'object',
                         'confidence',
                         'sentence'])
        for t in tuples:
            writer.writerow([str(x) for x in t])


def openie6_generate_openie6_input(doc2sentences: {int: List[str]}, openie6_input: str):
    """
    Generates the OpenIE6 input file. Writes a .txt with one sentence per line
    :param doc2sentences: a dict mapping a document it to a list of sentences
    :param openie6_input: the OpenIE6 input file path
    :return: None
    """
    doc_size = len(doc2sentences)
    logging.info('Writing {} documents as OpenIE 6 input...'.format(doc_size))
    start_time = datetime.now()
    with open(openie6_input, 'wt') as f_out:
        f_out.write("0fake0. This is a test.\n")
        for idx, (doc_id, sentences) in enumerate(doc2sentences.items()):
            for sent in sentences:
                f_out.write('{}. {}.\n'.format(doc_id, sent))
            print_progress_with_eta(f'Writing {doc_size} documents as OpenIE 6 input...', idx, doc_size, start_time)
    logging.info('Conversion finished')


def openie6_invoke_toolkit(openie6_dir: str, input_file: str, output_file: str):
    """
    Invokes the OpenIE6 toolkit to generate fact extractions
    :param openie6_dir: the OpenIE6 tool directory
    :param input_file: the OpenIE6 input file
    :param output_file: the output file
    :return: None
    """
    start = datetime.now()
    run_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run.sh")
    sp_args = ["/bin/bash", "-c", "{} {} {} {}".format(run_script, openie6_dir, input_file, output_file)]
    process = subprocess.Popen(sp_args, cwd=openie6_dir)
    logging.info('Waiting for OpenIE6 to terminate...')
    while process.poll() is None:
        sleep(1)
    logging.info(f'Process finished in {datetime.now() - start}s')


def openie6_run(document_file, output, config=NLP_CONFIG, no_entity_filter=False):
    """
    Initializes OpenIE6. Will generate the corresponding input file, reads the output and converts it to our
    internal OpenIE format
    :param document_file: input file with documents to generate
    :param output: the output file
    :param config: the nlp config
    :param no_entity_filter: if true only sentences with two tags will be processed by OpenIE
    :return: None
    """
    # Read config
    with open(config) as f:
        conf = json.load(f)
        openie6_dir = conf["openie6"]

    # Prepare files
    doc_count = count_documents(document_file)
    logging.info('{} documents counted'.format(doc_count))

    logging.info('Init spacy nlp...')
    spacy_nlp = English()  # just the language with no model
    spacy_nlp.add_pipe("sentencizer")
    doc2sentences = {}
    if no_entity_filter:
        for document_content in read_pubtator_documents(document_file):
            doc = TaggedDocument(from_str=document_content, spacy_nlp=spacy_nlp)
            if doc:
                doc2sentences[doc.id] = [s.text for s in doc.sentence_by_id.values()]
    else:
        doc2sentences, doc2tags = filter_document_sentences_without_tags(doc_count, document_file, spacy_nlp)
        doc_count = len(doc2tags)

    openie6_input_file = f'{output}_pubtator'
    openie6_raw_extractions = f'{output}_extractions'
    if doc_count == 0:
        print('no files to process - stopping')
    else:
        start = datetime.now()
        # Process output
        openie6_generate_openie6_input(doc2sentences, openie6_input_file)
        # invoke OpenIE 6
        openie6_invoke_toolkit(openie6_dir, openie6_input_file, openie6_raw_extractions)
        # extract tuples
        openie6_extract_tuples(openie6_raw_extractions, output)
        print(f'removing temp file: {openie6_input_file}')
        os.remove(openie6_input_file)
        print(f'removing temp file: {openie6_raw_extractions}')
        os.remove(openie6_raw_extractions)
        print(" done in {}".format(datetime.now() - start))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Document file with tags")
    parser.add_argument("output", help="OpenIE results will be stored here")
    parser.add_argument("--no_entity_filter", action="store_true",
                        default=False, required=False, help="Does not filter sentences by tags")
    parser.add_argument("--config", default=NLP_CONFIG)
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)

    openie6_run(args.input, args.output, args.config, args.no_entity_filter)


if __name__ == "__main__":
    main()

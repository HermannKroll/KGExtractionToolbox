import argparse
import csv
import json
import logging
import multiprocessing
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from time import sleep

from spacy.lang.en import English

from kgextractiontoolbox.cleaning.relation_vocabulary import RelationVocabulary
from kgextractiontoolbox.config import NLP_CONFIG
from kgextractiontoolbox.document.count import count_documents
from kgextractiontoolbox.extraction.extraction_utils import filter_and_write_documents_to_tempdir
from kgextractiontoolbox.extraction.pathie.core import PathIEDependency, PathIEToken, pathie_extract_facts_from_sentence
from kgextractiontoolbox.progress import print_progress_with_eta

NUMBER_FIX_REGEX = re.compile(r"\d+,\d+")


def get_progress(out_corenlp_dir: str) -> int:
    """
    Get the current progress of the NLP tool
    :param out_corenlp_dir: reads the output dir and checks how many .json files have been created already
    :return: length of processed documents
    """
    hits = 0
    for fn in os.listdir(out_corenlp_dir):
        if fn.endswith('.json'):
            hits += 1
    return hits


def pathie_run_corenlp(core_nlp_dir: str, out_corenlp_dir: str, filelist_fn: str, worker_no: int):
    """
    Invokes the Stanford CoreNLP tool to process files
    :param core_nlp_dir: CoreNLP tool directory
    :param out_corenlp_dir: the output directory
    :param filelist_fn: the path of the filelist which files should be processed
    :param worker_no: number of parallel workers
    :return: None
    """
    start = datetime.now()
    with open(filelist_fn) as f:
        num_files = len(f.read().split("\n"))

    run_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run.sh")
    filelist_fn = os.path.join(os.path.dirname(os.path.abspath(filelist_fn)), os.path.basename(filelist_fn))
    sp_args = ["/bin/bash", "-c", "{} {} {} {} {}".format(run_script, core_nlp_dir, out_corenlp_dir, filelist_fn,
                                                          worker_no)]
    logging.info(f'Invoking Stanford CoreNLP with: {sp_args}')
    process = subprocess.Popen(sp_args, cwd=core_nlp_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    start_time = datetime.now()
    print_progress_with_eta('CoreNLP running...', 0, num_files, start_time, print_every_k=1)
    return_code = process.poll()
    while return_code is None:
        sleep(10)
        print_progress_with_eta('CoreNLP running...', get_progress(out_corenlp_dir), num_files, start_time,
                                print_every_k=1)
        return_code = process.poll()

    if return_code != 0:
        raise ValueError(f'CoreNLP returned code: {return_code}. (Did you add +x permissions to run.sh?)')

    sys.stdout.write("\rProgress: {}/{} ... done in {}\n".format(
        get_progress(out_corenlp_dir), num_files, datetime.now() - start,
    ))
    sys.stdout.flush()


def load_and_fix_json_nlp_data(json_path):
    """
    Loads and fixes a txt CoreNLP text json file
    :param json_path: path to json file
    :return: json object
    """
    with open(json_path, 'r') as f:
        json_fixed_lines = []
        for line in f:
            if NUMBER_FIX_REGEX.findall(line):
                json_fixed_lines.append(line.replace(',', '.', 1))
            else:
                json_fixed_lines.append(line)
        return json.loads(''.join(json_fixed_lines))


def process_json_file(doc_id, input_file, doc_tags, predicate_vocabulary: {str: [str]}):
    """
    Extracts facts out of a JSON file
    :param doc_id: document id
    :param input_file: JSON input file as a filename
    :param doc_tags: set of tags in the corresponding document
    :param predicate_vocabulary: the predicate vocabulary if special words are given
    :return: a list of extracted tuples
    """
    extracted_tuples = []
    json_data = load_and_fix_json_nlp_data(input_file)
    for sent in json_data["sentences"]:
        sent_dependencies = []
        for dep_json in sent["enhancedPlusPlusDependencies"]:
            sent_dependencies.append(PathIEDependency(int(dep_json["governor"]), int(dep_json["dependent"]),
                                                      dep_json["dep"]))

        sent_tokens = []
        for t in sent["tokens"]:
            sent_tokens.append(PathIEToken(t["originalText"], t["originalText"].lower(), t["before"], t["after"],
                                           int(t["index"]), int(t["characterOffsetBegin"]),
                                           int(t["characterOffsetEnd"]), t["pos"], t["lemma"]))

        extracted_tuples.extend(pathie_extract_facts_from_sentence(doc_id, doc_tags, sent_tokens, sent_dependencies,
                                                                   predicate_vocabulary=predicate_vocabulary))
    return extracted_tuples


def pathie_process_corenlp_output(out_corenlp_dir, amount_files, outfile, doc2tags,
                                  predicate_vocabulary: {str: [str]}):
    """
    Processes the CoreNLP output directory: iterates over all files and calls the process_json_file function
    :param out_corenlp_dir: CoreNLP output directory (dir of .json files)
    :param amount_files: amount of files
    :param outfile: filename where all extractions will be stored
    :param doc2tags: dict mapping doc ids to tags
    :param predicate_vocabulary: the predicate vocabulary if special words are given
    :return: None
    """
    tuples = 0
    start_time = datetime.now()
    with open(outfile, 'wt') as f_out:
        writer = csv.writer(f_out, delimiter='\t')
        writer.writerow(['document id', 'subject id', 'subject str', 'subject type', 'predicate',
                         'predicate lemmatized', 'object id', 'object str', 'object type',
                         'confidence', 'sentence'])
        for idx, filename in enumerate(os.listdir(out_corenlp_dir)):
            if filename.endswith('.json'):
                doc_id = int(filename.split('.')[0])
                extracted_tuples = process_json_file(doc_id, os.path.join(out_corenlp_dir, filename),
                                                     doc2tags[doc_id], predicate_vocabulary=predicate_vocabulary)
                tuples += len(extracted_tuples)
                for e_tuple in extracted_tuples:
                    writer.writerow([str(t) for t in e_tuple])
            print_progress_with_eta("extracting triples", idx, amount_files, start_time, print_every_k=1)
    logging.info('{} lines written'.format(tuples))


def pathie_process_corenlp_output_parallelized_worker(tasks: multiprocessing.Queue,
                                                      results: multiprocessing.Queue,
                                                      predicate_vocabulary: {str: [str]}):
    """
    Helper method to process the CoreNLP output in parallel
    :param tasks: the queue of tasks
    :param results: the queue the results will be put to
    :param predicate_vocabulary: the predicate vocabulary if special words are given
    :return: None
    """
    logging.debug('Worker processing the PathIE output started')
    extracted_tuples = []
    while tasks.qsize() > 0:
        try:
            task = tasks.get(timeout=1)
            if task is None:
                logging.debug('Nothing to stop - stop here')
                continue
            doc_id, filepath, doc_tags = task
            tuples = process_json_file(doc_id, filepath, doc_tags, predicate_vocabulary=predicate_vocabulary)
            if tuples:
                extracted_tuples.extend(tuples)
        except queue.Empty:
            logging.debug('Queue empty exception - waiting for new tasks or exit condition')
            sleep(0.1)
            continue
    results.put(extracted_tuples)
    logging.debug('Worker finished')


def pathie_process_corenlp_output_parallelized(out_corenlp_dir, amount_files, outfile, doc2tags,
                                               predicate_vocabulary: {str: [str]}, workers=1):
    """
    Parallelized version of the PathIE CoreNLP output processing steps
    :param out_corenlp_dir: the directory of the CoreNLP output
    :param amount_files: the number of files to show a progress
    :param outfile: the outfile where the extracted tuples will be written to
    :param doc2tags: dict mapping doc_ids to tags
    :param predicate_vocabulary: the predicate vocabulary if special words are given

    :param workers: the number of workers
    :return: None
    """
    if workers == 1:
        pathie_process_corenlp_output(out_corenlp_dir, amount_files, outfile, doc2tags,
                                      predicate_vocabulary=predicate_vocabulary)
    else:
        task_queue = multiprocessing.Queue()
        result_queue = multiprocessing.Queue()
        # init the task
        no_tasks = 0
        for idx, filename in enumerate(os.listdir(out_corenlp_dir)):
            if filename.endswith('.json'):
                filepath = os.path.join(out_corenlp_dir, filename)
                doc_id = int(filename.split('.')[0])
                doc_tags = doc2tags[doc_id]
                task_queue.put((doc_id, filepath, doc_tags))
                no_tasks += 1
        logging.info(f'{no_tasks} json documents to process...')
        # init the processes
        processes = []
        for i in range(0, workers):
            p = multiprocessing.Process(target=pathie_process_corenlp_output_parallelized_worker,
                                        args=(task_queue, result_queue, predicate_vocabulary))
            processes.append(p)
            p.start()

        logging.info('Collecting results...')
        with open(outfile, 'wt') as f_out:
            writer = csv.writer(f_out, delimiter='\t')
            writer.writerow(['document id', 'subject id', 'subject str', 'subject type', 'predicate',
                             'predicate lemmatized', 'object id', 'object str', 'object type',
                             'confidence', 'sentence'])
            for p in processes:
                extracted_tuples = result_queue.get()
                for e_tuple in extracted_tuples:
                    writer.writerow([str(t) for t in e_tuple])

        logging.info('Waiting for workers to terminate...')
        for p in processes:
            while p.is_alive():
                logging.debug('join thread')
                p.join(timeout=1)
        logging.info('Workers terminated - Results written')


def run_pathie(input, output, workdir=None, config=NLP_CONFIG,
               predicate_vocabulary: {str: [str]} = None, workers=1,
               consider_sections=False):
    """
    Runs PathIE based on Stanford CoreNLP toolkit
    :param input: pubtator input file
    :param output: pathie output file
    :param workdir: workdir (if none a temp dir will be created)
    :param config: NLP config
    :param predicate_vocabulary: the predicate vocabulary if special words are given
    :param workers: number of parallel workers
    :param consider_sections: Should document sections be considered for text generation?
    :return: None
    """
    # Read config
    with open(config) as f:
        conf = json.load(f)
        core_nlp_dir = conf["corenlp"]
    tmp_dir_created = False
    if workdir:
        temp_dir = workdir
    else:
        tmp_dir_created = True
        temp_dir = tempfile.mkdtemp()
    out_corenlp_dir = os.path.join(temp_dir, "output")
    temp_in_dir = os.path.join(temp_dir, "input")
    filelist_fn = os.path.join(temp_dir, "filelist.txt")
    if not os.path.isdir(temp_in_dir):
        os.mkdir(temp_in_dir)
    if not os.path.isdir(out_corenlp_dir):
        os.mkdir(out_corenlp_dir)
    logging.info('Working in: {}'.format(temp_dir))

    if workers == 1:
        logging.info('Init spacy nlp...')
        spacy_nlp = English()  # just the language with no model
        spacy_nlp.add_pipe("sentencizer")
    else:
        # will be created for each worker independently
        spacy_nlp = None

    logging.info('counting documents...')
    # Prepare files
    doc_count = count_documents(input)
    logging.info('{} documents counted'.format(doc_count))
    amount_files, doc2tags = filter_and_write_documents_to_tempdir(doc_count, input, temp_in_dir, filelist_fn,
                                                                   spacy_nlp, worker_count=workers,
                                                                   consider_sections=consider_sections)
    if amount_files == 0:
        print('no files to process - stopping')
    else:
        pathie_run_corenlp(core_nlp_dir, out_corenlp_dir, filelist_fn, worker_no=workers)
        print("Processing output ...", end="")
        start = datetime.now()
        # Process output
        pathie_process_corenlp_output_parallelized(out_corenlp_dir, amount_files, output, doc2tags,
                                                   predicate_vocabulary=predicate_vocabulary, workers=workers)
        print(" done in {}".format(datetime.now() - start))
    if tmp_dir_created:
        logging.info(f'Removing {temp_dir}...')
        shutil.rmtree(temp_dir)
    logging.info('PathIE finished')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="PubTator/JSON file / directory of PubTator/JSON files - the files must include tags")
    parser.add_argument("output", help="PathIE output file")
    parser.add_argument("--workdir", help="working directory")
    parser.add_argument("--config", default=NLP_CONFIG)
    parser.add_argument('--relation_vocab', default=None, help='Path to a relation vocabulary (json file)')
    parser.add_argument("--sections", action="store_true", default=False,
                        help="Should the section texts be considered in the extraction step?")
    parser.add_argument("-w", "--workers", help="number of parallel workers", default=1, type=int)
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)
    if args.relation_vocab:
        relation_vocab = RelationVocabulary()
        relation_vocab.load_from_json(args.relation_vocab)

        run_pathie(args.input, args.output, args.workdir, args.config, workers=args.workers,
                   predicate_vocabulary=relation_vocab.relation_dict, consider_sections=args.sections)
    else:
        run_pathie(args.input, args.output, args.workdir, args.config, workers=args.workers,
                   consider_sections=args.sections)


if __name__ == "__main__":
    main()

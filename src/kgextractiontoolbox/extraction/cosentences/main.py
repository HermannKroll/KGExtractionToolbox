import argparse
import csv
import itertools
import logging
import multiprocessing
import queue
from time import sleep

from spacy.lang.en import English

from kgextractiontoolbox.document.count import count_documents
from kgextractiontoolbox.document.document import TaggedDocument
from kgextractiontoolbox.document.extract import read_pubtator_documents
from kgextractiontoolbox.extraction.pathie.core import PathIEExtraction


def extract_based_on_co_occurrences_in_sentences(spacy_nlp, document_content, consider_sections=False) -> [
    PathIEExtraction]:
    """
    Extracts PathIE tuples based on co-mentions of tags in a sentence
    Note: only one direction is extracted
    :param spacy_nlp: spacy nlp handle
    :param document_content: the document content (will be used to create and parse a TaggedDocument)
    :param consider_sections: should we consider the sections of a document
    :return: a list of PathIE tuples
    """
    # initialize the document + create all nlp indexes by setting spacy nlp in sentence
    tagged_doc = TaggedDocument(document_content, spacy_nlp=spacy_nlp, sections=consider_sections)

    tuples = []
    # get the sentences
    sorted_sentences = sorted(tagged_doc.sentence_by_id.keys())
    for sent_id in sorted_sentences:
        tags = tagged_doc.entities_by_sentence[sent_id]

        # combine all tags with all tags within that sentence
        for t1, t2 in itertools.product(tags, tags):
            # only extract one direction
            if t1.end > t2.start:
                continue
            # confidence
            s_len = len(tagged_doc.sentence_by_id[sent_id].text)
            # eg. sentences has 100 characters
            # difference between entities is 10 characters -> 0.9
            confidence = round((s_len - (t2.start - t1.end)) / s_len, 2)

            assert 0.0 <= confidence <= 1.0
            tuples.append(PathIEExtraction(tagged_doc.id,
                                           t1.ent_id, t1.text, t1.ent_type,
                                           "associated", "associated",
                                           t2.ent_id, t2.text, t2.ent_type,
                                           confidence, tagged_doc.sentence_by_id[sent_id].text))

    return tuples


def co_occurrence_worker_job(tasks: multiprocessing.Queue,
                             results: multiprocessing.Queue,
                             consider_sections=False):
    """
    Worker logic to perform the co mention-based extraction method
    :param tasks: task queue
    :param results: result queue
    :param consider_sections: should we consider sections for the extraction logic
    :return: none
    """
    logging.debug('Worker processing the co-occurrence extractions started')

    spacy_nlp = English()  # just the language with no model
    spacy_nlp.add_pipe("sentencizer")

    extracted_tuples = []
    while tasks.qsize() > 0:
        try:
            task = tasks.get(timeout=1)
            if task is None:
                logging.debug('Nothing to stop - stop here')
                continue

            doc_content = task

            extracted_tuples.extend(extract_based_on_co_occurrences_in_sentences(spacy_nlp,
                                                                                 doc_content,
                                                                                 consider_sections))
        except queue.Empty:
            logging.debug('Queue empty exception - waiting for new tasks or exit condition')
            sleep(0.1)
            continue
    results.put(extracted_tuples)
    logging.debug('Worker finished')


def run_co_occurrences_in_sentences(input_file, output, workers=1, consider_sections=False):
    """
    Executes the co-occurrence-based extraction method
    :param input_file: documents will be loaded from that file / path
    :param output: the extracted tuples will be written as a tsv file to this path
    :param workers: number of parallel workers
    :param consider_sections: should sections be considered when processing the document content
    :return:
    """
    logging.info(f'Working with document input file: {input_file}')
    logging.info('counting documents...')
    # Prepare files
    doc_count = count_documents(input_file)
    logging.info('{} documents counted'.format(doc_count))

    # create multiprocessing queues
    task_queue = multiprocessing.Queue()
    result_queue = multiprocessing.Queue()
    # init the task
    no_tasks = 0
    for content in read_pubtator_documents(input_file):
        task_queue.put(content)
        no_tasks += 1

    logging.info(f'{no_tasks} documents to process...')
    # init the processes
    processes = []
    for i in range(0, workers):
        p = multiprocessing.Process(target=co_occurrence_worker_job,
                                    args=(task_queue, result_queue, consider_sections))
        processes.append(p)
        p.start()

    logging.info('Collecting results...')
    with open(output, 'wt') as f_out:
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input",
                        help="PubTator/JSON file / directory of PubTator/JSON files - the files must include tags")
    parser.add_argument("output", help="PathIE output file")
    parser.add_argument("--sections", action="store_true", default=False,
                        help="Should the section texts be considered in the extraction step?")
    parser.add_argument("-w", "--workers", help="number of parallel workers", default=1, type=int)
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)
    run_co_occurrences_in_sentences(args.input, args.output, workers=args.workers, consider_sections=args.sections)


if __name__ == "__main__":
    main()

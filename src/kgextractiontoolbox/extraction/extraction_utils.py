import logging
import multiprocessing
import os
import queue
from datetime import datetime
from time import sleep

from spacy.lang.en import English

from kgextractiontoolbox.document.document import TaggedDocument, TaggedEntity
from kgextractiontoolbox.document.extract import read_pubtator_documents
from kgextractiontoolbox.progress import print_progress_with_eta


def filter_document_content(pubtator_content: str, spacy_nlp, consider_sections=False):
    """
    Filter the content of a single document by removing all sentences which do not include two different tags
    :param pubtator_content: the pubtator document as a str
    :param spacy_nlp: ref to spacy nlp
    :param consider_sections: Should document sections be considered for text generation?
    :return: doc_id, a list of filtered sentences (str), a set of included tags
    """
    tagged_doc = TaggedDocument(pubtator_content, spacy_nlp=spacy_nlp, sections=consider_sections)
    doc_id = tagged_doc.id
    filtered_content = []
    tag_terms = set()
    tag_original_character_offset = 0

    sorted_sentences = sorted(tagged_doc.sentence_by_id.keys())
    for sent in sorted_sentences:
        tags = tagged_doc.entities_by_sentence[sent]
        ent_ids = {t.ent_id for t in tags}
        if len(ent_ids) > 1:  # at minimum two tags must be included in this sentence
            sentence_str = tagged_doc.sentence_by_id[sent].text
            # be sure and separate sentences
            if sentence_str[-1] in ['.', '?', '!', ':', ';']:
                sentence_str = sentence_str + ' '
            else:
                sentence_str = sentence_str + '. '
            sentence_str_lower = sentence_str.lower()
            for t in tagged_doc.entities_by_sentence[sent]:
                try:
                    t_start_new = tag_original_character_offset + sentence_str_lower.index(t.text.lower())
                    t_start_end = t_start_new + len(t.text)
                    tag_terms.add((doc_id, t_start_new, t_start_end, t.text, t.ent_type, t.ent_id))
                except ValueError:
                    logging.debug(f'Cannot find "{t.text.lower()}" in "{sentence_str_lower}"')

            tag_original_character_offset += len(sentence_str)
            filtered_content.append(sentence_str)
    return doc_id, filtered_content, tag_terms


def filter_document_sentences_without_tags(doc_len: int, input_file: str, spacy_nlp, consider_sections=False):
    """
    Filtering a PubTator file as a preperation for the extraction
    Keeps only sentences with at least two entities
    :param doc_len: the len of included documents in the input file
    :param input_file: a PubTator input file / directory of PubTator file
    :param spacy_nlp:
    :param consider_sections: Should document sections be considered for text generation?
    :return: len of extracted documents, a dict mapping document ids to tags (ent_id, ' ' + lower(ent_str), ent_type)
    """
    logging.info('Filtering {} documents (keep only document sentences with tags)'.format(doc_len))
    doc2tags = dict()
    doc2sentences = dict()
    start_time = datetime.now()
    for idx, pubtator_content in enumerate(read_pubtator_documents(input_file)):
        print_progress_with_eta('filtering documents...', idx, doc_len, start_time, print_every_k=100)
        doc_id, filtered_content, tag_terms = filter_document_content(pubtator_content, spacy_nlp,
                                                                      consider_sections=consider_sections)
        # skip empty documents
        if not filtered_content:
            continue

        doc2sentences[doc_id] = filtered_content
        doc2tags[doc_id] = [TaggedEntity(t) for t in tag_terms]

    return doc2sentences, doc2tags


def filter_document_sentences_without_tags_parallelized_worker(tasks: multiprocessing.Queue,
                                                               results: multiprocessing.Queue,
                                                               consider_sections=False):
    """
    Parallelized worker for document filtering (keep only sentences with two tags)
    :param tasks: a multiprocessing queue with all tasks
    :param results: a multiprocessing queue where all results will be stored
    :param consider_sections: Should document sections be considered for text generation?
    :return: None
    """
    logging.debug('Worker started')
    doc2tags = dict()
    doc2sentences = dict()
    spacy_nlp = English()  # just the language with no model
    spacy_nlp.add_pipe("sentencizer")
    while tasks.qsize() > 0:
        try:
            pubtator_content = tasks.get(timeout=1)
            if pubtator_content is None:
                continue
            doc_id, filtered_content, tag_terms = filter_document_content(pubtator_content, spacy_nlp,
                                                                          consider_sections=consider_sections)
            # skip empty documents
            if not filtered_content:
                continue

            doc2sentences[doc_id] = filtered_content
            doc2tags[doc_id] = [TaggedEntity(t) for t in tag_terms]
        except queue.Empty:
            logging.debug('Queue empty exception - waiting for new tasks or exit condition')
            sleep(0.1)
            continue
    results.put((doc2sentences, doc2tags))
    logging.debug('Worker finished')


def filter_document_sentences_without_tags_parallelized(doc_len: int, input_file: str, spacy_nlp, worker_count: int,
                                                        consider_sections=False):
    """
    Parallelized document filtering (keep only sentences with two tags)
    :param doc_len: the len of included documents in the input file
    :param input_file: a PubTator input file / directory of PubTator file
    :param spacy_nlp: space nlp reference
    :param worker_count: number of workers
    :param consider_sections: Should document sections be considered for text generation?
    :return: doc2sentences (dict), doc2tags (dict)
    """
    if worker_count == 1:
        logging.info('Using single-threaded filtering...')
        return filter_document_sentences_without_tags(doc_len, input_file, spacy_nlp,
                                                      consider_sections=consider_sections)
    else:
        logging.info('Using parallelized filtering...')
        task_queue = multiprocessing.Queue()

        start_time = datetime.now()
        for idx, pubtator_content in enumerate(read_pubtator_documents(input_file)):
            print_progress_with_eta('adding documents...', idx, doc_len, start_time, print_every_k=100)
            task_queue.put(pubtator_content)

        logging.debug(f'Starting {worker_count} workers...')
        result_queue = multiprocessing.Queue()
        processes = []
        for i in range(0, worker_count):
            p = multiprocessing.Process(target=filter_document_sentences_without_tags_parallelized_worker,
                                        args=(task_queue, result_queue, consider_sections))
            processes.append(p)
            p.start()

        logging.debug('Collecting results...')
        doc2sentences, doc2tags = dict(), dict()
        for p in processes:
            task_doc2sentences, task_doc2tags = result_queue.get()
            doc2sentences.update(task_doc2sentences)
            doc2tags.update(task_doc2tags)

        logging.debug('Waiting for workers to terminate...')
        for p in processes:
            while p.is_alive():
                logging.debug('join thread')
                p.join(timeout=1)
        logging.debug('Workers terminated')
        return doc2sentences, doc2tags


def filter_and_write_documents_to_tempdir(doc_len: int, input_file: str, output_dir: str,
                                          out_filelist_file: str, spacy_nlp, worker_count=1,
                                          consider_sections=False):
    """
    Filtering a PubTator file as a preperation for the extraction
    Keeps only sentences with at least two entities
    :param doc_len: the len of included documents in the input file
    :param input_file: a PubTator input file / directory of PubTator file
    :param output_dir: output directory where the documents are extracted
    :param out_filelist_file: output file where a filelist of all extracted files is stored
    :param spacy_nlp: spacy nlp handle
    :param worker_count: the number of parallel workers
    :param consider_sections: Should document sections be considered for text generation?
    :return: len of extracted documents, a dict mapping document ids to tags (ent_id, ' ' + lower(ent_str), ent_type)
    """
    logging.info('Filtering {} documents (keep only document sentences with tags)'.format(doc_len))
    amount_skipped_files = 0
    openie_files = []
    doc2sentences, doc2tags = filter_document_sentences_without_tags_parallelized(doc_len, input_file, spacy_nlp,
                                                                                  worker_count,
                                                                                  consider_sections=consider_sections)
    start_time = datetime.now()
    for idx, (doc_id, doc_sentences) in enumerate(doc2sentences.items()):
        # write filtered document
        o_file_path = os.path.join(output_dir, '{}.txt'.format(doc_id))
        openie_files.append(o_file_path)
        with open(o_file_path, 'w') as f_out:
            f_out.write(''.join(doc_sentences))
        print_progress_with_eta('writing documents...', idx, doc_len, start_time, print_every_k=10)

    logging.info('{} files need to be processed. {} files skipped.'.format(len(openie_files), amount_skipped_files))
    with open(out_filelist_file, "w") as f:
        f.write("\n".join(openie_files))
    return len(openie_files), doc2tags

import argparse
import csv
import logging
import stanza
from datetime import datetime
from spacy.lang.en import English

from kgextractiontoolbox.cleaning.relation_vocabulary import RelationVocabulary
from kgextractiontoolbox.document.count import count_documents
from kgextractiontoolbox.extraction.extraction_utils import filter_document_sentences_without_tags
from kgextractiontoolbox.extraction.pathie.core import PathIEDependency, PathIEToken, pathie_extract_facts_from_sentence
from kgextractiontoolbox.progress import print_progress_with_eta

STANZA_DOCUMENT_BATCH = 1000


def _pathie_process_document_batch(stanza_nlp, documents, doc2tags, predicate_vocabulary: {str: [str]}):
    """
    Perform extraction based on PathIE Stanza
    Invokes Stanza to produce the corresponding tokenization and dependency parsing
    :param stanza_nlp: Stanza NLP handle
    :param documents a list of tuples (doc_id, doc_content) to enable batch processing
    :param doc2tags: a dict that maps a document to its corresponding tags
    :param predicate_vocabulary: the predicate vocabulary if special words are given
    :return: None
    """
    # perform the stanza call
    texts = [stanza.Document([], text=doc[1]) for doc in documents]
    processed_docs = stanza_nlp(texts)
    extracted_tuples = []
    for (doc_id, doc_text), stanza_doc in zip(documents, processed_docs):
        for sent in stanza_doc.sentences:
            # convert stanza tokens and dependencies to PathIE tuples
            sent_dependencies = []
            for dep in sent.dependencies:
                w1, relation, w2 = dep
                sent_dependencies.append(PathIEDependency(w1.id, w2.id, relation))
            sent_tokens = []
            for t in sent.tokens:
                # fake before and after tokens because they are not available in stanza
                sent_tokens.append(PathIEToken(t.text, t.text.lower(), "", " ",
                                               t.id[0], t.start_char, t.end_char,
                                               t.words[0].pos, t.words[0].lemma))

            extracted_tuples.extend(pathie_extract_facts_from_sentence(doc_id, doc2tags[doc_id], sent_tokens,
                                                                       sent_dependencies,
                                                                       predicate_vocabulary=predicate_vocabulary))
    return extracted_tuples


def pathie_stanza_extract_interactions(doc2sentences, doc2tags, file_count, output,
                                       predicate_vocabulary: {str: [str]},
                                       cpu=False):
    """
    Perform extraction based on PathIE Stanza
    Invokes Stanza to produce the corresponding tokenization and dependency parsing
    :param doc2sentences: a dict that maps a document id to a list of sentences
    :param doc2tags: a dict that maps a document to its corresponding tags
    :param file_count: the number of files for progress estimation
    :param output: the output that should be written
    :param predicate_vocabulary: the predicate vocabulary if special words are given
    :param cpu: forces Stanford Stanza to run on CPU
    :return: None
    """
    start_time = datetime.now()
    logging.info('Initializing Stanza Pipeline...')
    nlp = stanza.Pipeline(lang='en', processors='tokenize,mwt,pos,lemma,depparse', use_gpu=not cpu)

    with open(output, 'wt') as f_out:
        writer = csv.writer(f_out, delimiter='\t')
        writer.writerow(['document id', 'subject id', 'subject str', 'subject type', 'predicate',
                         'predicate lemmatized', 'object id', 'object str', 'object type',
                         'confidence', 'sentence'])
        document_batch = []
        for idx, (doc_id, sentences) in enumerate(doc2sentences.items()):
            print_progress_with_eta("pathie: processing documents...", idx, file_count, start_time, print_every_k=100)
            doc_content = ' '.join(sentences)
            document_batch.append((doc_id, doc_content))
            if len(document_batch) >= STANZA_DOCUMENT_BATCH:
                extracted_tuples = _pathie_process_document_batch(nlp, document_batch, doc2tags, predicate_vocabulary)
                for e_tuple in extracted_tuples:
                    writer.writerow([str(t) for t in e_tuple])
                document_batch.clear()

        if len(document_batch) > 0:
            extracted_tuples = _pathie_process_document_batch(nlp, document_batch, doc2tags, predicate_vocabulary)
            for e_tuple in extracted_tuples:
                writer.writerow([str(t) for t in e_tuple])
            document_batch.clear()


def run_stanza_pathie(input_file, output, predicate_vocabulary: {str: [str]} = None, cpu=False):
    """
    Executes PathIE via Stanza
    :param input_file: the PubTator input file (tags must be included)
    :param output: extractions will be written to output
    :param predicate_vocabulary: the predicate vocabulary if special words are given
    :param cpu: forces Stanford Stanza to run on CPU
    :return: None
    """
    logging.info('Init spacy nlp...')
    spacy_nlp = English()  # just the language with no model
    spacy_nlp.add_pipe("sentencizer")

    # Prepare files
    doc_count = count_documents(input_file)
    logging.info('{} documents counted'.format(doc_count))

    doc2sentences, doc2tags = filter_document_sentences_without_tags(doc_count, input_file, spacy_nlp)
    amount_files = len(doc2tags)

    if amount_files == 0:
        print('no files to process - stopping')
    else:
        start = datetime.now()
        # Process output
        pathie_stanza_extract_interactions(doc2sentences, doc2tags, amount_files, output,
                                           predicate_vocabulary=predicate_vocabulary, cpu=cpu)
        print(" done in {}".format(datetime.now() - start))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input file or directory (pubtator or json) including tags")
    parser.add_argument("output", help="PathIE output file")
    parser.add_argument('--relation_vocab', default=None, help='Path to a relation vocabulary (json file)')
    parser.add_argument('--cpu', default=False, action="store_true", help="forces Stanza to run in CPU mode")
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)

    cpu = True if args.cpu else False

    if args.relation_vocab:
        relation_vocab = RelationVocabulary()
        relation_vocab.load_from_json(args.relation_vocab)

        run_stanza_pathie(args.input, args.output, predicate_vocabulary=relation_vocab.relation_dict, cpu=cpu)
    else:
        run_stanza_pathie(args.input, args.output, cpu=cpu)


if __name__ == "__main__":
    main()

import argparse
import csv
import logging

from spacy.lang.en import English

from kgextractiontoolbox.document.count import count_documents
from kgextractiontoolbox.document.document import TaggedDocument
from kgextractiontoolbox.document.extract import read_pubtator_documents
from kgextractiontoolbox.extraction.extraction_utils import filter_document_sentences_without_tags
from kgextractiontoolbox.extraction.loading.load_openie_extractions import OPENIE_TUPLE
from kgextractiontoolbox.extraction.openie51.oie5_server_controller import Oi5ServerController
from kgextractiontoolbox.progress import Progress


def openie51_run(document_file, output, no_entity_filter=False):
    """
    Initializes OpenIE6. Will generate the corresponding input file, reads the output and converts it to our
    internal OpenIE format
    :param document_file: input file with documents to generate
    :param output: the output file
    :param no_entity_filter: if true only sentences with two tags will be processed by OpenIE
    :return: None
    """
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

    if doc_count == 0:
        print('no files to process - stopping')
    else:
        contr = Oi5ServerController.get()
        try:
            contr.start_server()
            prog = Progress(total=doc_count, text="Extracting")
            prog.start_time()
            spacy_lemma = English()  # just the language with no model
            spacy_lemma.add_pipe("lemmatizer", config={"mode": "lookup"})
            spacy_lemma.initialize()
            with open(output, 'wt') as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerow(['document id',
                                 'subject',
                                 'predicate',
                                 'predicate lemmatized',
                                 'object',
                                 'confidence',
                                 'sentence'])

                for n, (doc_id, sentences) in enumerate(doc2sentences.items()):
                    prog.print_progress(n)
                    for sentence in sentences:
                        sentence = sentence.replace("\n", " ").replace("\t", " ").strip()
                        extractions = contr.get_extraction(sentence)
                        for extraction in extractions:
                            conf = extraction["confidence"]
                            subj = extraction["extraction"]["arg1"]["text"]
                            pred = extraction["extraction"]["rel"]["text"]
                            pred_lemma = ' '.join([token.lemma_ for token in spacy_lemma(pred)])
                            for arg2 in extraction["extraction"]["arg2s"]:
                                obj = arg2["text"]
                                writer.writerow(OPENIE_TUPLE(doc_id, subj, pred, pred_lemma, obj, conf, sentence))
                prog.done()
        finally:
            logging.info("Stopping OpenIE5.1 Server")
            contr.stop_server()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Document file with tags")
    parser.add_argument("output", help="OpenIE results will be stored here")
    parser.add_argument("--no_entity_filter", action="store_true",
                        default=False, required=False, help="Does not filter sentences by tags")
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)

    openie51_run(args.input, args.output, args.no_entity_filter)


if __name__ == "__main__":
    main()

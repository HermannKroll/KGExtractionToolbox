import argparse
import csv
import logging
import pathlib as pl
import rdflib
import typing as tp
import urllib
from datetime import datetime

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Predication, Sentence
from kgextractiontoolbox.progress import print_progress_with_eta, Progress


def export_predications_as_rdf(output_file: tp.Union[pl.Path, str], document_collection=None, export_metadata=False,
                               check_relation_not_null=True):
    """
    Exports predications in a turtle rdf serialization format
    :param output_file: the path to the output file
    :param document_collection: export statements for this document collection only (optional)
    :param export_metadata: if true metadata will also be extracted
    :return: None
    """
    session = Session.get()
    count = Predication.query_predication_count(session, document_collection=document_collection)
    logging.info(f"Found {count} triples")
    prog = Progress(total=count, text="Building Graph", print_every=100)
    output_graph = rdflib.Graph()
    prog.start_time()
    for n, row in enumerate(Predication.iterate_predications(session, check_relation_not_null=check_relation_not_null,
                                                             document_collection=document_collection)):
        prog.print_progress(n + 1)
        if export_metadata:
            output_graph.add((rdflib.URIRef(f'statement_{row.id}'), rdflib.URIRef("document_id"),
                              rdflib.URIRef(str(row.document_id))))
            output_graph.add((rdflib.URIRef(f'statement_{row.id}'), rdflib.URIRef("document_collection"),
                              rdflib.URIRef(row.document_collection)))
            output_graph.add(
                (rdflib.URIRef(f'statement_{row.id}'), rdflib.URIRef("subject_id"),
                 rdflib.URIRef(urllib.parse.quote(row.subject_id))))
            output_graph.add(
                (rdflib.URIRef(f'statement_{row.id}'), rdflib.URIRef("subject_type"),
                 rdflib.URIRef(urllib.parse.quote(row.subject_type))))
            output_graph.add(
                (rdflib.URIRef(f'statement_{row.id}'), rdflib.URIRef("subject_str"),
                 rdflib.Literal(urllib.parse.quote(row.subject_str))))
            output_graph.add(
                (rdflib.URIRef(f'statement_{row.id}'), rdflib.URIRef("predicate"),
                 rdflib.Literal(urllib.parse.quote(row.predicate))))
            output_graph.add(
                (rdflib.URIRef(f'statement_{row.id}'), rdflib.URIRef("relation"),
                 rdflib.Literal(urllib.parse.quote(row.relation))))
            output_graph.add(
                (rdflib.URIRef(f'statement_{row.id}'), rdflib.URIRef("object_id"),
                 rdflib.URIRef(urllib.parse.quote(row.object_id))))
            output_graph.add(
                (rdflib.URIRef(f'statement_{row.id}'), rdflib.URIRef("object_type"),
                 rdflib.URIRef(urllib.parse.quote(row.object_type))))
            output_graph.add(
                (rdflib.URIRef(f'statement_{row.id}'), rdflib.URIRef("object_str"),
                 rdflib.Literal(urllib.parse.quote(row.object_str))))
            output_graph.add((rdflib.URIRef(f'statement_{row.id}'), rdflib.URIRef("sentence_id"),
                              rdflib.Literal(f'sentence_id_{row.sentence_id}')))
            output_graph.add((rdflib.URIRef(f'statement_{row.id}'), rdflib.URIRef("extraction_type"),
                              rdflib.Literal(row.extraction_type)))
        else:
            output_graph.add((rdflib.URIRef(urllib.parse.quote(row.subject_id)),
                              rdflib.URIRef(row.relation if row.relation else ""),
                              rdflib.URIRef(urllib.parse.quote(row.object_id))))
    if export_metadata:
        logging.info('Exporting sentences...')
        # export sentences also
        for n, row in enumerate(Sentence.iterate_sentences(session, document_collection=document_collection)):
            output_graph.add((rdflib.URIRef(f'sentence_id_{row.id}'), rdflib.URIRef('text'), rdflib.Literal(row.text)))

    prog.done()
    logging.info(f"Writing graph to {output_file}...")
    output_graph.serialize(destination=output_file, format="turtle")
    logging.info("done!")


def export_predications_as_tsv(output_file: str, document_collection=None, export_metadata=False,
                               check_relation_not_null=True):
    """
    Exports the database tuples as a CSV
    :param output_file: output filename
    :param document_collection: only export statements in this document collection (optional)
    :param export_metadata: if true metadata will also be extracted
    :return: None
    """
    session = Session.get()
    logging.info('Counting predications...')
    count = Predication.query_predication_count(session, relation=None,
                                                document_collection=document_collection)

    start_time = datetime.now()
    with open(output_file, 'wt') as f:
        logging.info(f'exporting {count} entries with metadata in TSV format to {output_file}...')
        writer = csv.writer(f, delimiter='\t')
        if export_metadata:
            writer.writerow(["document_id", "document_collection",
                             "subject_id", "subject_type", "subject_str",
                             "predicate", "relation",
                             "object_id", "object_type", "object_str",
                             "sentence_id", "extraction_type"])
            for idx, pred in enumerate(
                    Predication.iterate_predications_joined_sentences(session,
                                                                      document_collection=document_collection,
                                                                      check_relation_not_null=check_relation_not_null)):
                writer.writerow([pred.Predication.document_id, pred.Predication.document_collection,
                                 pred.Predication.subject_id, pred.Predication.subject_type,
                                 pred.Predication.subject_str,
                                 pred.Predication.predicate, pred.Predication.relation,
                                 pred.Predication.object_id, pred.Predication.object_type, pred.Predication.object_str,
                                 pred.Sentence.text, pred.Predication.extraction_type])
                print_progress_with_eta("exporting", idx, count, start_time)
        else:
            writer.writerow(["subject_id", "relation", "object_id"])
            logging.info(f'exporting {count} entries without metadata in TSV format to {output_file}...')
            for idx, pred in enumerate(Predication.iterate_predications(session,
                                                                        document_collection=document_collection)):
                writer.writerow([pred.subject_id, pred.relation, pred.object_id])
                print_progress_with_eta("exporting", idx, count, start_time)

    logging.info('Export finished')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", help='Path for the output file')
    parser.add_argument("-c", "--collection", required=False,
                        help='Export statements only for this document collection')
    parser.add_argument("--metadata", required=False, action="store_true", help='Should metadata be exported?')
    parser.add_argument("-f", "--format", action='store', choices=["rdf", "tsv"],
                        help='export format (supported: rdf (turtle) | tsv)', required=True)
    parser.add_argument("-n", "--none-relations", action="store_true",
                        help="also export relations with missing predicate")
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)

    if args.format.lower() == 'rdf':
        export_predications_as_rdf(args.output, document_collection=args.collection, export_metadata=args.metadata,
                                   check_relation_not_null=not args.none_relations)
    else:
        export_predications_as_tsv(args.output, document_collection=args.collection, export_metadata=args.metadata,
                                   check_relation_not_null=not args.none_relations)


if __name__ == "__main__":
    main()

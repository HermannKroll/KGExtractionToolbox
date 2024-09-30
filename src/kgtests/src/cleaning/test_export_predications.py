import unittest

import rdflib

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Document, Sentence, Predication
from kgextractiontoolbox.extraction.export_predications import export_predications_as_tsv, export_predications_as_rdf
from kgtests import util


class ExportPredicationsTest(unittest.TestCase):

    def setUp(self) -> None:
        session = Session.get()
        documents = [dict(id=1, collection="Test_Export", title="ABC", abstract=""),
                     dict(id=2, collection="Test_Export", title="DEF", abstract=""),
                     dict(id=2, collection="Test_Export_Not", title="DEF", abstract="")]
        Document.bulk_insert_values_into_table(session, documents)

        sentences = [dict(id=11, document_collection="Test_Export", text="Hello", md5hash="1"),
                     dict(id=12, document_collection="Test_Export", text="World. Nice", md5hash="2")]
        Sentence.bulk_insert_values_into_table(session, sentences)

        predications = [dict(id=11,
                             document_id=1, document_collection="Test_Export",
                             subject_id="A", subject_type="Drug", subject_str="ab",
                             predicate="treat", relation="treats",
                             object_id="B", object_type="Disease", object_str="bc",
                             sentence_id=11, extraction_type="PathIE"),
                        dict(id=12,
                             document_id=1, document_collection="Test_Export",
                             subject_id="C", subject_type="Disease", subject_str="c a",
                             predicate="treat", relation="treats",
                             object_id="B", object_type="Disease", object_str="b a",
                             sentence_id=11, extraction_type="PathIE"),
                        dict(id=13,
                             document_id=2, document_collection="Test_Export",
                             subject_id="A", subject_type="Disease", subject_str="a",
                             predicate="induce", relation="induces",
                             object_id="B", object_type="Disease", object_str="b",
                             sentence_id=12, extraction_type="PathIE"),
                        dict(id=14,
                             document_id=2, document_collection="Test_Export",
                             subject_id="C", subject_type="Gene", subject_str="",
                             predicate="induce", relation="induces",
                             object_id="D", object_type="Gene", object_str="",
                             sentence_id=12, extraction_type="PathIE"),
                        dict(id=15,
                             document_id=2, document_collection="Test_Export_Not",
                             subject_id="C", subject_type="Gene", subject_str="",
                             predicate="induce", relation="induces",
                             object_id="D", object_type="Gene", object_str="",
                             sentence_id=12, extraction_type="PathIE")
                        ]
        Predication.bulk_insert_values_into_table(session, predications)

    def test_export_predications_as_tsv_without_metadata(self):
        output_file = util.tmp_rel_path("export_predications_without_metadata.tsv")
        export_predications_as_tsv(output_file, document_collection="Test_Export")

        tuples = set()
        with open(output_file, 'rt') as f:
            for line in f:
                tuples.add(tuple(line.strip().split('\t')))

        self.assertEqual(5, len(tuples))
        self.assertIn(('subject_id', 'relation', 'object_id'), tuples)
        self.assertIn(('A', 'treats', 'B'), tuples)
        self.assertIn(('C', 'treats', 'B'), tuples)
        self.assertIn(('A', 'induces', 'B'), tuples)
        self.assertIn(('C', 'induces', 'D'), tuples)

    def test_export_predications_as_tsv_with_metadata(self):
        output_file = util.tmp_rel_path("export_predications_with_metadata.tsv")
        export_predications_as_tsv(output_file, document_collection="Test_Export", export_metadata=True)

        tuples = set()
        with open(output_file, 'rt') as f:
            for line in f:
                tuples.add(tuple(line.strip().split('\t')))

        self.assertEqual(5, len(tuples))
        self.assertIn(("document_id", "document_collection",
                       "subject_id", "subject_type", "subject_str",
                       "predicate", "relation",
                       "object_id", "object_type", "object_str",
                       "sentence_id", "extraction_type"), tuples)
        self.assertIn(
            ('1', 'Test_Export', 'A', 'Drug', 'ab', 'treat', 'treats', 'B', 'Disease', 'bc', 'Hello', 'PathIE'),
            tuples)
        self.assertIn(
            ('1', 'Test_Export', 'C', 'Disease', 'c a', 'treat', 'treats', 'B', 'Disease', 'b a', 'Hello', 'PathIE'),
            tuples)
        self.assertIn(('2', 'Test_Export', 'A', 'Disease', 'a', 'induce', 'induces', 'B', 'Disease', 'b', 'World. Nice',
                       'PathIE'),
                      tuples)
        self.assertIn(
            ('2', 'Test_Export', 'C', 'Gene', '', 'induce', 'induces', 'D', 'Gene', '', 'World. Nice', 'PathIE'),
            tuples)

    def test_export_predications_as_rdf(self):
        output_file = util.tmp_rel_path("export_predications.ttl")
        export_predications_as_rdf(output_file, document_collection="Test_Export")

        g = rdflib.Graph()
        g.parse(output_file, format="turtle")
        tuples = set([(s.split('/')[-1], p.split('/')[-1], o.split('/')[-1]) for s, p, o in g])
        self.assertEqual(4, len(tuples))
        self.assertIn(('A', 'treats', 'B'), tuples)
        self.assertIn(('C', 'treats', 'B'), tuples)
        self.assertIn(('A', 'induces', 'B'), tuples)
        self.assertIn(('C', 'induces', 'D'), tuples)

    def test_export_predications_as_rdf_with_metadata(self):
        output_file = util.tmp_rel_path("export_predications_with_metadata.ttl")
        export_predications_as_rdf(output_file, document_collection="Test_Export", export_metadata=True)

        g = rdflib.Graph()
        g.parse(output_file, format="turtle")
        tuples = set([(s.split('/')[-1], p.split('/')[-1], o.split('/')[-1]) for s, p, o in g])
        self.assertEqual(4 * 12 + 2, len(tuples))

        self.assertIn(('sentence_id_11', 'text', 'Hello'), tuples)
        self.assertIn(('sentence_id_12', 'text', 'World. Nice'), tuples)
        self.assertIn(('statement_11', 'document_id', '1'), tuples)
        self.assertIn(('statement_11', 'document_collection', 'Test_Export'), tuples)
        self.assertIn(('statement_11', 'subject_id', 'A'), tuples)
        self.assertIn(('statement_11', 'subject_type', 'Drug'), tuples)
        self.assertIn(('statement_11', 'subject_str', 'ab'), tuples)
        self.assertIn(('statement_11', 'predicate', 'treat'), tuples)
        self.assertIn(('statement_11', 'relation', 'treats'), tuples)
        self.assertIn(('statement_11', 'object_id', 'B'), tuples)
        self.assertIn(('statement_11', 'object_type', 'Disease'), tuples)
        self.assertIn(('statement_11', 'object_str', 'bc'), tuples)
        self.assertIn(('statement_11', 'sentence_id', 'sentence_id_11'), tuples)
        self.assertIn(('statement_11', 'extraction_type', 'PathIE'), tuples)

        self.assertIn(('statement_12', 'document_id', '1'), tuples)
        self.assertIn(('statement_12', 'document_collection', 'Test_Export'), tuples)
        self.assertIn(('statement_12', 'subject_id', 'C'), tuples)
        self.assertIn(('statement_12', 'subject_type', 'Disease'), tuples)
        self.assertIn(('statement_12', 'subject_str', 'c%20a'), tuples)
        self.assertIn(('statement_12', 'predicate', 'treat'), tuples)
        self.assertIn(('statement_12', 'relation', 'treats'), tuples)
        self.assertIn(('statement_12', 'object_id', 'B'), tuples)
        self.assertIn(('statement_12', 'object_type', 'Disease'), tuples)
        self.assertIn(('statement_12', 'object_str', 'b%20a'), tuples)
        self.assertIn(('statement_12', 'sentence_id', 'sentence_id_11'), tuples)
        self.assertIn(('statement_12', 'extraction_type', 'PathIE'), tuples)

        self.assertIn(('statement_13', 'document_id', '2'), tuples)
        self.assertIn(('statement_13', 'document_collection', 'Test_Export'), tuples)
        self.assertIn(('statement_13', 'subject_id', 'A'), tuples)
        self.assertIn(('statement_13', 'subject_type', 'Disease'), tuples)
        self.assertIn(('statement_13', 'subject_str', 'a'), tuples)
        self.assertIn(('statement_13', 'predicate', 'induce'), tuples)
        self.assertIn(('statement_13', 'relation', 'induces'), tuples)
        self.assertIn(('statement_13', 'object_id', 'B'), tuples)
        self.assertIn(('statement_13', 'object_type', 'Disease'), tuples)
        self.assertIn(('statement_13', 'object_str', 'b'), tuples)
        self.assertIn(('statement_13', 'sentence_id', 'sentence_id_12'), tuples)
        self.assertIn(('statement_13', 'extraction_type', 'PathIE'), tuples)

        self.assertIn(('statement_14', 'document_id', '2'), tuples)
        self.assertIn(('statement_14', 'document_collection', 'Test_Export'), tuples)
        self.assertIn(('statement_14', 'subject_id', 'C'), tuples)
        self.assertIn(('statement_14', 'subject_type', 'Gene'), tuples)
        self.assertIn(('statement_14', 'subject_str', rdflib.term.Literal('')), tuples)
        self.assertIn(('statement_14', 'predicate', 'induce'), tuples)
        self.assertIn(('statement_14', 'relation', 'induces'), tuples)
        self.assertIn(('statement_14', 'object_id', 'D'), tuples)
        self.assertIn(('statement_14', 'object_type', 'Gene'), tuples)
        self.assertIn(('statement_14', 'object_str', rdflib.term.Literal('')), tuples)
        self.assertIn(('statement_14', 'sentence_id', 'sentence_id_12'), tuples)
        self.assertIn(('statement_14', 'extraction_type', 'PathIE'), tuples)

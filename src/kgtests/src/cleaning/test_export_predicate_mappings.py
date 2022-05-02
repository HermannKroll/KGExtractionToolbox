import csv
import unittest

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Document, Sentence, Predication
from kgextractiontoolbox.cleaning.export_predicate_mappings import export_predicate_mapping
from kgtests import util


class PredicateMappingExportTest(unittest.TestCase):

    def setUp(self) -> None:
        session = Session.get()
        documents = [dict(id=1, collection="Test_Export_Mappings", title="ABC", abstract=""),
                     dict(id=2, collection="Test_Export_Mappings", title="DEF", abstract="")]
        Document.bulk_insert_values_into_table(session, documents)

        sentences = [dict(id=1, document_collection="Test_Export_Mappings", text="Hello", md5hash="1"),
                     dict(id=2, document_collection="Test_Export_Mappings", text="World", md5hash="2")]
        Sentence.bulk_insert_values_into_table(session, sentences)

        predications = [dict(id=21,
                             document_id=1, document_collection="Test_Export_Mappings",
                             subject_id="A", subject_type="Drug", subject_str="",
                             predicate="treats", relation="treats",
                             object_id="B", object_type="Disease", object_str="",
                             sentence_id=1, extraction_type="PathIE"),
                        dict(id=22,
                             document_id=1, document_collection="Test_Export_Mappings",
                             subject_id="A", subject_type="Disease", subject_str="",
                             predicate="treats", relation="treats",
                             object_id="B", object_type="Disease", object_str="",
                             sentence_id=1, extraction_type="PathIE"),
                        dict(id=23,
                             document_id=2, document_collection="Test_Export_Mappings",
                             subject_id="A", subject_type="Disease", subject_str="",
                             predicate="induces", relation="induces",
                             object_id="B", object_type="Disease", object_str="",
                             sentence_id=2, extraction_type="PathIE"),
                        dict(id=24,
                             document_id=2, document_collection="Test_Export_Mappings",
                             subject_id="A", subject_type="Gene", subject_str="",
                             predicate="induces", relation="induces",
                             object_id="B", object_type="Gene", object_str="",
                             sentence_id=2, extraction_type="PathIE"),
                        dict(id=25,
                             document_id=2, document_collection="Test_Export_Mappings",
                             subject_id="A", subject_type="Gene", subject_str="",
                             predicate="therapy", relation="therapy",
                             object_id="B", object_type="Gene", object_str="",
                             sentence_id=2, extraction_type="PathIE"),
                        dict(id=26,
                             document_id=2, document_collection="Test_Export_Mappings",
                             subject_id="A", subject_type="Gene", subject_str="",
                             predicate="test",
                             object_id="B", object_type="Gene", object_str="",
                             sentence_id=2, extraction_type="PathIE")
                        ]
        Predication.bulk_insert_values_into_table(session, predications)

    def test_export_predicate_mappings(self):
        output_file = util.tmp_rel_path("predicate_mappings.tsv")
        export_predicate_mapping(output_file, "Test_Export_Mappings")
        output_results = set()
        with open(output_file, 'rt') as f:
            reader = csv.reader(f, delimiter='\t')
            for t in reader:
                output_results.add(tuple(t))

        self.assertIn(('predicate', 'count', 'relation'), output_results)
        self.assertIn(("treats", "2", "treats"), output_results)
        self.assertIn(("induces", "2", "induces"), output_results)
        self.assertIn(("therapy", "1", "therapy"), output_results)
        self.assertIn(("test", "1", ""), output_results)
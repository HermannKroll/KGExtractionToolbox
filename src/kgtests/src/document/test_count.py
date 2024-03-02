import unittest

from kgextractiontoolbox.document.count import count_documents
from kgtests.util import get_test_resource_filepath


class TestCountDocument(unittest.TestCase):


    def test_count_pubtator_document(self):
        self.assertEqual(10, count_documents(get_test_resource_filepath("pubmed_sample.pubtator")))
        self.assertEqual(1, count_documents(get_test_resource_filepath("PubMed26.txt")))
        self.assertEqual(1, count_documents(get_test_resource_filepath("PubMed54.txt")))

    def test_count_json_document(self):
        self.assertEqual(2, count_documents(get_test_resource_filepath("infiles/json_infiles/5297_5600.json")))
        self.assertEqual(1, count_documents(get_test_resource_filepath("loading/example_doc_sections.json")))

    def test_count_json_line(self):
        self.assertEqual(3, count_documents(get_test_resource_filepath("loading/example_json_line.jsonl")))

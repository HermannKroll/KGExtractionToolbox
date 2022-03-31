import copy
import unittest

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.retrieve import retrieve_tagged_documents_from_database
from kgextractiontoolbox.document.document import TaggedDocument
from kgextractiontoolbox.document.load_document import document_bulk_load
from kgtests import util


class TestLoadDocument(unittest.TestCase):

    def test_document_comparison(self):
        test_path = util.get_test_resource_filepath("loading/example_doc_sections.json")
        document_bulk_load(test_path, "TestLoading1")

        # parsed json document
        with open(test_path, 'rt') as f:
            doc_content = f.read()
        test_doc = TaggedDocument(doc_content)

        session = Session.get()
        db_docs = retrieve_tagged_documents_from_database(session, {test_doc.id}, "TestLoading1")

        self.assertEqual(1, len(db_docs))
        self.assertEqual(test_doc, db_docs[0])

        test1 = copy.copy(db_docs[0])
        test1.id = test_doc.id + 1
        self.assertNotEqual(test_doc, test1)

        test2 = copy.copy(db_docs[0])
        test2.title = test_doc.title + "bla"
        self.assertNotEqual(test_doc, test2)

        test3 = copy.copy(db_docs[0])
        test3.abstract = test_doc.abstract + "bla"
        self.assertNotEqual(test_doc, test3)

        test4 = copy.copy(db_docs[0])
        test4.sections = []
        self.assertNotEqual(test_doc, test3)

    def test_load_document_with_sections(self):
        test_path = util.get_test_resource_filepath("loading/example_doc_sections.json")
        document_bulk_load(test_path, "TestLoading1")

        # parsed json document
        with open(test_path, 'rt') as f:
            doc_content = f.read()
        test_doc = TaggedDocument(doc_content)

        session = Session.get()
        db_docs = retrieve_tagged_documents_from_database(session, {test_doc.id}, "TestLoading1")

        self.assertEqual(1, len(db_docs))
        self.assertEqual(test_doc, db_docs[0])

    def test_load_document_with_classification(self):
        test_path = util.get_test_resource_filepath("loading/example_doc_classification.json")
        document_bulk_load(test_path, "TestLoading2")

        # parsed json document
        with open(test_path, 'rt') as f:
            doc_content = f.read()
        test_doc = TaggedDocument(doc_content)

        session = Session.get()
        db_docs = retrieve_tagged_documents_from_database(session, {test_doc.id}, "TestLoading2")

        self.assertEqual(1, len(db_docs))
        self.assertEqual(test_doc, db_docs[0])

    def test_load_document_long(self):
        test_path = util.get_test_resource_filepath("loading/example_doc_long.json")
        document_bulk_load(test_path, "TestLoading3")

        # parsed json document
        with open(test_path, 'rt') as f:
            doc_content = f.read()
        test_doc = TaggedDocument(doc_content)

        session = Session.get()
        db_docs = retrieve_tagged_documents_from_database(session, {test_doc.id}, "TestLoading3")

        self.assertEqual(1, len(db_docs))
        self.assertEqual(test_doc, db_docs[0])

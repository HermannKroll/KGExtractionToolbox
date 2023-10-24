import copy
import unittest

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.retrieve import retrieve_narrative_documents_from_database
from kgextractiontoolbox.document.load_narrative_documents import narrative_document_bulk_load
from kgextractiontoolbox.document.narrative_document import NarrativeDocument
from kgtests import util


class TestLoadNarrativeDocument(unittest.TestCase):

    def test_document_comparison(self):
        test_path = util.get_test_resource_filepath("narrative_documents/example1.json")
        narrative_document_bulk_load(test_path, "TestLoadingNarrative1")

        # parsed json document
        with open(test_path, 'rt') as f:
            doc_content = f.read()
        test_doc = NarrativeDocument()
        test_doc.load_from_json(doc_content)

        session = Session.get()
        db_docs = retrieve_narrative_documents_from_database(session, {test_doc.id}, "TestLoadingNarrative1")

        self.assertEqual(1, len(db_docs))
        self.assertEqual(test_doc, db_docs[0])

        test1 = copy.copy(db_docs[0])
        test1.id = test_doc.id + 1
        self.assertNotEqual(test_doc, test1)

        test2 = copy.copy(db_docs[0])
        test2.metadata.authors = test_doc.metadata.authors + "bla"
        self.assertNotEqual(test_doc, test2)

        test3 = copy.copy(db_docs[0])
        test3.metadata.publication_doi = test_doc.metadata.publication_doi + "bla"
        self.assertNotEqual(test_doc, test3)

        test4 = copy.copy(db_docs[0])
        test4.sections = []
        self.assertNotEqual(test_doc, test3)

    def test_load_document_with_metadata(self):
        test_path = util.get_test_resource_filepath("narrative_documents/example1.json")
        narrative_document_bulk_load(test_path, "TestLoadingNarrative2")

        # parsed json document
        with open(test_path, 'rt') as f:
            doc_content = f.read()
        test_doc = NarrativeDocument()
        test_doc.load_from_json(doc_content)

        session = Session.get()
        db_docs = retrieve_narrative_documents_from_database(session, {test_doc.id}, "TestLoadingNarrative2")

        self.assertEqual(1, len(db_docs))
        self.assertEqual(test_doc, db_docs[0])

    def test_load_document_translation(self):
        test_path = util.get_test_resource_filepath("narrative_documents/example_document_translation.json")
        narrative_document_bulk_load(test_path, "TestLoadingNarrative3", artificial_document_ids=True)

        # parsed json document
        with open(test_path, 'rt') as f:
            doc_content = f.read()
        test_doc = NarrativeDocument()
        test_doc.load_from_json(doc_content)

        session = Session.get()
        db_docs = retrieve_narrative_documents_from_database(session, {1}, "TestLoadingNarrative3")
        self.assertEqual(1, len(db_docs))
        self.assertNotEqual(test_doc, db_docs[0])
        self.assertNotEqual(test_doc.id, db_docs[0].id)
        self.assertEqual(test_doc.abstract, db_docs[0].abstract)
        self.assertEqual(test_doc.title, db_docs[0].title)
        self.assertEqual(test_doc.metadata, db_docs[0].metadata)
        self.assertEqual(test_doc.sections, db_docs[0].sections)

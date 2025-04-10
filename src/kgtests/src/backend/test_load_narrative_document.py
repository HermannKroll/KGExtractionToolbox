import copy
import unittest

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.retrieve import retrieve_narrative_documents_from_database, \
    iterate_over_all_documents_in_collection
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

    def test_replace_existing_document(self):
        test_path = util.get_test_resource_filepath("narrative_documents/example1.json")
        narrative_document_bulk_load(test_path, "TestLoadingNarrative3")

        # parsed json document
        with open(test_path, 'rt') as f:
            doc_content = f.read()
        test_doc = NarrativeDocument()
        test_doc.load_from_json(doc_content)

        session = Session.get()
        db_docs = retrieve_narrative_documents_from_database(session, {0}, "TestLoadingNarrative3")
        self.assertEqual(1, len(db_docs))
        self.assertEqual(test_doc, db_docs[0])
        self.assertEqual(test_doc.id, db_docs[0].id)
        self.assertEqual(test_doc.abstract, db_docs[0].abstract)
        self.assertEqual(test_doc.title, db_docs[0].title)
        self.assertEqual(test_doc.metadata, db_docs[0].metadata)
        self.assertEqual(test_doc.sections, db_docs[0].sections)

        # now replace the document with another document that has the same id
        test_path = util.get_test_resource_filepath("narrative_documents/example1_changed.json")
        narrative_document_bulk_load(test_path, "TestLoadingNarrative3", replace_existing=True)

        # parsed json document
        with open(test_path, 'rt') as f:
            doc_content = f.read()
        test_doc = NarrativeDocument()
        test_doc.load_from_json(doc_content)

        session = Session.get()
        db_docs = retrieve_narrative_documents_from_database(session, {0}, "TestLoadingNarrative3")
        self.assertEqual(1, len(db_docs))
        self.assertEqual(test_doc, db_docs[0])
        self.assertEqual(test_doc.id, db_docs[0].id)
        self.assertEqual(test_doc.abstract, db_docs[0].abstract)
        self.assertEqual(test_doc.title, db_docs[0].title)
        self.assertEqual(test_doc.metadata, db_docs[0].metadata)
        self.assertEqual(test_doc.sections, db_docs[0].sections)

    def test_replace_existing_document_artificial_id(self):
        test_path = util.get_test_resource_filepath("narrative_documents/example1.json")
        narrative_document_bulk_load(test_path, "TestLoadingNarrative4", artificial_document_ids=True)

        # parsed json document
        with open(test_path, 'rt') as f:
            doc_content = f.read()
        test_doc = NarrativeDocument()
        test_doc.load_from_json(doc_content)
        # we will generate the art id 1
        test_doc.id = 1

        session = Session.get()
        db_docs = retrieve_narrative_documents_from_database(session,  {1}, "TestLoadingNarrative4")
        self.assertEqual(1, len(db_docs))
        self.assertEqual(test_doc, db_docs[0])
        self.assertEqual(test_doc.id, db_docs[0].id)
        self.assertEqual(test_doc.abstract, db_docs[0].abstract)
        self.assertEqual(test_doc.title, db_docs[0].title)
        self.assertEqual(test_doc.metadata, db_docs[0].metadata)
        self.assertEqual(test_doc.sections, db_docs[0].sections)

        # now replace the document with another document that has the same id
        test_path = util.get_test_resource_filepath("narrative_documents/example1_changed.json")
        narrative_document_bulk_load(test_path, "TestLoadingNarrative4", artificial_document_ids=True,
                                     replace_existing=True)

        # parsed json document
        with open(test_path, 'rt') as f:
            doc_content = f.read()
        test_doc = NarrativeDocument()
        test_doc.load_from_json(doc_content)
        # we will generate the art id 1
        test_doc.id = 1

        session = Session.get()
        db_docs = retrieve_narrative_documents_from_database(session,  {1}, "TestLoadingNarrative4")
        self.assertEqual(1, len(db_docs))
        self.assertEqual(test_doc, db_docs[0])
        self.assertEqual(test_doc.id, db_docs[0].id)
        self.assertEqual(test_doc.abstract, db_docs[0].abstract)
        self.assertEqual(test_doc.title, db_docs[0].title)
        self.assertEqual(test_doc.metadata, db_docs[0].metadata)
        self.assertEqual(test_doc.sections, db_docs[0].sections)



    def test_replace_many_existing_document_artificial_id(self):
        test_path = util.get_test_resource_filepath("narrative_documents/example2.jsonl")
        narrative_document_bulk_load(test_path, "TestLoadingNarrative5", artificial_document_ids=True)

        # parsed json document
        test_docs = []
        doc_6_stable = None
        with open(test_path, 'rt') as f:
            for idx, line in enumerate(f):
                # we need to set the artificial id when loading
                test_doc = NarrativeDocument()
                test_doc.load_from_json(line)
                test_docs.append(test_doc)
                # artificial ids are increased and each line has one :)
                test_doc.id = idx + 1
                if test_doc.source_id == "Test6":
                    doc_6_stable= test_doc

        session = Session.get()
        db_docs = retrieve_narrative_documents_from_database(session,  {1, 2, 3, 4, 5, 6}, "TestLoadingNarrative5")
        self.assertEqual(len(test_docs), len(db_docs))
        for test_doc, db_doc in zip(test_docs, db_docs):
            self.assertEqual(test_doc.title, db_doc.title)
            self.assertEqual(test_doc.abstract, db_doc.abstract)

        # documents 1-5 are changed. 6 is not changed
        # now replace the document with another document that has the same id
        test_path = util.get_test_resource_filepath("narrative_documents/example2_changed.jsonl")
        narrative_document_bulk_load(test_path, "TestLoadingNarrative5", artificial_document_ids=True,
                                     replace_existing=True)

        # parsed json document
        test_docs_changed = []
        with open(test_path, 'rt') as f:
            for idx, line in enumerate(f):
                test_doc = NarrativeDocument()
                test_doc.load_from_json(line)
                test_docs_changed.append(test_doc)
                # artificial ids are increased and each line has one :)
                test_doc.id = idx + 1

        session = Session.get()
        # we use incremented ids, so the next ids will be.... (6 is skipped because document has not changed)
        db_docs = retrieve_narrative_documents_from_database(session, {7, 8, 9, 10, 11}, "TestLoadingNarrative5")
        self.assertEqual(len(test_docs_changed), len(db_docs))
        for test_doc, db_doc in zip(test_docs_changed, db_docs):
            self.assertEqual(test_doc.title, db_doc.title)
            self.assertEqual(test_doc.abstract, db_doc.abstract)

        # check whether the last document stayed the same
        db_docs = retrieve_narrative_documents_from_database(session, {6}, "TestLoadingNarrative5")
        self.assertEqual(1, len(db_docs))
        self.assertEqual(doc_6_stable.title, db_docs[0].title)
        self.assertEqual(doc_6_stable.abstract, db_docs[0].abstract)
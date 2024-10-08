import copy
import json
import unittest

from sqlalchemy import event
from sqlalchemy.engine import Engine

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.retrieve import retrieve_tagged_documents_from_database, \
    iterate_over_all_documents_in_collection
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

    def test_load_document_translation(self):
        test_path = util.get_test_resource_filepath("loading/example_doc_translation.json")
        document_bulk_load(test_path, "TestLoading4", artificial_document_ids=True)

        # parsed json document
        with open(test_path, 'rt') as f:
            doc_content = f.read()
        test_doc = TaggedDocument(doc_content)

        session = Session.get()
        db_docs = list(iterate_over_all_documents_in_collection(session, "TestLoading4", consider_sections=True))
        self.assertEqual(1, len(db_docs))
        self.assertNotEqual(test_doc, db_docs[0])
        self.assertNotEqual(test_doc.id, db_docs[0].id)
        self.assertEqual(test_doc.abstract, db_docs[0].abstract)
        self.assertEqual(test_doc.title, db_docs[0].title)
        self.assertEqual(test_doc.sections, db_docs[0].sections)

    def test_load_json_line_file(self):
        test_path = util.get_test_resource_filepath("loading/example_json_line.jsonl")
        document_bulk_load(test_path, "TestLoadingJsonLine")

        session = Session.get()
        db_docs = list(iterate_over_all_documents_in_collection(session, "TestLoadingJsonLine", consider_sections=True))
        self.assertEqual(3, len(db_docs))

        self.assertEqual("Comparing Letrozole", db_docs[0].title)
        self.assertEqual("Abstract 1", db_docs[0].abstract)
        self.assertEqual(1, db_docs[0].id)

        self.assertEqual("A Study Investigating", db_docs[1].title)
        self.assertEqual("Abstract 2", db_docs[1].abstract)
        self.assertEqual(2, db_docs[1].id)

        self.assertEqual("Title 3", db_docs[2].title)
        self.assertEqual("Abstract 3", db_docs[2].abstract)
        self.assertEqual(3, db_docs[2].id)

    def test_replace_existing_document(self):
        test_path = util.get_test_resource_filepath("loading/example_doc_classification.json")
        document_bulk_load(test_path, "TestLoadingReplace")


        with open(test_path, 'rt') as f:
            doc_content = f.read()
        test_doc = TaggedDocument(doc_content)

        session = Session.get()
        db_docs = retrieve_tagged_documents_from_database(session, {test_doc.id}, "TestLoadingReplace")

        self.assertEqual(1, len(db_docs))
        self.assertEqual(test_doc, db_docs[0])

        modified_doc_content = copy.deepcopy(test_doc)
        modified_doc_content.title = "Modified " + test_doc.title
        modified_doc_content.abstract = "Modified " + test_doc.abstract
        modified_doc_content.sections[0].text = "Modified " + test_doc.sections[0].text
        modified_doc_content.classification[next(iter(modified_doc_content.classification))] = "Modified " + \
                                                                                               modified_doc_content.classification[
                                                                                                   next(iter(
                                                                                                       modified_doc_content.classification))]

        modified_test_path = util.tmp_rel_path("modified_doc.json")
        with open(modified_test_path, 'w') as f:
            json.dump(modified_doc_content.to_dict(), f)

        document_bulk_load(modified_test_path, "TestLoadingReplace", replace_existing=True)

        db_docs_after_replace = retrieve_tagged_documents_from_database(session, {modified_doc_content.id},
                                                                        "TestLoadingReplace")

        self.assertEqual(1, len(db_docs_after_replace))
        self.assertEqual(modified_doc_content.title, db_docs_after_replace[0].title)
        self.assertEqual(modified_doc_content.abstract, db_docs_after_replace[0].abstract)
        self.assertEqual(modified_doc_content.sections, db_docs_after_replace[0].sections)
        self.assertEqual(modified_doc_content.classification, db_docs_after_replace[0].classification)

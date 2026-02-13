import unittest

from sqlalchemy import update

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Document
from kgextractiontoolbox.backend.retrieve import retrieve_tagged_documents_from_database
from kgextractiontoolbox.backend.update_documents_with_md5_hash import update_all_db_documents_with_md5_hash
from kgextractiontoolbox.document.document import TaggedDocument
from kgextractiontoolbox.document.load_document import document_bulk_load
from kgextractiontoolbox.util.md5 import get_md5hash_from_str
from kgtests import util


class TestComputeMD5hashInDB(unittest.TestCase):

    def test_compute_md5hash_in_db(self):
        # delete existing documents
        session = Session.get()
        session.query(Document).delete()
        session.commit()
        test_path = util.get_test_resource_filepath("loading/example_doc_sections.json")
        document_bulk_load(test_path, "TestLoading1")

        # parsed json document
        with open(test_path, 'rt') as f:
            doc_content = f.read()
        test_doc = TaggedDocument(doc_content)

        db_docs = retrieve_tagged_documents_from_database(session, {test_doc.id}, "TestLoading1")
        self.assertEqual(get_md5hash_from_str(test_doc.get_text_content(sections=True)), db_docs[0].md5hash)

        #delete all md5 hashes
        session.execute(update(Document) .values(md5hash=None))
        session.commit()

        db_docs = retrieve_tagged_documents_from_database(session, {test_doc.id}, "TestLoading1")
        self.assertNotEqual(get_md5hash_from_str(test_doc.get_text_content(sections=True)), db_docs[0].md5hash)

        # update all hashes
        update_all_db_documents_with_md5_hash()

        db_docs = retrieve_tagged_documents_from_database(session, {test_doc.id}, "TestLoading1")
        self.assertEqual(get_md5hash_from_str(test_doc.get_text_content(sections=True)), db_docs[0].md5hash)

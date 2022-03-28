import unittest

import kgtests.util as util
from kgextractiontoolbox.document.count import get_document_ids
from kgextractiontoolbox.document.document import TaggedEntity
from kgextractiontoolbox.document.extract import read_tagged_documents


class TestExtractCount(unittest.TestCase):
    def test_extract(self):
        indocs = util.get_test_resource_filepath("infiles/test_extract")
        tagged_docs = {doc.id: doc for doc in read_tagged_documents(indocs)}
        self.assertSetEqual(set(tagged_docs.keys()), {1, 2, 3, 4, 5297, 5600})
        self.assertEqual("foo", tagged_docs[1].title)
        self.assertIn(TaggedEntity(document=3, start=97, end=111, text="Ethylene Oxide", ent_type="Chemical",
                                   ent_id="MESH:D005027"), tagged_docs[3].tags)
        self.assertIn(TaggedEntity(document=4, start=97, end=111, text="Ethylene Oxide", ent_type="Chemical",
                                   ent_id="MESH:D005027"), tagged_docs[4].tags)

    def test_count(self):
        indocs = util.get_test_resource_filepath("infiles/test_extract")
        ids = get_document_ids(indocs)
        self.assertSetEqual(ids, {1, 2, 3, 4, 5297, 5600})

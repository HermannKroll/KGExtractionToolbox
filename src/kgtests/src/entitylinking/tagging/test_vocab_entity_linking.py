import unittest
import kgextractiontoolbox.entitylinking.vocab_entity_linking as vdp
from kgextractiontoolbox.document.document import TaggedDocument
from kgextractiontoolbox.document.load_document import document_bulk_load
from kgtests import util


class TestVocabEntityLinking(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workdir = util.make_test_tempdir()
        cls.collection = "test_collection"
        cls.vocabulary_file = util.resource_rel_path('vocabs/test_vocab.tsv')
        cls.input_file = util.resource_rel_path('infiles/test_vocab_dictpreprocess/abbreviation_test_allowed.txt')

    def test_tag_collection_without_input_file(self):
        util.clear_database()
        document_bulk_load(self.input_file, self.collection)
        args = [
            *f"-c {self.collection} -v {self.vocabulary_file} --loglevel DEBUG --workdir {self.workdir} -w 1 -y".split()
        ]
        vdp.main(args)
        tags = set(util.get_tags_from_database())
        test_tags = set(TaggedDocument(self.input_file).tags)
        self.assertTrue(tags, test_tags)
        util.clear_database()

    def test_ignore_already_tagged_documents(self):
        with self.assertRaises(SystemExit):
            util.clear_database()
            args = [
                *f"-i {self.input_file} -c {self.collection} -v {self.vocabulary_file} --loglevel DEBUG --workdir {self.workdir} -w 1 -y".split()
            ]
            vdp.main(args)
            #util.clear_doc_tagged_by_table()
            print(set(util.get_docs_tagged_by_from_database()))
            args = [
                *f"-i {self.input_file} -c {self.collection} -v {self.vocabulary_file} --loglevel DEBUG --workdir {self.workdir} -w 1 -y".split()
            ]
            vdp.main(args)
            util.clear_database()

    def test_force_parameter_for_tagging(self):
        util.clear_database()
        args = [
            *f"-i {self.input_file} -c {self.collection} -v {self.vocabulary_file} --loglevel DEBUG --workdir {self.workdir} -w 1 -y".split()
        ]
        vdp.main(args)
        tags1 = set(util.get_docs_tagged_by_from_database())
        # Attempt to tag the same input file with force parameter
        args = [
            *f"-i {self.input_file} -c {self.collection} -v {self.vocabulary_file} --loglevel DEBUG --workdir {self.workdir} -w 1 -y -f".split()
        ]
        vdp.main(args)
        tags2 = set(util.get_docs_tagged_by_from_database())
        self.assertEqual(tags1, tags2)
        util.clear_database()

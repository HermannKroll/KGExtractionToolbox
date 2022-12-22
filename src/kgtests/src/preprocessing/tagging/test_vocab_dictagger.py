import unittest

import kgextractiontoolbox.entitylinking.vocab_entity_linking as vdp
import kgtests
from kgextractiontoolbox.document.document import TaggedDocument
from kgtests import util


class TestVocabDictagger(unittest.TestCase):
    def tagfile_test(self, testfile):
        workdir = kgtests.util.make_test_tempdir()
        args = [
                *f"-i {testfile} -c PREPTEST --loglevel DEBUG -v {util.resource_rel_path('vocabs/test_vocab.tsv')} --workdir {workdir} -w 1 -y".split()
                ]
        vdp.main(args)
        tags = set(util.get_tags_from_database())
        test_tags = set(TaggedDocument(testfile).tags)
        self.assertSetEqual(tags, test_tags)
        util.clear_database()

    def test_custom_abbreviations_and_synonyms(self):
        util.clear_database()
        testfile = util.resource_rel_path('infiles/test_vocab_dictpreprocess/abbreviation_test_allowed.txt')
        self.tagfile_test(testfile)

    def test_vocab_expansion(self):
        util.clear_database()
        self.tagfile_test(util.resource_rel_path('infiles/test_vocab_dictpreprocess/expansion_test.txt'))

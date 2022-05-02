import unittest

from kgextractiontoolbox.cleaning.relation_vocabulary import RelationVocabulary
from kgtests import util


class RelationVocabularyTest(unittest.TestCase):

    def setUp(self) -> None:
        self.vocab = RelationVocabulary()
        self.vocab.load_from_json(util.get_test_resource_filepath('cleaning/pharm_relation_vocab.json'))

    def test_relation_count(self):
        self.assertEqual(10, len(self.vocab.relation_dict))

    def test_relation_treats(self):
        treats_syn = self.vocab.get_relation_synonyms('treats')
        self.assertEqual(8, len(treats_syn))
        for s in ["prevent*", "use", "improv*", "promot*", "sensiti*", "aid", "treat*", "*therap*"]:
            self.assertIn(s, treats_syn)

    def test_relation_inhibits(self):
        inhibits_syn = self.vocab.get_relation_synonyms('inhibits')
        self.assertEqual(4, len(inhibits_syn))
        for s in ["disrupt*", "suppres*", "inhibit*", "disturb*"]:
            self.assertIn(s, inhibits_syn)

    def test_broken_relation_vocab(self):
        vocab2 = RelationVocabulary()
        with self.assertRaises(ValueError):
            vocab2.load_from_json(util.get_test_resource_filepath('cleaning/pharm_relation_vocab_broken.json'))

    def test_broken_relation_vocab_2(self):
        vocab2 = RelationVocabulary()
        with self.assertRaises(ValueError):
            vocab2.load_from_json(util.get_test_resource_filepath('cleaning/pharm_relation_vocab_broken_2.json'))

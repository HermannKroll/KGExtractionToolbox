import unittest

import kgextractiontoolbox.document.document as doc
from kgextractiontoolbox.document.extract import read_tagged_documents
from kgextractiontoolbox.entitylinking.tagging.dictagger import split_indexed_words, DictTagger
from kgextractiontoolbox.entitylinking.tagging.vocabulary import expand_vocabulary_term
from kgtests.util import create_test_kwargs, get_test_resource_filepath, resource_rel_path


class TestDictagger(unittest.TestCase):

    def test_exand_vocab_terms(self):
        self.assertIn('ontologies', expand_vocabulary_term('ontology'))
        self.assertIn('ontologys', expand_vocabulary_term('ontology'))
        self.assertIn('ontology', expand_vocabulary_term('ontology'))

        self.assertIn('color', expand_vocabulary_term('colour'))
        self.assertIn('colours', expand_vocabulary_term('colour'))

        self.assertIn("non-small-cell-lung-cancer", list(expand_vocabulary_term("non-small cell lung cancer")))
        self.assertIn("non small cell lung cancer", list(expand_vocabulary_term("non-small cell lung cancer")))

    def test_split_indexed_words(self):
        content = "This is a water-induced, foobar carbon-copper:"
        indexed = split_indexed_words(content)
        self.assertIn(('water-induced', 10), indexed)
        self.assertIn(('water', 10), indexed)
        self.assertIn(('carbon-copper', 32), indexed)
        self.assertNotIn(('carbon', 32), indexed)

    def test_split_indexed_words_with_multiple_minus(self):
        content_1 = "non-small cell lung cancer"
        indexed_1 = split_indexed_words(content_1)

        content_2 = "non-small-cell lung cancer"
        indexed_2 = split_indexed_words(content_2)
        self.assertNotEqual(indexed_1, indexed_2)

    def test_split_indexed_words_slash(self):
        content = "Simvastatin/Metformin"
        indexed = split_indexed_words(content)
        self.assertIn(('Simvastatin', 0), indexed)
        self.assertIn(('Metformin', 12), indexed)
        self.assertIn(('Simvastatin/Metformin', 0), indexed)

    def test_split_indexed_words_slash_not(self):
        content = "Simvastatin/Metformin"
        indexed = split_indexed_words(content, False)
        self.assertNotIn(('Simvastatin', 0), indexed)
        self.assertNotIn(('Metformin', 12), indexed)
        self.assertIn(('Simvastatin/Metformin', 0), indexed)

    def test_split_indexed_words_end(self):
        content = "matica (Monimiacea) (Monimiaceae)."
        indexed = split_indexed_words(content)
        self.assertIn(('matica', 0), indexed)
        self.assertIn(('Monimiacea', 8), indexed)
        self.assertIn(('Monimiaceae', 21), indexed)

    def test_split_indexed_words_non_characters(self):
        content = "---(Monimiaceae)."
        indexed = split_indexed_words(content)
        self.assertIn(('Monimiaceae', 4), indexed)

        content = "---(Monimi-aceae)."
        indexed = split_indexed_words(content)
        self.assertIn(('Monimi-aceae', 4), indexed)

        content = "Monimi-aceae)."
        indexed = split_indexed_words(content)
        self.assertIn(('Monimi-aceae', 0), indexed)

        content = "Monimiaceae)."
        indexed = split_indexed_words(content)
        self.assertIn(('Monimiaceae', 0), indexed)

        content = "(-Monimiaceae"
        indexed = split_indexed_words(content)
        self.assertIn(('Monimiaceae', 2), indexed)

        content = "(-Monimiaceae"
        indexed = split_indexed_words(content)
        self.assertIn(('Monimiaceae', 2), indexed)

    def test_clean_abbreviations(self):
        ent1 = doc.TaggedEntity(document=1, start=0, end=1, text="AB", ent_type="Drug", ent_id="A")
        not_ent1_full = doc.TaggedEntity(document=1, start=0, end=6, text="ABCDEF", ent_type="Drug", ent_id="B")

        should_be_cleaned_1 = [ent1]
        self.assertEqual(0, len(DictTagger.clean_abbreviation_tags(should_be_cleaned_1)))

        should_be_cleaned_2 = [ent1, not_ent1_full]
        self.assertEqual([not_ent1_full], DictTagger.clean_abbreviation_tags(should_be_cleaned_2))

        ent1_full = doc.TaggedEntity(document=1, start=0, end=6, text="ABCDEF", ent_type="Drug", ent_id="A")
        should_not_be_cleaned = [ent1, ent1_full]
        self.assertEqual(should_not_be_cleaned, DictTagger.clean_abbreviation_tags(should_not_be_cleaned))


if __name__ == '__main__':
    unittest.main()

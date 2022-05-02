import re
import unittest

import kgtests
from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.retrieve import retrieve_tagged_documents_from_database
from kgextractiontoolbox.document.document import TaggedDocument, DocumentSection
from kgextractiontoolbox.entitylinking import classification
from kgextractiontoolbox.entitylinking.classifier import Classifier
from kgtests import util


class TestClassifier(unittest.TestCase):
    pet_rules = util.get_test_resource_filepath("classifier_rules/testrules.txt")

    def test_read_ruleset(self):
        rules, _ = Classifier.read_ruleset(TestClassifier.pet_rules)
        self.assertIn([re.compile(r"kitten\w*\b", re.IGNORECASE)], rules)
        self.assertIn([re.compile(r"dog\w*\b", re.IGNORECASE)], rules)
        self.assertIn([re.compile(r"hamster\b", re.IGNORECASE)], rules)
        self.assertIn([re.compile(r"animal\b", re.IGNORECASE), re.compile(r"house\b", re.IGNORECASE)], rules)

    def test_translate_rule(self):
        rule1 = 'volatile w/1 compound*'
        goal1 = r'volatile \w* compound\w*\b'
        self.assertEqual(re.compile(goal1, re.IGNORECASE), Classifier.compile_entry_to_regex(rule1))

        # apply regex
        re1_compiled = Classifier.compile_entry_to_regex(rule1)
        test1 = 'volatile chinese compounds'
        self.assertTrue(re.match(re1_compiled, test1))
        test1_a = 'volatile chinese compoundsasdfdsafa'
        self.assertTrue(re.match(re1_compiled, test1_a))
        test1_b = 'volatile compound'
        self.assertFalse(re.match(re1_compiled, test1_b))

        rule2 = 'Traditional w/1 Medicine'
        goal2 = r'Traditional \w* Medicine\b'
        self.assertEqual(re.compile(goal2, re.IGNORECASE), Classifier.compile_entry_to_regex(rule2))

        # apply regex
        re2_compiled = Classifier.compile_entry_to_regex(rule2)
        test2 = 'Traditional chinese Medicine'
        self.assertTrue(re.match(re2_compiled, test2))
        test2_a = 'Traditional Medicine'
        self.assertFalse(re.match(re2_compiled, test2_a))

        rule3 = rule1 + 'AND' + rule2
        self.assertIn(re.compile(goal1, re.IGNORECASE), Classifier.compile_line_to_regex(rule3))
        self.assertIn(re.compile(goal2, re.IGNORECASE), Classifier.compile_line_to_regex(rule3))

        rule3 = 'Traditional w/2 Medicine'
        goal3 = r'Traditional \w* \w* Medicine\b'
        self.assertEqual(re.compile(goal3, re.IGNORECASE), Classifier.compile_entry_to_regex(rule3))

        rule4 = 'Traditional w/5 Medicine'
        goal4 = r'Traditional \w* \w* \w* \w* \w* Medicine\b'
        self.assertEqual(re.compile(goal4, re.IGNORECASE), Classifier.compile_entry_to_regex(rule4))

    def test_classify(self):
        classfier = Classifier("pet", rule_path=TestClassifier.pet_rules)
        positive_docs = [
            TaggedDocument(title="some animals", abstract="Some people keep an animal in their house."),
            TaggedDocument(title="a cute hamster", abstract=""),
            TaggedDocument(title="two kittens for sale")
        ]
        negative_docs = [
            TaggedDocument(title="this has nothing to do with an animal"),
            TaggedDocument(title="this is about hamsters")
        ]
        for doc in positive_docs + negative_docs:
            classfier.classify_document(doc)

        for doc in positive_docs:
            self.assertIn('pet', doc.classification)
        for doc in negative_docs:
            self.assertNotIn('pet', doc.classification, msg=f"{doc}: false positive")

    def test_classify_sections(self):
        classfier = Classifier("pet", rule_path=TestClassifier.pet_rules)
        positive_docs = [
            TaggedDocument(title="a", abstract=""),
            TaggedDocument(title="a", abstract=""),
            TaggedDocument(title="a")
        ]
        positive_docs[0].sections.append(DocumentSection(0, "test", "some animals"))
        positive_docs[0].sections.append(DocumentSection(0, "test", "Some people keep an animal in their house."))

        positive_docs[1].sections.append(DocumentSection(0, "test", "a cute hamster"))
        positive_docs[2].sections.append(DocumentSection(0, "test", "two kittens for sale"))

        negative_docs = [
            TaggedDocument(title="this has nothing to do with an animal"),
            TaggedDocument(title="this is about hamsters")
        ]

        # no positive matches because sections are not considered
        for doc in positive_docs + negative_docs:
            classfier.classify_document(doc)

        for doc in positive_docs:
            self.assertNotIn('pet', doc.classification)
        for doc in negative_docs:
            self.assertNotIn('pet', doc.classification, msg=f"{doc}: false positive")

        # test consider sections
        for doc in positive_docs + negative_docs:
            classfier.classify_document(doc, consider_sections=True)

        for doc in positive_docs:
            self.assertIn('pet', doc.classification)
        for doc in negative_docs:
            self.assertNotIn('pet', doc.classification, msg=f"{doc}: false positive")

    def test_classification_positions(self):
        classfier = Classifier("pet", rule_path=TestClassifier.pet_rules)
        positive_docs = [
            TaggedDocument(title="a", abstract="Some people keep an animal in their house."),
            TaggedDocument(title="a cute hamster", abstract=""),
            TaggedDocument(title="kittens for sale")
        ]

        for doc in positive_docs:
            classfier.classify_document(doc)

        positions0 = str(positive_docs[0].classification['pet'])
        self.assertIn('(22, 28)', positions0)
        self.assertIn('animal', positions0)
        self.assertIn('(38, 43)', positions0)
        self.assertIn('house', positions0)
        self.assertIn('AND', positions0)

        positions1 = str(positive_docs[1].classification['pet'])
        self.assertIn('(7, 14)', positions1)
        self.assertIn('hamster', positions1)

        positions2 = str(positive_docs[2].classification['pet'])
        self.assertIn('(0, 7)', positions2)
        self.assertIn('kittens', positions2)

    def test_classification_explanation(self):
        classfier = Classifier("pet", rule_path=TestClassifier.pet_rules)
        doc1 = TaggedDocument(title="kittens for sale")
        classfier.classify_document(doc1)
        self.assertEqual('kitten*:kittens(0, 7)', doc1.classification['pet'])

        doc2 = TaggedDocument(title="Some people keep an animal in their house")
        classfier.classify_document(doc2)
        self.assertEqual('animal:animal(20, 26) AND house:house(36, 41)',
                         doc2.classification['pet'])

    def test_classification_ignore_sections(self):
        in_file = util.get_test_resource_filepath("infiles/test_classifyer/fulltext_test.json")
        workdir = kgtests.util.make_test_tempdir()
        args = [
            *f"-i {in_file} -c CLASSIFICATION_TEST_1 --loglevel DEBUG --cls pet --workdir {workdir} -w 2 -y -r {self.pet_rules}".split()
        ]
        classification.main(args)

        session = Session.get()
        classified_documents = retrieve_tagged_documents_from_database(session, document_ids={1, 2, 3},
                                                                       document_collection="CLASSIFICATION_TEST_1")
        positive_docs = {1}
        for doc in classified_documents:
            if 'pet' in doc.classification:
                self.assertIn(doc.id, positive_docs)

    def test_dictpreprocess_include_sections(self):
        in_file = util.get_test_resource_filepath("infiles/test_preprocess/fulltext_19128.json")
        workdir = kgtests.util.make_test_tempdir()
        args = [
            *f"-i {in_file} -c CLASSIFICATION_TEST_2 --loglevel DEBUG --sections --cls pet --workdir {workdir} -w 2 -y -r {self.pet_rules}".split()
        ]
        classification.main(args)
        session = Session.get()
        classified_documents = retrieve_tagged_documents_from_database(session, document_ids={1, 2, 3},
                                                                       document_collection="CLASSIFICATION_TEST_1")
        positive_docs = {1, 2, 3}
        for doc in classified_documents:
            if 'pet' in doc.classification:
                self.assertIn(doc.id, positive_docs)

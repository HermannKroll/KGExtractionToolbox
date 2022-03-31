import unittest

from sqlalchemy import update

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Document, Sentence, Predication
from kgextractiontoolbox.cleaning.canonicalize_predicates import is_predicate_equal_to_vocab, transform_predicate, \
    canonicalize_predication_table
from kgextractiontoolbox.cleaning.relation_vocabulary import RelationVocabulary
from kgtests import util


class CanonicalizePredicateTestCase(unittest.TestCase):

    def setUp(self) -> None:
        session = Session.get()
        documents = [dict(id=1, collection="Test_Canonicalize", title="ABC", abstract=""),
                     dict(id=2, collection="Test_Canonicalize", title="DEF", abstract="")]
        Document.bulk_insert_values_into_table(session, documents)

        sentences = [dict(id=1, document_id=1, document_collection="Test_Canonicalize", text="Hello", md5hash="1"),
                     dict(id=2, document_id=1, document_collection="Test_Canonicalize", text="World", md5hash="2")]
        Sentence.bulk_insert_values_into_table(session, sentences)

        predications = [dict(id=1,
                             document_id=1, document_collection="Test_Canonicalize",
                             subject_id="A", subject_type="Drug", subject_str="",
                             predicate="therapies",
                             object_id="B", object_type="Disease", object_str="",
                             sentence_id=1, extraction_type="PathIE"),
                        dict(id=2,
                             document_id=1, document_collection="Test_Canonicalize",
                             subject_id="A", subject_type="Disease", subject_str="",
                             predicate="therapy",
                             object_id="B", object_type="Disease", object_str="",
                             sentence_id=1, extraction_type="PathIE"),
                        dict(id=3,
                             document_id=2, document_collection="Test_Canonicalize",
                             subject_id="A", subject_type="Disease", subject_str="",
                             predicate="side effect",
                             object_id="B", object_type="Disease", object_str="",
                             sentence_id=2, extraction_type="PathIE"),
                        dict(id=4,
                             document_id=2, document_collection="Test_Canonicalize",
                             subject_id="A", subject_type="Disease", subject_str="",
                             predicate="side effects",
                             object_id="B", object_type="Disease", object_str="",
                             sentence_id=2, extraction_type="PathIE"),
                        dict(id=5,
                             document_id=2, document_collection="Test_Canonicalize",
                             subject_id="A", subject_type="Gene", subject_str="",
                             predicate="induces",
                             object_id="B", object_type="Gene", object_str="",
                             sentence_id=2, extraction_type="PathIE"),
                        dict(id=6,
                             document_id=2, document_collection="Test_Canonicalize",
                             subject_id="A", subject_type="Gene", subject_str="",
                             predicate="induc",
                             object_id="B", object_type="Gene", object_str="",
                             sentence_id=2, extraction_type="PathIE"),
                        dict(id=7,
                             document_id=7, document_collection="Test_Canonicalize_Wrong",
                             subject_id="A", subject_type="Gene", subject_str="",
                             predicate="induces",
                             object_id="B", object_type="Gene", object_str="",
                             sentence_id=2, extraction_type="PathIE"),
                        dict(id=8,
                             document_id=7, document_collection="Test_Canonicalize",
                             subject_id="A", subject_type="Gene", subject_str="",
                             predicate="induces",
                             object_id="B", object_type="Gene", object_str="",
                             sentence_id=2, extraction_type="PathIE"),
                        dict(id=9,
                             document_id=7, document_collection="Test_Canonicalize",
                             subject_id="A", subject_type="Gene", subject_str="",
                             predicate="induces",
                             object_id="B", object_type="Gene", object_str="",
                             sentence_id=2, extraction_type="PathIE")
                        ]

        Predication.bulk_insert_values_into_table(session, predications)

    def test_is_predicate_equal_to_vocab(self):
        self.assertTrue(is_predicate_equal_to_vocab("produce", "produce"))
        self.assertTrue(is_predicate_equal_to_vocab("produce", "*oduce"))
        self.assertTrue(is_predicate_equal_to_vocab("produce", "prod*"))
        self.assertTrue(is_predicate_equal_to_vocab("produce", "produc*"))
        self.assertTrue(is_predicate_equal_to_vocab("produce", "*duc*"))

        self.assertTrue(is_predicate_equal_to_vocab("inhibitory", "inhibit*"))

    def test_transform_predicate(self):
        self.assertEqual("produce", transform_predicate("produce"))
        self.assertEqual("produce", transform_predicate("produced"))
        self.assertEqual("produce", transform_predicate("produces"))

    def test_canonicalize_without_word2vec_model(self):
        vocab = RelationVocabulary()
        vocab.load_from_json(util.get_test_resource_filepath('cleaning/pharm_relation_vocab.json'))
        canonicalize_predication_table(relation_vocabulary=vocab, document_collection="Test_Canonicalize",
                                       min_predicate_threshold=0)

        session = Session.get()
        self.assertEqual("treats",
                         session.query(Predication.relation).filter(Predication.id == 1).first()[0])
        self.assertEqual("treats",
                         session.query(Predication.relation).filter(Predication.id == 2).first()[0])
        self.assertEqual("induces",
                         session.query(Predication.relation).filter(Predication.id == 3).first()[0])
        self.assertEqual("induces",
                         session.query(Predication.relation).filter(Predication.id == 4).first()[0])
        self.assertEqual("induces",
                         session.query(Predication.relation).filter(Predication.id == 5).first()[0])
        self.assertIsNone(session.query(Predication.relation).filter(Predication.id == 6).first()[0])
        self.assertIsNone(session.query(Predication.relation).filter(Predication.id == 7).first()[0])

    def test_canonicalize_without_word2vec_model_threshold_too_high(self):
        vocab = RelationVocabulary()
        vocab.load_from_json(util.get_test_resource_filepath('cleaning/pharm_relation_vocab.json'))
        session = Session.get()
        session.execute(update(Predication).values(relation=None)
                        .where(Predication.document_collection == "Test_Canonicalize"))
        session.commit()

        canonicalize_predication_table(relation_vocabulary=vocab, document_collection="Test_Canonicalize",
                                       min_predicate_threshold=1)
        self.assertIsNone(session.query(Predication.relation).filter(Predication.id == 1).first()[0])
        self.assertIsNone(session.query(Predication.relation).filter(Predication.id == 2).first()[0])
        self.assertIsNone(session.query(Predication.relation).filter(Predication.id == 3).first()[0])
        self.assertIsNone(session.query(Predication.relation).filter(Predication.id == 4).first()[0])
        self.assertIsNone(session.query(Predication.relation).filter(Predication.id == 5).first()[0])
        self.assertIsNone(session.query(Predication.relation).filter(Predication.id == 6).first()[0])
        self.assertIsNone(session.query(Predication.relation).filter(Predication.id == 7).first()[0])

    def test_canonicalize_without_word2vec_model_threshold(self):
        vocab = RelationVocabulary()
        vocab.load_from_json(util.get_test_resource_filepath('cleaning/pharm_relation_vocab.json'))
        session = Session.get()
        session.execute(update(Predication).values(relation=None)
                        .where(Predication.document_collection == "Test_Canonicalize"))
        session.commit()

        canonicalize_predication_table(relation_vocabulary=vocab, document_collection="Test_Canonicalize",
                                       min_predicate_threshold=0.3)
        self.assertIsNone(session.query(Predication.relation).filter(Predication.id == 1).first()[0])
        self.assertIsNone(session.query(Predication.relation).filter(Predication.id == 2).first()[0])
        self.assertIsNone(session.query(Predication.relation).filter(Predication.id == 3).first()[0])
        self.assertIsNone(session.query(Predication.relation).filter(Predication.id == 4).first()[0])
        self.assertIsNone(session.query(Predication.relation).filter(Predication.id == 6).first()[0])
        self.assertIsNone(session.query(Predication.relation).filter(Predication.id == 7).first()[0])

        self.assertEqual("induces",
                         session.query(Predication.relation).filter(Predication.id == 5).first()[0])
        self.assertEqual("induces",
                         session.query(Predication.relation).filter(Predication.id == 8).first()[0])
        self.assertEqual("induces",
                         session.query(Predication.relation).filter(Predication.id == 9).first()[0])

    def test_canonicalize_without_word2vec_model_output_file(self):
        vocab = RelationVocabulary()
        vocab.load_from_json(util.get_test_resource_filepath('cleaning/pharm_relation_vocab.json'))
        output_file = util.tmp_rel_path("canonicalize_output_test.tsv")
        canonicalize_predication_table(relation_vocabulary=vocab,
                                       output_distances=output_file,
                                       document_collection="Test_Canonicalize",
                                       min_predicate_threshold=0)

        output_results = set()
        with open(output_file, 'rt') as f:
            for line in f:
                output_results.add(tuple(line.strip().split('\t')))

        self.assertIn(("therapy", "*therap*", '1.0'), output_results)
        self.assertIn(("therapy", "induces", '0.0'), output_results)
        self.assertIn(("therapies", "*therap*", '1.0'), output_results)
        self.assertIn(("side effect", "side effect*", '1.0'), output_results)
        self.assertIn(("side effects", "side effect*", '1.0'), output_results)
        self.assertIn(("induc", "induces", '0.0'), output_results)
        self.assertIn(("induces", "induces", '1.0'), output_results)

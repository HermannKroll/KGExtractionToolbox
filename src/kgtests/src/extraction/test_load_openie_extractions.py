from unittest import TestCase

from sqlalchemy import delete

from kgextractiontoolbox.extraction.loading.load_extractions import PRED
from kgextractiontoolbox.extraction.loading.load_openie_extractions import load_openie_tuples, OpenIEEntityFilterMode, \
    get_subject_and_object_entities, clean_tuple_predicate_based
from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Predication
from kgextractiontoolbox.document.load_document import document_bulk_load
from kgtests import util


class LoadExtractionsTestCase(TestCase):

    def setUp(self) -> None:
        documents_file = util.get_test_resource_filepath("extraction/documents_1.pubtator")
        test_mapping = {"Chemical": ("Chemical", "1.0"), "Disease": ("Diseasetagger", "1.0")}
        document_bulk_load(documents_file, "Test_Load_OpenIE_1", tagger_mapping=test_mapping, ignore_tags=False)

    def test_detect_subjects_and_objects(self):
        doc_tags = [("E1", "this", "ThisType"),
                    ("E1", "test", "TestType")]

        s, o = get_subject_and_object_entities(doc_tags, "this", "test",
                                               entity_filter=OpenIEEntityFilterMode.EXACT_ENTITY_FILTER)
        self.assertEqual(('this', 'E1', 'ThisType'), s[0])
        self.assertEqual(('test', 'E1', 'TestType'), o[0])

        s, o = get_subject_and_object_entities(doc_tags, "This", "Test",
                                               entity_filter=OpenIEEntityFilterMode.EXACT_ENTITY_FILTER)
        self.assertEqual(('this', 'E1', 'ThisType'), s[0])
        self.assertEqual(('test', 'E1', 'TestType'), o[0])

        s, o = get_subject_and_object_entities(doc_tags, "this", "test",
                                               entity_filter=OpenIEEntityFilterMode.PARTIAL_ENTITY_FILTER)
        self.assertEqual(('this', 'E1', 'ThisType'), s[0])
        self.assertEqual(('test', 'E1', 'TestType'), o[0])

        s, o = get_subject_and_object_entities(doc_tags, "This", "Test",
                                               entity_filter=OpenIEEntityFilterMode.PARTIAL_ENTITY_FILTER)
        self.assertEqual(('this', 'E1', 'ThisType'), s[0])
        self.assertEqual(('test', 'E1', 'TestType'), o[0])

        s, o = get_subject_and_object_entities(doc_tags, "this is", "a test",
                                               entity_filter=OpenIEEntityFilterMode.PARTIAL_ENTITY_FILTER)
        self.assertEqual(('this', 'E1', 'ThisType'), s[0])
        self.assertEqual(('test', 'E1', 'TestType'), o[0])

        s, o = get_subject_and_object_entities(doc_tags, "This is", "A Test",
                                               entity_filter=OpenIEEntityFilterMode.PARTIAL_ENTITY_FILTER)
        self.assertEqual(('this', 'E1', 'ThisType'), s[0])
        self.assertEqual(('test', 'E1', 'TestType'), o[0])

        s, o = get_subject_and_object_entities(doc_tags, "this is", "a test",
                                               entity_filter=OpenIEEntityFilterMode.NO_ENTITY_FILTER)
        self.assertEqual(('this is', 'this is', 'Unknown'), s[0])
        self.assertEqual(('a test', 'a test', 'Unknown'), o[0])

    def test_load_openie_extrations_no_entity_filter(self):
        session = Session.get()
        session.execute(delete(Predication).where(Predication.document_collection == 'Test_Load_OpenIE_1'))
        session.commit()

        openie_file = util.get_test_resource_filepath("extraction/openie_extractions_1.tsv")
        load_openie_tuples(openie_file, document_collection="Test_Load_OpenIE_1",
                           entity_filter=OpenIEEntityFilterMode.NO_ENTITY_FILTER,
                           filter_predicate_str=True,
                           swap_passive_voice=True,
                           keep_be_and_have=False)

        self.assertEqual(8, session.query(Predication).filter(
            Predication.document_collection == "Test_Load_OpenIE_1").count())
        tuples = set()
        for q in Predication.iterate_predications_joined_sentences(session, document_collection="Test_Load_OpenIE_1"):
            tuples.add((q.Predication.document_id, q.Predication.document_collection,
                        q.Predication.subject_id, q.Predication.subject_type, q.Predication.subject_str,
                        q.Predication.predicate, q.Predication.relation,
                        q.Predication.object_id, q.Predication.object_type, q.Predication.object_str,
                        q.Predication.extraction_type, q.Sentence.text))

        self.assertIn((22836123, 'Test_Load_OpenIE_1',
                       'tacrolimus', 'Unknown', 'tacrolimus',
                       'induce', None,
                       'onset scleroderma crisis', 'Unknown', 'onset scleroderma crisis', 'OpenIE',
                       'Late - onset scleroderma renal crisis induced by tacrolimus and prednisolone : a case report .'),
                      tuples)
        self.assertIn((22836123, 'Test_Load_OpenIE_1',
                       'tacrolimus', 'Unknown', 'tacrolimus',
                       'induce', None,
                       'onset scleroderma renal crisis', 'Unknown', 'onset scleroderma renal crisis', 'OpenIE',
                       'Late - onset scleroderma renal crisis induced by tacrolimus and prednisolone : a case report .'),
                      tuples)
        self.assertIn((22836123, 'Test_Load_OpenIE_1',
                       'major risk factor', 'Unknown', 'major risk factor',
                       'recognize', None,
                       'moderate', 'Unknown', 'moderate', 'OpenIE',
                       'Moderate to high dose corticosteroid use is recognized as a major risk factor for SRC .'),
                      tuples)
        self.assertIn((22836123, 'Test_Load_OpenIE_1',
                       'risk factor for src', 'Unknown', 'risk factor for src',
                       'recognize', None,
                       'moderate', 'Unknown', 'moderate', 'OpenIE',
                       'Moderate to high dose corticosteroid use is recognized as a major risk factor for SRC .'),
                      tuples)
        self.assertIn((22836123, 'Test_Load_OpenIE_1',
                       'major risk factor for src', 'Unknown', 'major risk factor for src',
                       'recognize', None,
                       'moderate', 'Unknown', 'moderate', 'OpenIE',
                       'Moderate to high dose corticosteroid use is recognized as a major risk factor for SRC .'),
                      tuples)
        self.assertIn((22836123, 'Test_Load_OpenIE_1',
                       'risk factor', 'Unknown', 'risk factor',
                       'recognize', None,
                       'moderate', 'Unknown', 'moderate', 'OpenIE',
                       'Moderate to high dose corticosteroid use is recognized as a major risk factor for SRC .'),
                      tuples)
        self.assertIn((22836123, 'Test_Load_OpenIE_1',
                       'cyclosporine patients', 'Unknown', 'cyclosporine patients',
                       'precipitate', None,
                       'have reports', 'Unknown', 'have reports', 'OpenIE',
                       'Furthermore , there have been reports of thrombotic microangiopathy precipitated by cyclosporine in patients with SSc .'),
                      tuples)
        self.assertIn((22836123, 'Test_Load_OpenIE_1',
                       'cyclosporine patients ssc', 'Unknown', 'cyclosporine patients ssc',
                       'precipitate', None,
                       'have reports', 'Unknown', 'have reports', 'OpenIE',
                       'Furthermore , there have been reports of thrombotic microangiopathy precipitated by cyclosporine in patients with SSc .'),
                      tuples)

    def test_load_openie_extrations_partial_entity_filter(self):
        session = Session.get()
        session.execute(delete(Predication).where(Predication.document_collection == 'Test_Load_OpenIE_1'))
        session.commit()

        openie_file = util.get_test_resource_filepath("extraction/openie_extractions_1.tsv")
        load_openie_tuples(openie_file, document_collection="Test_Load_OpenIE_1",
                           filter_predicate_str=True,
                           swap_passive_voice=True,
                           entity_filter=OpenIEEntityFilterMode.PARTIAL_ENTITY_FILTER)

        self.assertEqual(1, session.query(Predication).filter(
            Predication.document_collection == "Test_Load_OpenIE_1").count())
        tuples = set()
        for q in Predication.iterate_predications_joined_sentences(session, document_collection="Test_Load_OpenIE_1"):
            tuples.add((q.Predication.document_id, q.Predication.document_collection,
                        q.Predication.subject_id, q.Predication.subject_type, q.Predication.subject_str,
                        q.Predication.predicate, q.Predication.relation,
                        q.Predication.object_id, q.Predication.object_type, q.Predication.object_str,
                        q.Predication.extraction_type, q.Sentence.text))

        self.assertIn((22836123, 'Test_Load_OpenIE_1',
                       'D016559', 'Chemical', 'tacrolimus',
                       'induce', None,
                       'D007674', 'Disease', 'scleroderma renal crisis', 'OpenIE',
                       'Late - onset scleroderma renal crisis induced by tacrolimus and prednisolone : a case report .'),
                      tuples)

    def test_load_openie_extrations_exact_entity_filter(self):
        session = Session.get()
        session.execute(delete(Predication).where(Predication.document_collection == 'Test_Load_OpenIE_1'))
        session.commit()

        openie_file = util.get_test_resource_filepath("extraction/openie_extractions_1.tsv")
        load_openie_tuples(openie_file, document_collection="Test_Load_OpenIE_1",
                           filter_predicate_str=True,
                           swap_passive_voice=True,
                           entity_filter=OpenIEEntityFilterMode.EXACT_ENTITY_FILTER)

        self.assertEqual(0, session.query(Predication).filter(
            Predication.document_collection == "Test_Load_OpenIE_1").count())

    def test_clean_tuple_predicate_based_not(self):
        example1 = PRED(1, "USA", "will not tolerate", "be not tolerate", "UDSSR", 0.0, "USA will not tolerate UDSSR.",
                        "USA", "USA", "State", "UDSSR", "UDSSR", "State")

        cleaned = clean_tuple_predicate_based(example1)
        self.assertEqual(cleaned, example1)

        example2 = PRED(1, "USA", "will tolerate", "be tolerate", "UDSSR", 0.0, "USA will not tolerate UDSSR.",
                        "USA", "USA", "State", "UDSSR", "UDSSR", "State")

        cleaned2 = clean_tuple_predicate_based(example2)
        self.assertEqual(cleaned2, example2)

    def test_clean_tuple_predicate_based_ignore_be(self):
        example1 = PRED(1, "USA", "will not tolerate", "be not tolerate", "UDSSR", 0.0, "USA will not tolerate UDSSR.",
                        "USA", "USA", "State", "UDSSR", "UDSSR", "State")

        cleaned = clean_tuple_predicate_based(example1, keep_be_and_have=False, filter_predicate_str=True)
        self.assertNotEqual(cleaned, example1)

        correct1 = PRED(1, "USA", "will not tolerate", "not tolerate", "UDSSR", 0.0, "USA will not tolerate UDSSR.",
                        "USA", "USA", "State", "UDSSR", "UDSSR", "State")
        self.assertEqual(cleaned, correct1)

        example2 = PRED(1, "USA", "will tolerate", "be tolerate", "UDSSR", 0.0, "USA will not tolerate UDSSR.",
                        "USA", "USA", "State", "UDSSR", "UDSSR", "State")
        cleaned2 = clean_tuple_predicate_based(example2, keep_be_and_have=False, filter_predicate_str=True)
        self.assertNotEqual(cleaned2, example2)
        correct2 = PRED(1, "USA", "will tolerate", "tolerate", "UDSSR", 0.0, "USA will not tolerate UDSSR.",
                        "USA", "USA", "State", "UDSSR", "UDSSR", "State")
        self.assertEqual(cleaned2, correct2)

    def test_clean_tuple_predicate_based_passive_voice(self):
        # this triple should be flipped (passive voice)
        example3 = PRED(1, "USA", "be tolerated by", "be tolerate by", "UDSSR", 0.0, "USA will not tolerate UDSSR.",
                        "USA", "USA", "State", "UDSSR", "UDSSR", "State")
        correct3 = PRED(1, "UDSSR", "be tolerated by", "tolerate", "USA", 0.0, "USA will not tolerate UDSSR.",
                        "UDSSR", "UDSSR", "State", "USA", "USA", "State")

        cleaned3 = clean_tuple_predicate_based(example3, swap_passive_voice=True)
        self.assertNotEqual(cleaned3, example3)
        self.assertEqual(cleaned3, correct3)

    def test_clean_tuple_predicate_based_no_passive_voice_swap(self):
        # this triple should be flipped (passive voice)
        example3 = PRED(1, "USA", "be tolerated by", "be tolerate by", "UDSSR", 0.0, "USA will not tolerate UDSSR.",
                        "USA", "USA", "State", "UDSSR", "UDSSR", "State")
        correct3 = PRED(1, "UDSSR", "be tolerated by", "be tolerate by", "USA", 0.0, "USA will not tolerate UDSSR.",
                        "UDSSR", "UDSSR", "State", "USA", "USA", "State")

        cleaned3 = clean_tuple_predicate_based(example3, swap_passive_voice=False)
        self.assertNotEqual(cleaned3, correct3)
        self.assertEqual(cleaned3, example3)

    def test_clean_tuple_predicate_based_fails_to(self):
        example = PRED(1, "USA", "fails to offer", "fail to offer", "UDSSR", 0.0, "USA fails to offer the UDSSR.",
                       "USA", "USA", "State", "UDSSR", "UDSSR", "State")

        cleaned = clean_tuple_predicate_based(example, filter_predicate_str=True)
        self.assertNotEqual(cleaned, example)
        correct = PRED(1, "USA", "fails to offer", "fail offer", "UDSSR", 0.0, "USA fails to offer the UDSSR.",
                       "USA", "USA", "State", "UDSSR", "UDSSR", "State")
        self.assertEqual(cleaned, correct)

    def test_clean_tuple_predicate_based_mate(self):
        # Example extraction:
        # 995    Henry A. Wallace,        is mate of from          be mate of from       Franklin D. Roosevelt  0.16
        #  Letter from Govenor Herbert H. Lehman to William Wallace Farley, October 22, 1940 inviting Mr.
        #  Farley to a supper party in honor of Henry A. Wallace, Vice Presidential Candidate and running mate of
        # Franklin D. Roosevelt in the 1940 U.S. Presidential Election..
        example = PRED(1, "Henry A. Wallace", "is mate of from", "be mate of from", "Franklin D. Roosevelt", 0.0,
                       ".",
                       "Henry A. Wallace", "Henry A. Wallace", "Person",
                       "Franklin D. Roosevelt", "Franklin D. Roosevelt", "Person")

        cleaned = clean_tuple_predicate_based(example, filter_predicate_str=True)
        self.assertNotEqual(cleaned, example)
        correct = PRED(1, "Henry A. Wallace", "is mate of from", "be mate", "Franklin D. Roosevelt", 0.0,
                       ".",
                       "Henry A. Wallace", "Henry A. Wallace", "Person",
                       "Franklin D. Roosevelt", "Franklin D. Roosevelt", "Person")
        self.assertEqual(cleaned, correct)

    def test_clean_tuple_keep_original_predicate(self):
        example = PRED(1, "USA", "fails to offer", "fail to offer", "UDSSR", 0.0, "USA fails to offer the UDSSR.",
                       "USA", "USA", "State", "UDSSR", "UDSSR", "State")
        correct = PRED(1, "USA", "fails to offer", "fails to offer", "UDSSR", 0.0, "USA fails to offer the UDSSR.",
                       "USA", "USA", "State", "UDSSR", "UDSSR", "State")

        cleaned = clean_tuple_predicate_based(example, keep_original_predicate=True)
        self.assertNotEqual(example, cleaned)
        self.assertEqual(correct, cleaned)

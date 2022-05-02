from unittest import TestCase

from sqlalchemy import delete

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Predication
from kgextractiontoolbox.extraction.loading.load_pathie_extractions import load_pathie_extractions
from kgextractiontoolbox.document.load_document import document_bulk_load
from kgtests import util


class LoadExtractionsTestCase(TestCase):

    def setUp(self) -> None:
        documents_file = util.get_test_resource_filepath("extraction/documents_1.pubtator")
        document_bulk_load(documents_file, "Test_Load_PathIE_1")

    def test_load_pathie_extrations(self):
        session = Session.get()
        session.execute(delete(Predication).where(Predication.document_collection == 'Test_Load_PathIE_1'))
        session.commit()

        pathie_file = util.get_test_resource_filepath("extraction/pathie_extractions_1.tsv")
        load_pathie_extractions(pathie_file, document_collection="Test_Load_PathIE_1", extraction_type="PathIE")

        self.assertEqual(20, session.query(Predication).filter(
            Predication.document_collection == "Test_Load_PathIE_1").count())
        tuples = set()
        for q in Predication.iterate_predications_joined_sentences(session, document_collection="Test_Load_PathIE_1"):
            tuples.add((q.Predication.document_id, q.Predication.document_collection,
                        q.Predication.subject_id, q.Predication.subject_type, q.Predication.subject_str,
                        q.Predication.predicate, q.Predication.relation,
                        q.Predication.object_id, q.Predication.object_type, q.Predication.object_str,
                        q.Predication.extraction_type, q.Sentence.text))

        self.assertIn((7121659, 'Test_Load_PathIE_1',
                       'D058186', 'Disease', 'acute renal failure',
                       'induce', None,
                       'D012293', 'Chemical', 'rifampicin', 'PathIE',
                       '5 patients with acute renal failure (3 with thrombopenia and hemolysis) induced by the reintroduction of rifampicin are described.'),
                      tuples)
        self.assertIn((7121659, 'Test_Load_PathIE_1',
                       'D012293', 'Chemical', 'rifampicin',
                       'induce', None,
                       'D013921', 'Disease', 'thrombopenia', 'PathIE',
                       '5 patients with acute renal failure (3 with thrombopenia and hemolysis) induced by the reintroduction of rifampicin are described.'),
                      tuples)
        self.assertIn((7121659, 'Test_Load_PathIE_1',
                       'D012293', 'Chemical', 'rifampicin',
                       'induce', None,
                       'D006461', 'Disease', 'hemolysis', 'PathIE',
                       '5 patients with acute renal failure (3 with thrombopenia and hemolysis) induced by the reintroduction of rifampicin are described.'),
                      tuples)

        self.assertIn((23952588, 'Test_Load_PathIE_1',
                       'D010300', 'Disease', 'PD',
                       'study', None,
                       'D004409', 'Disease', 'dyskinesia', 'PathIE',
                       'We studied the prevalence and predictors of levodopa-induced dyskinesia among multiethnic Malaysian patients with PD.'),
                      tuples)
        self.assertIn((23952588, 'Test_Load_PathIE_1',
                       'D004409', 'Disease', 'dyskinesia',
                       'study', None,
                       'D010300', 'Disease', 'PD', 'PathIE',
                       'We studied the prevalence and predictors of levodopa-induced dyskinesia among multiethnic Malaysian patients with PD.'),
                      tuples)

    def test_load_pathie_extrations_not_symmetric(self):
        session = Session.get()
        session.execute(delete(Predication).where(Predication.document_collection == 'Test_Load_PathIE_1'))
        session.commit()
        pathie_file = util.get_test_resource_filepath("extraction/pathie_extractions_1.tsv")
        load_pathie_extractions(pathie_file, document_collection="Test_Load_PathIE_1", extraction_type="PathIE",
                                load_symmetric=False)

        self.assertEqual(10, session.query(Predication).filter(
            Predication.document_collection == "Test_Load_PathIE_1").count())
        tuples = set()
        for q in Predication.iterate_predications_joined_sentences(session,
                                                                   document_collection="Test_Load_PathIE_1"):
            tuples.add((q.Predication.document_id, q.Predication.document_collection,
                        q.Predication.subject_id, q.Predication.subject_type, q.Predication.subject_str,
                        q.Predication.predicate, q.Predication.relation,
                        q.Predication.object_id, q.Predication.object_type, q.Predication.object_str,
                        q.Predication.extraction_type, q.Sentence.text))

        self.assertIn((23952588, 'Test_Load_PathIE_1',
                       'D010300', 'Disease', 'PD',
                       'study', None,
                       'D004409', 'Disease', 'dyskinesia', 'PathIE',
                       'We studied the prevalence and predictors of levodopa-induced dyskinesia among multiethnic Malaysian patients with PD.'),
                      tuples)
        self.assertNotIn((23952588, 'Test_Load_PathIE_1',
                          'D004409', 'Disease', 'dyskinesia',
                          'study', None,
                          'D010300', 'Disease', 'PD', 'PathIE',
                          'We studied the prevalence and predictors of levodopa-induced dyskinesia among multiethnic Malaysian patients with PD.'),
                         tuples)

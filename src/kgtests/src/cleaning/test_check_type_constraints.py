import unittest

from sqlalchemy import update

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Document, Sentence, Predication
from kgextractiontoolbox.cleaning.check_type_constraints import delete_predications_hurting_type_constraints
from kgextractiontoolbox.cleaning.relation_type_constraints import RelationTypeConstraintStore
from kgtests import util


class RelationTypeConstraintChecking(unittest.TestCase):

    def setUp(self) -> None:
        session = Session.get()
        documents = [dict(id=1, collection="Test_Type_Checking", title="ABC", abstract=""),
                     dict(id=2, collection="Test_Type_Checking", title="DEF", abstract="")]
        Document.bulk_insert_values_into_table(session, documents)

        sentences = [dict(id=1, document_collection="Test_Type_Checking", text="Hello", md5hash="1"),
                     dict(id=2, document_collection="Test_Type_Checking", text="World", md5hash="2")]
        Sentence.bulk_insert_values_into_table(session, sentences)

        predications = [dict(id=31,
                             document_id=1, document_collection="Test_Type_Checking",
                             subject_id="A", subject_type="Drug", subject_str="",
                             predicate="treats", relation="treats",
                             object_id="B", object_type="Disease", object_str="",
                             sentence_id=1, extraction_type="PathIE"),
                        dict(id=32,
                             document_id=1, document_collection="Test_Type_Checking",
                             subject_id="A", subject_type="Disease", subject_str="",
                             predicate="treats", relation="treats",
                             object_id="B", object_type="Disease", object_str="",
                             sentence_id=1, extraction_type="PathIE"),
                        dict(id=33,
                             document_id=2, document_collection="Test_Type_Checking",
                             subject_id="A", subject_type="Disease", subject_str="",
                             predicate="induces", relation="induces",
                             object_id="B", object_type="Disease", object_str="",
                             sentence_id=2, extraction_type="PathIE"),
                        dict(id=34,
                             document_id=2, document_collection="Test_Type_Checking",
                             subject_id="A", subject_type="Gene", subject_str="",
                             predicate="induces", relation="induces",
                             object_id="B", object_type="Gene", object_str="",
                             sentence_id=2, extraction_type="PathIE")
                        ]
        Predication.bulk_insert_values_into_table(session, predications)

    def setup_relations(self):
        session = Session.get()
        session.execute(update(Predication).where(Predication.id == 31).values(relation="treats"))
        session.execute(update(Predication).where(Predication.id == 32).values(relation="treats"))
        session.execute(update(Predication).where(Predication.id == 33).values(relation="induces"))
        session.execute(update(Predication).where(Predication.id == 34).values(relation="induces"))
        session.commit()

    def test_check_constraints(self):
        self.setup_relations()
        store = RelationTypeConstraintStore()
        store.load_from_json(util.get_test_resource_filepath('cleaning/pharm_relation_type_constraints.json'))

        delete_predications_hurting_type_constraints(store, "Test_Type_Checking")

        session = Session.get()
        self.assertIsNotNone(session.query(Predication).filter(Predication.id == 31).first())
        self.assertIsNone(session.query(Predication).filter(Predication.id == 32).first())
        self.assertIsNotNone(session.query(Predication).filter(Predication.id == 33).first())
        self.assertIsNone(session.query(Predication).filter(Predication.id == 34).first())

    def test_check_constraints_above_id(self):
        self.setup_relations()
        store = RelationTypeConstraintStore()
        store.load_from_json(util.get_test_resource_filepath('cleaning/pharm_relation_type_constraints.json'))

        delete_predications_hurting_type_constraints(store, "Test_Type_Checking", predicate_id_minimum=33)

        session = Session.get()
        self.assertIsNotNone(session.query(Predication).filter(Predication.id == 31).first())
        self.assertIsNotNone(session.query(Predication).filter(Predication.id == 32).first())
        self.assertIsNotNone(session.query(Predication).filter(Predication.id == 33).first())
        self.assertIsNone(session.query(Predication).filter(Predication.id == 34).first())

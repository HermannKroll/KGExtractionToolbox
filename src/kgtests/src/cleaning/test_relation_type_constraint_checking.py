import unittest

from kgextractiontoolbox.cleaning.relation_type_constraints import RelationTypeConstraintStore
from kgtests import util




class RelationTypeConstraintChecking(unittest.TestCase):

    def test_missing_object_constraints_1(self):
        store = RelationTypeConstraintStore()
        with self.assertRaises(ValueError):
            store.load_from_json(
                util.get_test_resource_filepath('cleaning/pharm_relation_type_constraints_broken1.json'))

    def test_missing_object_constraints_2(self):
        store = RelationTypeConstraintStore()
        with self.assertRaises(ValueError):
            store.load_from_json(
                util.get_test_resource_filepath('cleaning/pharm_relation_type_constraints_broken2.json'))

    def test_missing_subject_constraints_3(self):
        store = RelationTypeConstraintStore()
        with self.assertRaises(ValueError):
            store.load_from_json(
                util.get_test_resource_filepath('cleaning/pharm_relation_type_constraints_broken3.json'))

    def test_missing_subject_constraints_4(self):
        store = RelationTypeConstraintStore()
        with self.assertRaises(ValueError):
            store.load_from_json(
                util.get_test_resource_filepath('cleaning/pharm_relation_type_constraints_broken4.json'))

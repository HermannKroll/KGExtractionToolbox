import json

from typing import List


class RelationTypeConstraintStore:

    def __init__(self):
        self.constraints = {}

    def load_from_json(self, constraint_json_file: str):
        with open(constraint_json_file, 'rt') as f:
            self.constraints = json.load(f)

        self._verify_integrity()

    def get_subject_constraints(self, relation: str) -> List[str]:
        return self.constraints[relation]["subjects"]

    def get_object_constraints(self, relation: str) -> List[str]:
        return self.constraints[relation]["objects"]

    def _verify_integrity(self):
        for relation, constraint in self.constraints.items():
            if 'subjects' not in constraint or not constraint['subjects']:
                raise ValueError(f'subject constraints missing for: {relation}')
            if 'objects' not in constraint or not constraint['objects']:
                raise ValueError(f'object constraints missing for: {relation}')

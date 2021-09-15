from collections import defaultdict

import json


class RelationVocabulary:

    def __init__(self):
        self.relation_dict = defaultdict(set)

    def get_relation_synonyms(self, relation: str) -> [str]:
        return self.relation_dict[relation]

    def load_from_json(self, relation_vocab_file: str):
        self.relation_dict.clear()
        with open(relation_vocab_file, 'rt') as f:
            self.relation_dict = json.load(f)

        self._verify_integrity()

    def _verify_integrity(self):
        for relation, synonyms in self.relation_dict.items():
            if '*' in relation:
                raise ValueError(f'* are not allowed in a relation (found {relation})')
            for syn in synonyms:
                if '*' in syn[1:-1]:
                    raise ValueError('the * operator can only be used as a start or end character'
                                     f'(found * in {syn} for relation {relation}')

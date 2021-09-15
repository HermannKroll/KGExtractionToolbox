from collections import defaultdict

import csv
from pathlib import Path
from typing import Union


def expand_vocabulary_term(term: str) -> str:
    if term.endswith('y'):
        yield f'{term[:-1]}ies'
    if term.endswith('ies'):
        yield f'{term[:-3]}y'
    if term.endswith('s') or term.endswith('e'):
        yield term[:-1]
    if term.endswith('or') and len(term) > 2:
        yield term[:-2] + "our"
    if term.endswith('our') and len(term) > 3:
        yield term[:-3] + "or"
    if "-" in term:
        yield term.replace("-", " ")
        yield term.replace("-", "")
    if " " in term:
        yield term.replace(" ", "-")
        yield term.replace(" ", "")
    yield from [term, f'{term}e', f'{term}s']


class Vocabulary:
    def __init__(self, path: Union[str, Path]):
        self.path = path
        self.vocabularies = defaultdict(lambda: defaultdict(set))

    def load_vocab(self):
        if self.vocabularies:
            return
        with open(self.path, "r") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for line in reader:
                if not line["heading"] or not line["type"] or not line["id"]:
                    continue
                for syn in {s
                            for t in (line["synonyms"].split(";") if line["synonyms"] else []) + [line["heading"]]
                            for s in expand_vocabulary_term(t.lower()) if t}:
                    self.vocabularies[line["type"]][syn] |= {line["id"]}
            self.vocabularies = {k: dict(v) for k, v in self.vocabularies.items()}

    def get_ent_types(self):
        return self.vocabularies.keys()

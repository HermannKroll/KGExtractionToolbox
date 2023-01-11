import csv
import logging
from collections import defaultdict
from pathlib import Path
from typing import Union, List


class VocabularyEntry:

    def __init__(self, entity_id, entity_type, heading, synonyms):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.heading = heading
        self.synonyms = synonyms

    def to_dict(self):
        return dict(id=self.entity_id, type=self.entity_type, heading=self.heading, synonyms=self.synonyms)


class Vocabulary:
    def __init__(self, path: Union[str, Path]):
        self.path = path
        self.vocabularies = defaultdict(lambda: defaultdict(set))
        self.vocabulary_entries: List[VocabularyEntry] = list()
        self._entry_by_id_and_type = {}
        self.size = 0

    def add_vocabulary(self, vocabulary, expand_terms=True):
        for entry in vocabulary.vocabulary_entries:
            self.add_vocab_entry(entry.entity_id, entry.entity_type, entry.heading, entry.synonyms, expand_terms=expand_terms)

    def add_vocab_entry(self, entity_id: str, entity_type: str, heading: str, synonyms: str, expand_terms=True):
        self.size += 1
        entry = VocabularyEntry(entity_id, entity_type, heading, synonyms)
        self.vocabulary_entries.append(entry)

        key = (entity_id, entity_type)
        if key in self._entry_by_id_and_type:
            logging.warning(f"Ignoring duplicated entry ({key}) in vocabulary{self.path}")
        else:
            self._entry_by_id_and_type[key] = entry

        if expand_terms:
            for syn in {s
                        for t in (synonyms.split(";") if synonyms else []) + [heading]
                        for s in expand_vocabulary_term(t.lower()) if t}:
                self.vocabularies[entity_type][syn] |= {entity_id}
        else:
            for syn in {t.lower()
                        for t in (synonyms.split(";") if synonyms else []) + [heading]}:
                self.vocabularies[entity_type][syn] |= {entity_id}

    def compute_reverse_index(self):
        self.vocabularies = {k: dict(v) for k, v in self.vocabularies.items()}

    def load_vocab(self, expand_terms=True):
        if self.vocabularies:
            return
        with open(self.path, "r") as f:
            reader = csv.DictReader(f, delimiter="\t")
            type_heading = 'type' if 'type' in reader.fieldnames else 'enttype'
            for line in reader:

                if not line["heading"] or not line[type_heading] or not line["id"]:
                    continue

                self.add_vocab_entry(line["id"], line[type_heading], line["heading"], line["synonyms"],
                                     expand_terms=expand_terms)

        self.compute_reverse_index()

    def export_vocabulary_as_tsv(self, output_file: str):
        """
        Export the vocabulary as a TSV file
        :param output_file: Path to the file
        :return: None
        """
        self.vocabulary_entries.sort(key=lambda x: x.entity_id)
        with open(output_file, 'wt') as f:
            f = csv.DictWriter(f, ["id", "type", "heading", "synonyms"], delimiter="\t")
            f.writeheader()
            for e in sorted(self.vocabulary_entries, key=lambda x: x.entity_id):
                f.writerow(e.to_dict())

    def get_entity_heading(self, entity_id: str, entity_type: str) -> str:
        """
        Get an entity heading from the vocabulary
        :param entity_id: entity id
        :param entity_type: entity type
        :return: heading
        """
        return self._entry_by_id_and_type[(entity_id, entity_type)].heading

    def get_ent_types(self):
        return self.vocabularies.keys()

    def count_distinct_entities(self):
        return len(self._entry_by_id_and_type)

    def count_distinct_terms(self):
        terms = set()
        for _, v_terms in self.vocabularies.items():
            for t in v_terms:
                terms.add(t)
        return len(terms)


def expand_vocabulary_term(term: str, minimum_len_to_expand=3, depth=0) -> str:
    # only consider the length the last term
    if ' ' in term and len(term.split(' ')[-1]) < minimum_len_to_expand:
        yield term
    # test if term has the minimum len to be expanded
    elif len(term) < minimum_len_to_expand:
        yield term
    else:
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
            if depth == 0:
                yield from expand_vocabulary_term(term.replace("-", " "), depth=1)
            yield term.replace("-", "")
            if depth == 0:
                yield from expand_vocabulary_term(term.replace("-", ""), depth=1)
        if " " in term:
            yield term.replace(" ", "-")
            if depth == 0:
                yield from expand_vocabulary_term(term.replace(" ", "-"), depth=1)
            yield term.replace(" ", "")
            if depth == 0:
                yield from expand_vocabulary_term(term.replace(" ", ""), depth=1)
        yield from [term, f'{term}e', f'{term}s']

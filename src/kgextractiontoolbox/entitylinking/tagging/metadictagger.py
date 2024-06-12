from typing import List

import kgextractiontoolbox.entitylinking.tagging.dictagger as dt
from kgextractiontoolbox.document.document import TaggedEntity, TaggedDocument

"""
Modified version of the dict tagger, that can run on the vocabularies of multiple dicttaggers
"""


class MetaDicTagger(dt.DictTagger):
    __name__ = "MetaDicTagger"
    __version__ = "1.0"

    def __init__(self, vocabulary=None, *args, **kwargs):
        super().__init__(short_name="meTa", long_name="meta dict tagger", version=None, tag_types=None,
                         *args, **kwargs)

        self._sub_taggers: List[dt.DictTagger] = []
        self._vocabs = {}
        if vocabulary:
            vocabulary.load_vocab()
            self._vocabs = vocabulary.vocabularies
        self.tag_types = set()

    def add_tagger(self, tagger: dt.DictTagger):
        self._sub_taggers.append(tagger)
        self.tag_types = set(self.tag_types).union(tagger.get_types())

    def prepare(self, resume=False):
        for tagger in self._sub_taggers:
            tagger.prepare()
            self._vocabs[tagger.tag_types[0]] = tagger.desc_by_term

    def generate_tag_lines(self, end, doc_id, start, term):
        for entType, vocab in self._vocabs.items():
            hits = vocab.get(term)
            if hits:
                for desc in hits:
                    yield doc_id, start, end, term, entType, desc

    def generate_tagged_entities(self, end, doc_id, start, term, tmp_vocab=None):
        if tmp_vocab:
            tmp_hit = tmp_vocab.get(term)
            if tmp_hit:
                for entType, hit in tmp_hit:
                    yield TaggedEntity(None, doc_id, start, end, term, entType, hit)
        else:
            for entType, vocab in self._vocabs.items():
                hits = vocab.get(term)
                if hits:
                    for desc in hits:
                        yield TaggedEntity((doc_id, start, end, term, entType, desc))

    def tag_doc(self, in_doc: TaggedDocument, consider_sections=False) -> TaggedDocument:
        doc = super().tag_doc(in_doc, consider_sections=consider_sections)
        for tagger in self._sub_taggers:
            tagger.custom_tag_filter_logic(doc)
        return doc

    def get_types(self):
        return self.tag_types

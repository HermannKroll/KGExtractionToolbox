import itertools as it
import re
from abc import ABCMeta
from collections import defaultdict
from typing import List

from kgextractiontoolbox.config import DICT_TAGGER_BLACKLIST
from kgextractiontoolbox.document.document import TaggedDocument, TaggedEntity
from kgextractiontoolbox.entitylinking.tagging.base import BaseTagger


def get_n_tuples(in_list, n):
    if n == 0:
        return []
    for i, element in enumerate(in_list):
        if i + n <= len(in_list):
            yield in_list[i:i + n]
        else:
            break


def clean_vocab_word_by_split_rules(word: str) -> str:
    if word and re.match(r"[^\w]", word[0]):
        word = word[1:]
    if word and re.match(r"[^\w]", word[-1]):
        word = word[:-1]
    return word


def split_indexed_words(content):
    words = content.split(' ')
    ind_words = []
    next_index_word = 0
    for word in words:
        ind = next_index_word
        word_offset = 0
        while word and re.match(r"[^\w]", word[0]):
            word = word[1:]
            ind += 1
            word_offset += 1
        while word and re.match(r"[^\w]", word[-1]):
            word = word[:-1]
            word_offset += 1
        ind_words.append((word, ind))

        # index = last index + length of last word incl. offset
        next_index_word = next_index_word + len(word) + word_offset + 1

    # For cases like "water-induced" add "water"
    amendment = []
    for word, index in ind_words:
        split = word.split("-")
        if len(split) == 2 and split[1][-2:] in {"ed", "et"}:
            amendment.append((split[0], index))
    ind_words += amendment
    return ind_words


class DictTagger(BaseTagger, metaclass=ABCMeta):
    PROGRESS_BATCH = 10000
    __name__ = None
    __version__ = None

    def __init__(self, short_name, long_name, version, tag_types, logger,
                 config, collection):
        super().__init__(config=config, collection=collection, logger=logger)
        self.tag_types = [tag_types, ]
        self.short_name, self.long_name, self.version = short_name, long_name, version
        self.desc_by_term = {}

    def get_types(self):
        return self.tag_types

    @staticmethod
    def get_blacklist_set():
        with open(DICT_TAGGER_BLACKLIST) as f:
            blacklist = f.read().splitlines()
        blacklist_set = set()
        for s in blacklist:
            s_lower = s.lower().strip()
            blacklist_set.add(s_lower)
            blacklist_set.add('{}s'.format(s_lower))
            blacklist_set.add('{}e'.format(s_lower))
            if s_lower.endswith('s') or s_lower.endswith('e'):
                blacklist_set.add(s_lower[0:-1])
        return blacklist_set

    def tag_doc(self, in_doc: TaggedDocument) -> TaggedDocument:
        """
        Generate tags for a TaggedDocument
        :param in_doc: document containing title+abstract to tag. Is modified by adding tags
        :return: the modified in_doc
        """
        and_check_range = 5
        connector_words = {"and", "or"}
        abb_vocab = dict()
        out_doc = in_doc
        pmid, title, abstact = in_doc.id, in_doc.title, in_doc.abstract
        content = title.strip() + " " + abstact.strip()
        content = content.lower()

        # split into indexed single words
        ind_words = split_indexed_words(content)

        tags = []
        for spaces in range(self.config.dict_max_words):
            for word_tuple in get_n_tuples(ind_words, spaces + 1):
                hits = self.get_hits(word_tuple, pmid)
                tags += hits

                if self.config.custom_abbreviations and hits:
                    words, indexes = zip(*word_tuple)
                    # only learn abbreviations from full entity mentions
                    term = " ".join(words)
                    if len(term) >= self.config.dict_min_full_tag_len:
                        match = re.match(r" \(([^\(\)]*)\).*", content[indexes[-1] + len(words[-1]):])
                        if match:
                            # strip the abbreviation
                            abbreviation = match.groups()[0].strip()
                            abb_vocab[abbreviation] = [(t.ent_type, t.ent_id) for t in hits]

        if abb_vocab:
            for spaces in range(self.config.dict_max_words):
                for word_tuple in get_n_tuples(ind_words, spaces + 1):
                    tags += self.get_hits(word_tuple, pmid, abb_vocab)

        if self.config.dict_check_abbreviation:
            tags = DictTagger.clean_abbreviation_tags(tags, self.config.dict_min_full_tag_len)

        out_doc.tags += tags
        return out_doc

    def get_hits(self, word_tuple, pmid, abb_vocab=None):
        words, indexes = zip(*word_tuple)
        term = " ".join(words)
        if not term:
            return []
        start = indexes[0]
        end = indexes[-1] + len(words[-1])
        hits = list(self.generate_tagged_entities(end, pmid, start, term, tmp_vocab=abb_vocab))
        return hits

    connector_words = {"and", "or"}

    @staticmethod
    def conjunction_product(token_seq, seperated=False):
        """
        split token_seq at last conn_word, return product of all sub token sequences. Exclude connector words.
        :param seperated: return left_tuples, right_tuples instead of left_tuples+right_tuples
        """
        cwords_indexes = [n for n, (w, i) in enumerate(token_seq) if w in DictTagger.connector_words]

        if not cwords_indexes:  # or max(cwords_indexes) in [0, len(token_seq)-1]:
            return []
        left = token_seq[:max(cwords_indexes)]
        right = token_seq[max(cwords_indexes):]

        left = [(w, i) for w, i in left if w not in DictTagger.connector_words]
        right = [(w, i) for w, i in right if w not in DictTagger.connector_words]

        left_tuples = [[]] + [t for n in range(0, len(left) + 1) for t in list(get_n_tuples(left, n))]
        right_tuples = [[]] + [t for n in range(0, len(right) + 1) for t in list(get_n_tuples(right, n))]
        yield from [(lt, rt) for lt, rt in it.product(left_tuples, right_tuples) if lt + rt]

    def _tag(self, in_file, out_file):
        with open(in_file) as f:
            document = f.read()
        result = self.tag_doc(TaggedDocument(document))
        with open(out_file, "w+") as f:
            f.write(str(result))

    def generate_tag_lines(self, end, pmid, start, term):
        hits = self._get_term(term)
        # print(f"Found {hits} for '{term}'")
        if hits:
            for desc in hits:
                yield pmid, start, end, term, self.tag_types[0], desc

    def generate_tagged_entities(self, end, pmid, start, term, tmp_vocab=None):
        hits = set()
        if tmp_vocab:
            tmp_hit = tmp_vocab.get(term)
            if tmp_hit:
                hits |= {hit[1] for hit in tmp_hit}
        else:
            hits |= set(self._get_term(term))

        # print(f"Found {hits} for '{term}'")
        if hits:
            for desc in hits:
                yield TaggedEntity((pmid, start, end, term, self.tag_types[0], desc))

    def _get_term(self, term):
        hits = self.desc_by_term.get(term)
        return hits if hits else set()

    @staticmethod
    def clean_abbreviation_tags(tags: List[TaggedEntity], minimum_tag_len=5):
        """
        This method removes all tags which are assumed to be an abbreviation and which do not have a long expression
        within the document
        e.g. Aspirin (ASA) -> ASA is allowed in the document because Aspirin is associated with the same descriptor
        without aspirin ASA will further not be kept as a valid tag
        :param minimum_tag_len: the minimum tag length to treat a term as a 'full' tag
        :param tags: a list of tags
        :return: a list of cleaned tags
        """
        tags_cleaned = []
        desc2tags = defaultdict(list)
        for t in tags:
            desc2tags[t.ent_id].append(t)

        # search if a full tag is found for a descriptor
        for desc, tags in desc2tags.items():
            keep_desc = False
            for t in tags:
                if len(t.text) >= minimum_tag_len:
                    keep_desc = True
                    break
            if keep_desc:
                tags_cleaned.extend(tags)
        return tags_cleaned

    def prepare(self):
        blacklist_set = DictTagger.get_blacklist_set()
        self.desc_by_term = {k.lower().strip(): v for k, v in self.desc_by_term.items() if
                             k.lower().strip() not in blacklist_set}

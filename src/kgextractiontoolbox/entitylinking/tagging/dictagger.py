import os.path
import re
from abc import ABCMeta
from collections import defaultdict
from typing import List, Set

from kgextractiontoolbox.config import DICT_TAGGER_BLACKLIST
from kgextractiontoolbox.document.document import TaggedDocument, TaggedEntity
from kgextractiontoolbox.entitylinking.tagging.base import BaseTagger


def get_n_tuples(in_list: List[str], n: int):
    """
    This method takes a list of strings and returns a list of subsequent tuples.
    We need that for generating candidates that are used for a lookup against our tagging vocabulary
    :param in_list: a list of strings
    :param n: n-subsequent tokens are used for the output list
    :return: a generator of n-subsequent tuples as lists
    """
    if n == 0:
        return []
    for i, element in enumerate(in_list):
        if i + n <= len(in_list):
            yield in_list[i:i + n]
        else:
            break


def clean_vocab_word_by_split_rules(word: str) -> str:
    """
    This method takes a word and returns a cleaned version of the word.
    First character or last character are removed if they are no non-numerical non-alphabetic characters.
    :param word: word
    :return: a cleaned version of the word
    """
    if word and re.match(r"[^\w]", word[0]):
        word = word[1:]
    if word and re.match(r"[^\w]", word[-1]):
        word = word[:-1]
    return word


def split_indexed_words(content: str, split_by_slash: bool=True):
    """
    This method works like a tokenization. However, we need to control the tokenization procedure
    to generate the correct token positions of the tagged entities in the end
    :param content: textual content
    :param split_by_slash: Control whether a token is also split by a slash
    :return: a list of tokens
    """
    words = content.split(' ')
    ind_words = []
    next_index_word = 0
    for word in words:
        if split_by_slash and "/" in word:
            ind_words.extend(split_indexed_words(word.replace("/", " ")))
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
    """
    Base logic for our dictionary-based entity linking. This class
    requires an entity vocabulary. Basically, the text is split into tokens.
    This list is then joined by subsequent tokens. The joined words are used
    to lookup whether they form an entity in our vocabulary.

    This entity linking method ignores "-" by replacing the character in
    the document text and in the vocabulary by a space.
    """
    PROGRESS_BATCH = 10000
    __name__ = None
    __version__ = None

    def __init__(self, short_name, long_name, version, tag_types, logger,
                 config, collection, blacklist_file=DICT_TAGGER_BLACKLIST):
        super().__init__(config=config, collection=collection, logger=logger)
        self.tag_types = [tag_types, ]
        self.short_name, self.long_name, self.version = short_name, long_name, version
        self.desc_by_term = {}
        self.blacklist_file = blacklist_file
        self.clean_abbreviation_tags_function = DictTagger.clean_abbreviation_tags
        self.dict_max_words = None

    def get_types(self) -> List[str]:
        """
        Returns which entity types are tagged
        :return: a list of tag types
        """
        return self.tag_types

    def get_blacklist_set(self) -> Set[str]:
        """
        Loads a list of blacklisted words that are ignored when tagging
        We provide a list of words like stopwords in our toolbox
        :return: a set of ignored words
        """
        if os.path.isfile(self.blacklist_file):
            with open(self.blacklist_file) as f:
                blacklist = f.read().splitlines()
            blacklist_set = set()
            for s in blacklist:
                s_lower = self.normalize_term(s)
                blacklist_set.add(s_lower)
                blacklist_set.add('{}s'.format(s_lower))
                blacklist_set.add('{}e'.format(s_lower))
                if s_lower.endswith('s') or s_lower.endswith('e'):
                    blacklist_set.add(s_lower[0:-1])
            return blacklist_set
        else:
            self.logger.info(f'No file of ignored words was fount at: {self.blacklist_file}')
            return set()

    def tag_doc(self, in_doc: TaggedDocument, consider_sections=False) -> TaggedDocument:
        """
        Implements the tagging logic
        :param in_doc: document containing title+abstract to tag. Is modified by adding tags
        :param consider_sections: should fulltexts be considered?
        :return: the modified in_doc
        """
        # the logic requires to know how many subsequent tokens could form a match
        # that is why we take the longest word in our vocabulary (defined by number of spaces)
        if self.dict_max_words is None:
            self.dict_max_words = max((len(norm.split()) for norm in self.desc_by_term), default=0)
            self.logger.info(f'dict_max_words set to {self.dict_max_words}')
        abb_vocab = dict()
        out_doc = in_doc
        docid = in_doc.id
        tags = []
        # loops over all text elements of a document (title, abstract, sections)
        for text_element, offset in in_doc.iterate_over_text_elements(sections=consider_sections):
            # normalizes the text
            content = self.normalize_term(text_element)
            # split into indexed single words
            ind_words = split_indexed_words(content, split_by_slash=self.config.dict_split_by_slash)

            # this loop generates all combinations of words that could form a candidate for a lookup
            for spaces in range(self.dict_max_words):
                # generate the words that are used for lookups
                for word_tuple in get_n_tuples(ind_words, spaces + 1):
                    # perform the lookup and generate the tagged entities
                    hits = self.get_hits(word_tuple, docid, offset=offset)
                    tags += hits

                    # if we allow to learn custom abbreviations
                    # we can only learn one for the rest of the document if at least a single entity has been taggeed
                    if self.config.custom_abbreviations and hits:
                        words, indexes = zip(*word_tuple)
                        # only learn abbreviations from full entity mentions
                        term = " ".join(words)
                        if len(term) >= self.config.dict_min_full_tag_len:
                            # Checks whether a user defines a custom abbreviations like Aspirin (ASA)
                            match = re.match(r" \(([^\(\)]*)\).*", content[indexes[-1] + len(words[-1]):])
                            if match:
                                # strip the abbreviation
                                abbreviation = match.groups()[0].strip()
                                # learn the abbreviation for this document
                                abb_vocab[abbreviation] = [(t.ent_type, t.ent_id) for t in hits]

        # if we learned some abbreviation, we have to tagg the document again
        # this time by using our abbreviation vocabulary
        if len(abb_vocab) > 0:
            for text_element, offset in in_doc.iterate_over_text_elements(sections=consider_sections):
                content = text_element.lower()
                # split into indexed single words
                ind_words = split_indexed_words(content, split_by_slash=self.config.dict_split_by_slash)
                for spaces in range(self.dict_max_words):
                    for word_tuple in get_n_tuples(ind_words, spaces + 1):
                        tags += self.get_hits(word_tuple, docid, abb_vocab=abb_vocab, offset=offset)

        # check if we need some cleaning here, e.g. take longest subsequences
        if self.config.dict_check_abbreviation:
            tags = self.clean_abbreviation_tags_function(tags, self.config.dict_min_full_tag_len)

        # finally we determined all tags within this document
        out_doc.tags += tags
        # Apply custom logic if applicable
        self.custom_tag_filter_logic(out_doc)

        # select original text without any normalization and lower casing
        doc_text = out_doc.get_text_content(sections=consider_sections)
        for t in out_doc.tags:
            t.text = doc_text[t.start:t.end]

        # return the output document
        return out_doc

    def get_hits(self, word_tuple, docid, abb_vocab=None, offset=0):
        """
        Generates the tagged entities
        :param word_tuple: tuple of subsequent strings
        :param docid: the current document id
        :param abb_vocab: abbreviation vocabulary (can be none)
        :param offset: the current offset position within the text
        :return:
        """
        words, indexes = zip(*word_tuple)
        term = " ".join(words)
        if not term:
            return []
        start = indexes[0] + offset
        end = indexes[-1] + len(words[-1]) + offset
        hits = list(self.generate_tagged_entities(end, docid, start, term, tmp_vocab=abb_vocab))
        return hits

    connector_words = {"and", "or"}

    def _tag(self, in_file, out_file):
        with open(in_file) as f:
            document = f.read()
        result = self.tag_doc(TaggedDocument(document))
        with open(out_file, "w+") as f:
            f.write(str(result))

    def generate_tagged_entities(self, end, docid, start, term, tmp_vocab=None):
        """
        Generate the tagged entities
        :param end: end position
        :param docid: documennt id
        :param start: start position
        :param term: term to check
        :param tmp_vocab: abbreviation vocabulary (can be none)
        :return:
        """
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
                yield TaggedEntity((docid, start, end, term, self.tag_types[0], desc))

    def _get_term(self, term: str) -> [str]:
        """
        Returns matches of the term in our vocabulary
        :param term: some string
        :return: a list of matches
        """
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

    @staticmethod
    def normalize_term(term):
        """
        Normalizes a text by replacing all "-" characters by spaces
        :param term:
        :return:
        """
        return term.lower().replace('-', ' ')

    def prepare(self):
        """
        Prepares tagger (load backlisted terms plus prepares internal dictionary)
        :return: None
        """
        blacklist = self.get_blacklist_set()
        self.desc_by_term = {norm: v for k, v in self.desc_by_term.items()
                             if (norm := self.normalize_term(k)) not in blacklist}

    def custom_tag_filter_logic(self, in_doc: TaggedDocument):
        """
        Allows to implement some custom tag filter logic
        :param in_doc: the current input document
        :return:
        """
        pass

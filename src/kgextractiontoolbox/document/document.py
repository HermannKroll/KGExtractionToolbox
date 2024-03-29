import json
import logging
import re
from collections import defaultdict
from enum import Enum, auto
from typing import List

from kgextractiontoolbox import tools
from kgextractiontoolbox.backend.models import Tag, Document
from kgextractiontoolbox.document.regex import TAG_LINE_NORMAL, CONTENT_ID_TIT_ABS


class DocFormat(Enum):
    JSON_LINE = auto()
    COMPOSITE_JSON = auto()
    SINGLE_JSON = auto()
    PUBTATOR = auto()


def get_doc_format(filehandle=None, path=None) -> DocFormat:
    if not filehandle or not path:
        raise ValueError("Filehandle or path must be filled to get the document format")
    if filehandle:
        first_char = filehandle.read(1)
        filehandle.seek(0)
    elif path:
        with open(path) as f:
            first_char = f.read(1)

    path_suffix = path.split('.')[-1].lower()
    if path_suffix == 'jsonl':
        return DocFormat.JSON_LINE
    if first_char == "[":
        return DocFormat.COMPOSITE_JSON
    elif first_char == "{":
        return DocFormat.SINGLE_JSON
    elif re.match(r"\d", first_char):
        return DocFormat.PUBTATOR
    else:
        return None


def is_doc_file(fn):
    return not fn.startswith(".") and any([fn.endswith(ext) for ext in [".txt", ".document", ".pubtator", "json",
                                                                        ".jsonl"]])


class TaggedEntity:

    def __init__(self, tag_tuple=None, document=None, start: int = None, end: int = None, text=None, ent_type=None,
                 ent_id=None):
        self.document = int(tag_tuple[0]) if tag_tuple else document
        self.start = int(tag_tuple[1]) if tag_tuple else int(start)
        self.end = int(tag_tuple[2]) if tag_tuple else int(end)
        self.text = tag_tuple[3] if tag_tuple else text
        self.ent_type = tag_tuple[4] if tag_tuple else ent_type
        self.ent_id = tag_tuple[5] if tag_tuple else ent_id

    def __str__(self):
        return Tag.create_pubtator(self.document, self.start, self.end, self.text, self.ent_type, self.ent_id)

    def __repr__(self):
        return "<Entity {},{},{},{},{}>".format(self.start, self.end, self.text, self.ent_type, self.ent_id)

    def __eq__(self, other):
        return self.document == other.document and self.start == other.start and self.end == other.end \
               and self.text == other.text and self.ent_type == other.ent_type and self.ent_id == other.ent_id

    def __hash__(self):
        return hash((self.start, self.end, self.text, self.ent_id))

    def is_valid(self):
        if not self.ent_id or not self.ent_type or not self.text or self.start is None or self.end is None:
            return False
        return True


def parse_tag_list(path_or_str):
    content = tools.read_if_path(path_or_str)
    reg_result = TAG_LINE_NORMAL.findall(content)
    return [TaggedEntity(t) for t in reg_result] if reg_result else []


class Sentence:
    def __init__(self, sid, text, start, end) -> None:
        super().__init__()
        self.start = start
        self.text = text
        self.sid = sid
        self.end = end

    def __str__(self):
        return f'<Sentence {self.sid}, {self.start}, {self.end}, {self.text}>'

    def __repr__(self):
        return str(self)


class DocumentSection:
    def __init__(self, position: int, title: str, text: str):
        self.position = position
        self.title = title
        self.text = text

    def to_dict(self):
        return {"position": self.position, "title": self.title, "text": self.text}

    def __str__(self):
        return f'<DocumentSection {self.position}, {self.title}, {self.text}>'

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.position == other.position and self.title == other.title and self.text == other.text


class TaggedDocument:

    def __init__(self, from_str=None, spacy_nlp=None, ignore_tags=False, id=None, title=None, abstract=None,
                 sections=False):
        """
        initialize a document document
        :param from_str: content of a document file or a document filename
        """
        self.title = None
        self.abstract = None
        self.id = None
        self.tags = []
        self.classification = {}
        self.sections: List[DocumentSection] = []

        if from_str:
            from_str = tools.read_if_path(from_str)
            str_format = "pt" if re.match(r"\d", from_str[0]) else "json"
            if str_format == "pt":
                self.load_from_pubtator(pubtator_content=from_str, ignore_tags=ignore_tags)
            elif str_format == "json":
                self.load_from_json(json_str=from_str, ignore_tags=ignore_tags)

        else:
            self.id = id
            self.title = title
            self.abstract = abstract

        if self.tags:
            # if multiple document tags are contained in a single doc - raise error
            if len(set([t.document for t in self.tags])) > 1:
                raise ValueError(f'Document contains tags for multiple document ids: {self.id}')

            if TaggedDocument.pubtator_has_composite_tags(self.tags):
                self.tags = TaggedDocument.pubtator_split_composite_tags(self.tags)

            self.remove_duplicates_and_sort_tags()

        self.entity_names = {t.text.lower() for t in self.tags}
        if spacy_nlp:
            self._compute_nlp_indexes(spacy_nlp, sections=sections)

    def load_from_pubtator(self, pubtator_content: str, ignore_tags=False):
        """
        Loads a TaggedDocument from a PubTator str
        :param pubtator_content: the pubtator content
        :param ignore_tags: should tags be ignored?
        :return: None
        """
        match = CONTENT_ID_TIT_ABS.match(pubtator_content)
        if match:
            self.id, self.title, self.abstract = match.group(1, 2, 3)
            self.title = self.title.strip()
            self.abstract = self.abstract.strip()
            self.id = int(self.id)
        else:
            self.id, self.title, self.abstract = None, None, None

        if pubtator_content and not ignore_tags:
            self.tags = [TaggedEntity(t) for t in TAG_LINE_NORMAL.findall(pubtator_content)]
            if not self.id and self.tags:
                self.id = self.tags[0].document

    def load_from_json(self, json_str: str, ignore_tags=False):
        """
        Loads a TaggedDocument from a JSON str
        :param json_str: the json str (not parsed)
        :param ignore_tags: should tags be ignored?
        :return: None
        """
        doc_dict = json.loads(json_str)
        self.id, self.title, self.abstract = doc_dict["id"], doc_dict.get("title"), doc_dict.get("abstract")
        if "tags" in doc_dict and not ignore_tags:
            self.tags = [
                TaggedEntity(document=self.id,
                             start=tag["start"],
                             end=tag["end"],
                             text=tag["mention"],
                             ent_type=tag["type"],
                             ent_id=tag["id"])
                for tag in doc_dict["tags"]
            ]
        if "classification" in doc_dict:
            self.classification = doc_dict["classification"]

        if "sections" in doc_dict:
            self.sections = [DocumentSection(position=sec["position"],
                                             title=sec["title"],
                                             text=sec["text"])
                             for sec in doc_dict["sections"]]

    @staticmethod
    def pubtator_has_composite_tags(tags: [TaggedEntity]) -> bool:
        """
        There are composite entity mentions like
        24729111	19	33	myxoedema coma	Disease	D007037|D003128	myxoedema|coma
        does an entity id contain a composite delimiter |
        :param tags:
        :return:
        """
        return '|' in str([''.join([t.ent_id for t in tags])])

    @staticmethod
    def pubtator_split_composite_tags(tags: [TaggedEntity]) -> [TaggedEntity]:
        """
        There are composite entity mentions like
        24729111	19	33	myxoedema coma	Disease	D007037|D003128	myxoedema|coma
        This method will split them to multiple tags (replaces self.tags)
        :param: a list of tags
        :return: a list of split tags
        """
        cleaned_composite_tags = []
        for t in tags:
            ent_id = t.ent_id
            # composite tag detected
            ent_str_split = []
            if '\t' in ent_id:
                # more explanations are given - split them (we ignore the rest)
                ent_id, ent_str_split = t.ent_id.split('\t')
                ent_str_split = ent_str_split.split('|')
            if '|' in ent_id:
                ent_ids = ent_id.split('|')
                # if we do not have a concrete explanation (then duplicate the original string)
                if len(ent_ids) != len(ent_str_split):
                    ent_str_split = [t.text for i in range(0, len(ent_ids))]
                for e_id, e_str in zip(ent_ids, ent_str_split):
                    # find the new start and end
                    e_start = t.start + t.text.find(e_str)
                    e_stop = e_start + len(e_str)
                    # create multiple tags for a composite tag
                    cleaned_composite_tags.append(TaggedEntity(document=t.document, start=e_start, end=e_stop,
                                                               text=e_str, ent_type=t.ent_type, ent_id=e_id))
            else:
                # just add the tag (it's a normal tag)
                cleaned_composite_tags.append(t)
        return cleaned_composite_tags

    def clean_tags(self):
        # Set ensures duplicate elimination
        self.remove_duplicates_and_sort_tags()
        clean_tags = set(self.tags)
        for tag1 in self.tags:
            if not tag1.is_valid():
                clean_tags.remove(tag1)
            else:
                for tag2 in self.tags:
                    if tag2.start <= tag1.start and tag2.end >= tag1.end and tag1.text.lower() != tag2.text.lower():
                        clean_tags.remove(tag1)
                        break
        self.tags = list(clean_tags)
        self.sort_tags()

    def remove_duplicates_and_sort_tags(self):
        """
        Removes duplicated tags and sort tags
        :return:
        """
        self.tags = list(set(self.tags))
        self.sort_tags()

    def sort_tags(self):
        """
        Sort tags by their text location
        :return:
        """
        try:
            self.tags = sorted(self.tags, key=lambda t: (t.start, t.end, t.ent_id))
        except TypeError:
            # No ent id given
            self.tags = sorted(self.tags, key=lambda t: (t.start, t.end))

    def check_and_repair_tag_integrity(self):
        """
        Checks and repairs tags in documents. If an entity is not correctly aligned to the content, the entity
        is searched left (-30) and right (5) from the location. If the entity could be found, then its position
        is upated. Otherwise nothing happens
        :return:
        """
        text_content = self.get_text_content().lower()
        for t in self.tags:
            tag_text = t.text.lower()
            text_text = text_content[t.start:t.end]
            if tag_text != text_text:
                repaired = False
                # run backwards trough the document
                for off in range(5, -30, -1):
                    if tag_text == text_content[t.start + off:t.end + off]:
                        t.start = t.start - off
                        t.end = t.end - off
                        repaired = True
                if not repaired:
                    logging.debug(f'Tag position does not match to string in text ({tag_text} vs {text_text})')

    def _compute_nlp_indexes(self, spacy_nlp, sections=False):
        self.sentence_by_id = {}  # Use to build entity->sentence index
        self.entities_by_ent_id = defaultdict(list)  # Use entity->TaggedEntity index to build Mesh->Sentence index
        self.sentences_by_ent_id = defaultdict(set)  # entity->Sentence index
        self.entities_by_sentence = defaultdict(set)  # sent->entities

        if not self.has_content():
            return
           # raise ValueError(f'Cannot process document ({self.id}) without title or abstract')
            # Indexes


        sentence_idx = 0
        # iterate over all text elements (title, abstract, sec1 title, sec1 text, sec2 title, ...)
        for text_element, offset in self.iterate_over_text_elements(sections=sections):
            doc_nlp = spacy_nlp(text_element)

            # iterate over sentences in each element
            for sent in doc_nlp.sents:
                sent_str = str(sent)
                start_pos = sent.start_char + offset
                end_pos = sent.end_char + offset

                self.sentence_by_id[sentence_idx] = Sentence(
                    sentence_idx,
                    sent_str,
                    start_pos,
                    end_pos
                )
                sentence_idx += 1

        for tag in self.tags:
            self.entities_by_ent_id[tag.ent_id].append(tag)

        for ent_id, entities in self.entities_by_ent_id.items():
            for entity in entities:
                for sid, sent in self.sentence_by_id.items():
                    if sent.start <= entity.start <= sent.end:
                        self.sentences_by_ent_id[ent_id].add(sid)
                        self.entities_by_sentence[sid].add(entity)

    def iterate_over_text_elements(self, sections=False):
        """
        Iterate over all text elements in a document
        :param sections: should sections be considered?
        :return: an iterator over (string, int)
        """
        running_offset = 0
        if self.title:
            yield self.title, 0
            running_offset += len(self.title) + 1
        if self.abstract:
            yield self.abstract, running_offset
            running_offset += len(self.abstract) + 1

        if sections and self.sections:
            for sec in self.sections:
                yield sec.title, running_offset
                running_offset += len(sec.title) + 1
                yield sec.text, running_offset
                running_offset += len(sec.text) + 1

    def to_dict(self, export_content=True, export_tags=True, export_sections=True, export_classification=True):
        """
        converts the TaggedDocument to a dictionary that is consistent with our json ouptut format.
        Gosh, it's beautiful to formulate a json construction in python
        :return:
        """
        out_dict = {
            "id": self.id
        }
        if export_content:
            out_dict.update({
                "title": self.title,
                "abstract": self.abstract
            })
        if export_classification:
            out_dict["classification"] = self.classification
        if export_tags:
            out_dict.update({
                "tags": [
                    {
                        "id": tag.ent_id,
                        "mention": tag.text,
                        "start": tag.start,
                        "end": tag.end,
                        "type": tag.ent_type,
                    }
                    for tag in self.tags
                ],
            })
        if export_sections and self.sections:
            out_dict["sections"] = [sec.to_dict() for sec in self.sections]

        return out_dict

    def has_content(self):
        return True if (self.title or self.abstract) else False

    def get_section_full_texts(self):
        if self.sections:
            return ' '.join([str(sec.title) + ' ' + str(sec.text) for sec in self.sections])
        else:
            return None

    def get_text_content(self, sections=False):
        if sections and self.sections:
            return f"{self.title} {self.abstract} " + self.get_section_full_texts()
        else:
            return f"{self.title} {self.abstract}"

    def __eq__(self, other):
        if not isinstance(other, TaggedDocument):
            return False
        return self.to_dict() == other.to_dict()

    def __str__(self):
        return Document.create_pubtator(self.id, self.title, self.abstract, self.get_section_full_texts()) + "".join(
            [str(t) for t in self.tags]) + "\n"

    def __repr__(self):
        return "<Document {} {}>".format(self.id, self.title)

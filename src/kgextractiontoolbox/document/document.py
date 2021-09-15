from collections import defaultdict
from enum import Enum, auto

import json
import re

from kgextractiontoolbox import tools
from kgextractiontoolbox.backend.models import Tag, Document
from kgextractiontoolbox.document.regex import TAG_LINE_NORMAL, CONTENT_ID_TIT_ABS


class DocFormat(Enum):
    COMPOSITE_JSON = auto()
    SINGLE_JSON = auto()
    PUBTATOR = auto()


def get_doc_format(filehandle=None, path=None) -> DocFormat:
    if not (bool(filehandle) ^ bool(path)):
        raise ValueError("Either filehandle or path must be filled")
    if filehandle:
        first_char = filehandle.read(1)
        filehandle.seek(0)
    elif path:
        with open(path) as f:
            first_char = f.read(1)
    if first_char == "[":
        return DocFormat.COMPOSITE_JSON
    elif first_char == "{":
        return DocFormat.SINGLE_JSON
    elif re.match(r"\d", first_char):
        return DocFormat.PUBTATOR
    else:
        return None


def is_doc_file(fn):
    return not fn.startswith(".") and any([fn.endswith(ext) for ext in [".txt", ".document", "json"]])


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


class Sentence:
    def __init__(self, sid, text, start, end) -> None:
        super().__init__()
        self.start = start
        self.text = text
        self.sid = sid
        self.end = end

    def __str__(self):
        return f'<Sentence {self.sid}, {self.start}, {self.end}, {self.text}'

    def __repr__(self):
        return str(self)


def parse_tag_list(path_or_str):
    content = tools.read_if_path(path_or_str)
    reg_result = TAG_LINE_NORMAL.findall(content)
    return [TaggedEntity(t) for t in reg_result] if reg_result else []


class TaggedDocument:

    def __init__(self, from_str=None, spacy_nlp=None, ignore_tags=False, id=None, title=None, abstract=None):
        """
        initialize a document document
        :param from_str: content of a document file or a document filename
        """
        self.title = None
        self.abstract = None
        self.id = None
        self.tags = []
        self.classification = {}

        if from_str:
            from_str = tools.read_if_path(from_str)
            str_format = "pt" if re.match(r"\d", from_str[0]) else "json"

            if str_format == "pt":
                match = CONTENT_ID_TIT_ABS.match(from_str)
                if match:
                    self.id, self.title, self.abstract = match.group(1, 2, 3)
                    self.title = self.title.strip()
                    self.abstract = self.abstract.strip()
                    self.id = int(self.id)
                else:
                    self.id, self.title, self.abstract = None, None, None

                if from_str and not ignore_tags:
                    self.tags = [TaggedEntity(t) for t in TAG_LINE_NORMAL.findall(from_str)]
                    if not self.id and self.tags:
                        self.id = self.tags[0].document

            elif str_format == "json":
                doc_dict = json.loads(from_str)
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
                    self.classification = {k: v for k, v in
                                           zip(doc_dict["classification"], [""] * len(doc_dict["classification"]))}

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

        self.entity_names = {t.text.lower() for t in self.tags}
        if spacy_nlp:
            if not self.title and not self.abstract:
                raise ValueError(f'Cannot process document ({self.id}) without title or abstract')
            # Indexes
            # self.mesh_by_entity_name = {}  # Use to select mesh descriptor by given entity
            self.sentence_by_id = {}  # Use to build mesh->sentence index
            self.entities_by_ent_id = defaultdict(list)  # Use Mesh->TaggedEntity index to build Mesh->Sentence index
            self.sentences_by_ent_id = defaultdict(set)  # Mesh->Sentence index
            self.entities_by_sentence = defaultdict(set)  # Use for _query processing
            self._create_index(spacy_nlp)

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
        clean_tags = self.tags.copy()
        for tag1 in self.tags:
            if not tag1.document or not tag1.start or not tag1.end or not tag1.text or not tag1.ent_type or not tag1.ent_id:
                clean_tags.remove(tag1)
            else:
                for tag2 in self.tags:
                    if tag2.start <= tag1.start and tag2.end >= tag1.end and tag1.text.lower() != tag2.text.lower():
                        clean_tags.remove(tag1)
                        break
        self.tags = sorted(clean_tags, key=lambda t: (t.start, t.end, t.ent_id))

    def _create_index(self, spacy_nlp):
        # self.mesh_by_entity_name = {t.text.lower(): t.mesh for t in self.tags if
        #                            t.text.lower() not in self.mesh_by_entity_name}
        if self.title:
            if self.title[-1] == '.':
                content = f'{self.title} {self.abstract}'
                offset = 1
            else:
                content = f'{self.title}. {self.abstract}'
                offset = 2
        else:
            content = f'{self.abstract}'
            offset = 0

        doc_nlp = spacy_nlp(content)
        for idx, sent in enumerate(doc_nlp.sents):
            sent_str = str(sent)
            start_pos = content.index(sent_str)
            end_pos = content.index(sent_str) + len(sent_str)
            if start_pos > len(self.title):
                start_pos -= offset
                end_pos -= offset

            self.sentence_by_id[idx] = Sentence(
                idx,
                sent_str,
                start_pos,
                end_pos
            )

        for tag in self.tags:
            self.entities_by_ent_id[tag.ent_id].append(tag)

        for ent_id, entities in self.entities_by_ent_id.items():
            for entity in entities:
                for sid, sent in self.sentence_by_id.items():
                    if sent.start <= entity.start <= sent.end:
                        self.sentences_by_ent_id[ent_id].add(sid)
                        self.entities_by_sentence[sid].add(entity)

    def to_dict(self, export_content=True, export_tags=True):
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
        if export_tags:
            out_dict.update({
                # "classification": list(self.classification.keys()),
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
        return out_dict

    def get_text_content(self):
        return f"{self.title} {self.abstract}"

    def __str__(self):
        return Document.create_pubtator(self.id, self.title, self.abstract) + "".join(
            [str(t) for t in self.tags]) + "\n"

    def __repr__(self):
        return "<Document {} {}>".format(self.id, self.title)

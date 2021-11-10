import stanza
from typing import List

from kgextractiontoolbox.document.document import TaggedDocument, TaggedEntity
from kgextractiontoolbox.entitylinking.tagging.base import BaseTagger


class StanzaTagger(BaseTagger):
    __name__ = "StanzaNER"
    __version__ = "1.0"

    def __init__(self, *args, **kwargs):
        self.__stanza = None
        super().__init__(*args, **kwargs)

    def tag_document_batch(self, in_docs: List[TaggedDocument]) -> List[TaggedDocument]:
        document_texts = []
        for in_doc in in_docs:
            pmid, title, abstact = in_doc.id, in_doc.title, in_doc.abstract
            content = title.strip() + " " + abstact.strip()
            #content = content.lower()
            document_texts.append(content)

        stanza_texts = [stanza.Document([], text=text) for text in document_texts]
        stanza_docs = self.__stanza(stanza_texts)
        ignored_entity_types = set(self.config.entity_type_blocked_list)
        for in_doc, stanza_doc in zip(in_docs, stanza_docs):
            for entity in stanza_doc.entities:
                start, end = entity.start_char, entity.end_char
                ent_str = entity.text
                ent_id = entity.text
                ent_type = entity.type

                # entity type belongs to ignored types
                if ent_type in ignored_entity_types:
                    continue

                in_doc.tags.append(TaggedEntity(document=in_doc.id, start=start, end=end, text=ent_str,
                                                ent_type=ent_type, ent_id=ent_id))
        return in_docs

    def prepare(self, resume=False, use_gpu=True):
        self.__stanza = stanza.Pipeline(lang='en', processors='tokenize,ner', use_gpu=use_gpu)
        pass

    def run(self):
        pass

    def get_progress(self):
        pass

    def get_tags(self):
        pass

    def get_successful_ids(self):
        pass

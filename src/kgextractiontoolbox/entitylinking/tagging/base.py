import logging
from typing import List

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.document.load_document import insert_taggers
from kgextractiontoolbox.backend.models import Tag, DocTaggedBy
from kgextractiontoolbox.entitylinking.entity_linking_config import Config
from kgextractiontoolbox.document.document import TaggedDocument, TaggedEntity


class BaseTagger:
    """
    Tagger base class. Provides basic functionality like
    - the initialization of logging,
    - adding tags to the database
    - selecting all tags which were found
    """
    OUTPUT_INTERVAL = 30
    TYPES = None
    __name__ = None
    __version__ = None

    def __init__(
            self,
            config: Config = None,
            logger=None,
            collection=None
    ):
        self.config: Config = config
        self.logger = logger if logger else logging.getLogger("preprocessing")
        self.name = self.__class__.__name__
        self.partial_tag_inserts = list()
        self.collection = collection
        if not collection:
            raise ValueError("Collection not set for tagger")

    def base_insert_tagger(self):
        self.logger.info('Add tagger')
        tagger_name = self.__name__
        tagger_version = self.__version__
        insert_taggers((tagger_name, tagger_version))

    def base_insert_tags_partial(self, tags: List[TaggedEntity]):
        """
        Stores tags to insert in a local list
        Does not store the data in the database
        You need to call bulk_insert_partial_tags to perform the inserting
        :param tags: a list of tagged entities
        :return: None
        """
        # Add tags
        for tag in tags:
            self.partial_tag_inserts.append(dict(
                ent_type=tag.ent_type,
                start=tag.start,
                end=tag.end,
                ent_id=tag.ent_id,
                ent_str=tag.text,
                document_id=tag.document,
                document_collection=self.collection,
            ))

    def bulk_insert_partial_tags(self):
        """
        Insert all partially saved tags as a large bulk insert to the database
        :return: None
        """
        session = Session.get()
        Tag.bulk_insert_values_into_table(session, self.partial_tag_inserts)
        self.partial_tag_inserts.clear()

    def base_insert_tags(self, doc: TaggedDocument, auto_commit=True):
        session = Session.get()

        tagged_ent_types = set()
        tag_inserts = []
        # Add tags
        for tag in doc.tags:
            tagged_ent_types.add(tag.ent_type)

            tag_inserts.append(dict(
                ent_type=tag.ent_type,
                start=tag.start,
                end=tag.end,
                ent_id=tag.ent_id,
                ent_str=tag.text,
                document_id=tag.document,
                document_collection=self.collection,
            ))

        doc_tagged_by_inserts = []
        # Add DocTaggedBy
        for ent_type in tagged_ent_types:
            doc_tagged_by_inserts.append(dict(
                document_id=doc.id,
                document_collection=self.collection,
                tagger_name=self.__name__,
                tagger_version=self.__version__,
                ent_type=ent_type,
            ))

        session.bulk_insert_mappings(Tag, tag_inserts)
        session.bulk_insert_mappings(DocTaggedBy, doc_tagged_by_inserts)

        if auto_commit:
            session.commit()

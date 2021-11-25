import logging
import os

import multiprocessing
from sqlalchemy.dialects.postgresql import insert
from threading import Thread
from typing import List, Tuple, Dict, Set

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Tag, DocTaggedBy
from kgextractiontoolbox.document.document import TaggedDocument, TaggedEntity
from kgextractiontoolbox.document.load_document import insert_taggers
from kgextractiontoolbox.document.regex import TAG_LINE_NORMAL
from kgextractiontoolbox.entitylinking.entity_linking_config import Config


# TODO: Add estimation when tagging is done
class BaseTagger(Thread):
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
            self, *args,
            collection: str = None,
            root_dir: str = None,
            input_dir: str = None,
            log_dir: str = None,
            config: Config = None,
            mapping_id_file: Dict[int, str] = None,
            mapping_file_id: Dict[str, int] = None,
            logger=None,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.collection: str = collection
        self.root_dir: str = root_dir
        self.input_dir: str = input_dir
        self.log_dir: str = log_dir
        self.config: Config = config
        self.thread = None
        self.logger = logger if logger else logging.getLogger("preprocessing")
        self.name = self.__class__.__name__
        self.files = set()
        self.partial_tag_inserts = list()
        self.progress_value: multiprocessing.Value = None

    def set_multiprocess_progress_value(self, progress_value):
        self.progress_value = progress_value

    def get_types(self):
        return self.__class__.TYPES

    def add_files(self, files: str):
        self.files.update(set(files))

    def prepare(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError

    def get_progress(self):
        raise NotImplementedError

    def finalize(self):
        """
        Add tags into database. First, clean tags, i.e., remove smaller tag ranges which are included in a larger tag.
        Create a mapping from document ID to set of tags and clean each set.

        Then, add tags into the database.
        """
        session = Session.get()
        tags = set(self.get_tags())

        self.logger.info('Cleaning tags')
        # Clean tags (remove smaller tags which are included in larger tags)
        doc2tags = {}
        for t in tags:
            did = t[0]
            if did not in doc2tags:
                doc2tags[did] = []
            doc2tags[did].append(t)

        # compare just the tags within a document
        tags_cleaned = []
        for did, doc_tags in doc2tags.items():
            doc_tags_cleaned = doc_tags.copy()
            for t1 in doc_tags:
                if len(t1) != 6:
                    doc_tags_cleaned.remove(t1)
                    print(f"removed {t1}")
                else:
                    for t2 in doc_tags_cleaned:
                        if int(t2[1]) < int(t1[1]) and int(t2[2]) > int(t1[2]):
                            doc_tags_cleaned.remove(t1)
                            break
            tags_cleaned.extend(doc_tags_cleaned)

        self.logger.info('Add tagger')
        tagger_name = self.__name__
        tagger_version = self.__version__
        insert_taggers((tagger_name, tagger_version))

        self.logger.info("Add tags")
        for d_id, start, end, ent_str, ent_type, ent_id in tags_cleaned:
            # is it composite tag?
            if ';' in ent_id or '|' in ent_id:
                if ';' in ent_id:
                    e_ids = ent_id.split(';')
                else:
                    e_ids = ent_id.split('|')
                for e_id in e_ids:
                    insert_tag = insert(Tag).values(
                        ent_type=ent_type,
                        start=start,
                        end=end,
                        ent_id=e_id,
                        ent_str=ent_str,
                        document_id=d_id,
                        document_collection=self.collection,
                    )
                    session.execute(insert_tag)
                    session.commit()
            else:
                insert_tag = insert(Tag).values(
                    ent_type=ent_type,
                    start=start,
                    end=end,
                    ent_id=ent_id,
                    ent_str=ent_str,
                    document_id=d_id,
                    document_collection=self.collection,
                )

                session.execute(insert_tag)
                session.commit()

        self.logger.info("Add doc_tagged_by")
        successful_ent_types = set(
            (did, ent_type) for ent_type in self.get_types() for did in self.get_successful_ids())
        for did, ent_type in successful_ent_types:
            insert_doc_tagged_by = insert(DocTaggedBy).values(
                document_id=did,
                document_collection=self.collection,
                tagger_name=tagger_name,
                tagger_version=tagger_version,
                ent_type=ent_type,
            )

            session.execute(insert_doc_tagged_by)
            session.commit()

        self.logger.info("Committed successfully")

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

    def get_tags(self):
        """
        Function returns list of 6-tuples with tags.
        Tuple consists of (document ID, start pos., end pos., matched text, tag type, entity ID)
        :return: List of 6-tuples
        """
        raise NotImplementedError

    def get_successful_ids(self):
        """
        Get a set of doc-ids that are already successfully processed. Should be overwritten by child classes.
        :return: set of ids
        """
        raise NotImplementedError

    @staticmethod
    def _get_tags(directory: str) -> List[Tuple[int, int, int, str, str, str]]:
        """
        Function returns list of tags (6-tuples) contained in all files in a certain directory.

        :param directory: Path to directory containing PubTator files
        :return: List of tag-tuples
        """
        tags = []
        # TODO: This function could (!) be too memory-intensive
        for fn in os.listdir(directory):
            with open(os.path.join(directory, fn)) as f:
                tags.extend(TAG_LINE_NORMAL.findall(f.read()))
        return tags

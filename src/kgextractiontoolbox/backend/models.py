import hashlib
import logging
import unicodedata
from collections import namedtuple
from datetime import datetime
from io import StringIO
from typing import List, Tuple, Set

from sqlalchemy import Column, String, Integer, DateTime, ForeignKeyConstraint, PrimaryKeyConstraint, \
    BigInteger, UniqueConstraint, Float, func
from sqlalchemy.ext.declarative import declarative_base

from kgextractiontoolbox.document.regex import ILLEGAL_CHAR
from kgextractiontoolbox.progress import print_progress_with_eta

Base = declarative_base()
BULK_INSERT_AFTER_K = 100000
POSTGRES_COPY_LOAD_AFTER_K = 1000000

BULK_QUERY_CURSOR_COUNT_DEFAULT = 10000

PredicationResult = namedtuple('PredicationResult', ["id", "document_id", "document_collection",
                                                     "subject_id", "subject_str", "subject_type",
                                                     "predicate", "relation",
                                                     "object_id", "object_str", "object_type",
                                                     "confidence", "sentence_id", "extraction_type"])


def chunks_list(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def postgres_sanitize_str(string: str) -> str:
    """
    Sanitizes a string for a postgres COPY insert
    :param string: a string
    :return: the sanitized string
    """
    return string.replace('\\', '\\\\')


def postgres_copy_insert(session, values: List[dict], table_name: str):
    """
    Performs a fast COPY INSERT operation for Postgres Databases
    Do not check any constraints!
    :param session: the current session object
    :param values: a list of dictionary objects (they must correspond to the table)
    :param table_name: the table name to insert into
    :return: None
    """
    for values_chunk in chunks_list(values, POSTGRES_COPY_LOAD_AFTER_K):
        connection = session.connection().connection
        memory_file = StringIO()
        attribute_keys = list(values_chunk[0].keys())
        for idx, v in enumerate(values_chunk):
            mem_str = '{}'.format('\t'.join([postgres_sanitize_str(str(v[k])) for k in attribute_keys]))
            if idx == 0:
                memory_file.write(mem_str)
            else:
                memory_file.write(f'\n{mem_str}')
        cursor = connection.cursor()
        logging.debug(f'Executing copy from {table_name}...')
        memory_file.seek(0)
        cursor.copy_from(memory_file, table_name, sep='\t', columns=attribute_keys)
        logging.debug('Committing...')
        connection.commit()
        memory_file.close()


def bulk_insert_values_to_table(session, values: List[dict], table_class, print_progress=False):
    """
    Performs a bulk insert to a database table
    :param session: the current session object
    :param values: a list of dictionary objects that correspond to the table
    :param table_class: the table class to insert into
    :param print_progress: should the progress be printed?
    :return: None
    """
    task_size = 1 + int(len(values) / BULK_INSERT_AFTER_K)
    start_time = datetime.now()
    for idx, chunk_values in enumerate(chunks_list(values, BULK_INSERT_AFTER_K)):
        if print_progress:
            print_progress_with_eta("Inserting values...", idx, task_size, start_time, print_every_k=1)
        session.bulk_insert_mappings(table_class, chunk_values)
        session.commit()


class DatabaseTable:
    """
    Every Database Class that inherits from this class will have this bulk insert method available as a class method
    """

    @classmethod
    def bulk_insert_values_into_table(cls, session, values: List[dict], check_constraints=True, print_progress=False):
        if not values or len(values) == 0:
            return
        logging.debug(f'Inserting values into {cls.__tablename__}...')
        if session.is_postgres and not check_constraints:
            postgres_copy_insert(session, values, cls.__tablename__)
        else:
            bulk_insert_values_to_table(session, values, cls, print_progress)
        logging.debug(f'{len(values)} values have been inserted')


class Document(Base, DatabaseTable):
    __tablename__ = "document"
    __table_args__ = (
        PrimaryKeyConstraint('collection', 'id', sqlite_on_conflict='IGNORE'),
    )
    collection = Column(String)
    id = Column(BigInteger)
    title = Column(String, nullable=False)
    abstract = Column(String, nullable=False)
    fulltext = Column(String)

    date_inserted = Column(DateTime, nullable=False, default=datetime.now)

    def __str__(self):
        return "{}{}".format(self.collection, self.id)

    def __repr__(self):
        return "<Document {}{}>".format(self.collection, self.id)

    def to_pubtator(self):
        return Document.create_pubtator(self.id, self.title, self.abstract)

    @staticmethod
    def create_pubtator(did, title: str, abstract: str):
        if title:
            title = unicodedata.normalize('NFD', title)
            title = ILLEGAL_CHAR.sub("", title).strip()
        else:
            title = ""
        if abstract:
            abstract = unicodedata.normalize('NFD', abstract)
            abstract = ILLEGAL_CHAR.sub("", abstract).strip()
        else:
            abstract = ""
        return "{id}|t|{tit}\n{id}|a|{abs}\n".format(id=did, tit=title, abs=abstract)

    @staticmethod
    def sanitize(to_sanitize):
        to_sanitize = unicodedata.normalize('NFD', to_sanitize)
        to_sanitize = ILLEGAL_CHAR.sub("", to_sanitize).strip()
        return to_sanitize

    @staticmethod
    def get_document_ids_for_collection(session, collection: str) -> Set[int]:
        query = session.query(Document.id).filter(Document.collection == collection)
        ids = set()
        for r in query:
            ids.add(int(r[0]))
        return ids

    @staticmethod
    def count_documents_in_collection(session, collection: str) -> int:
        return session.query(Document).filter(Document.collection == collection).count()


class Tagger(Base, DatabaseTable):
    __tablename__ = "tagger"
    __table_args__ = (
        PrimaryKeyConstraint('name', 'version', sqlite_on_conflict='IGNORE'),
    )
    name = Column(String, primary_key=True)
    version = Column(String, primary_key=True)


class DocTaggedBy(Base, DatabaseTable):
    __tablename__ = "doc_tagged_by"
    __table_args__ = (
        ForeignKeyConstraint(('document_id', 'document_collection'), ('document.id', 'document.collection')
                             , sqlite_on_conflict='IGNORE'),
        ForeignKeyConstraint(('tagger_name', 'tagger_version'), ('tagger.name', 'tagger.version')
                             , sqlite_on_conflict='IGNORE'),
        PrimaryKeyConstraint('document_id', 'document_collection', 'tagger_name', 'tagger_version', 'ent_type'
                             , sqlite_on_conflict='IGNORE'),
    )
    document_id = Column(BigInteger, nullable=False, index=True)
    document_collection = Column(String, nullable=False, index=True)
    tagger_name = Column(String, nullable=False)
    tagger_version = Column(String, nullable=False)
    ent_type = Column(String, nullable=False)
    date_inserted = Column(DateTime, nullable=False, default=datetime.now)


class Tag(Base, DatabaseTable):
    __tablename__ = "tag"
    __table_args__ = (
        ForeignKeyConstraint(('document_id', 'document_collection'), ('document.id', 'document.collection'),
                             sqlite_on_conflict='IGNORE'),
        UniqueConstraint('document_id', 'document_collection', 'start', 'end', 'ent_type', 'ent_id',
                         sqlite_on_conflict='IGNORE'),
        PrimaryKeyConstraint('id', sqlite_on_conflict='IGNORE')
    )

    id = Column(Integer)
    ent_type = Column(String, nullable=False)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    ent_id = Column(String, nullable=False)
    ent_str = Column(String, nullable=False)
    document_id = Column(BigInteger, nullable=False, index=True)
    document_collection = Column(String, nullable=False, index=True)

    def __eq__(self, other):
        return self.ent_type == other.ent_type and self.start == other.start and self.end == other.end and \
               self.ent_id == other.ent_id and self.ent_str == other.ent_str and \
               self.document_id == other.document_id and self.document_collection == other.document_collection

    def __hash__(self):
        return hash((self.ent_type, self.start, self.end, self.ent_id, self.ent_str, self.document_id,
                     self.document_collection))

    @staticmethod
    def create_pubtator(did, start, end, ent_str, ent_type, ent_id):
        return "{}\t{}\t{}\t{}\t{}\t{}\n".format(did, start, end, ent_str, ent_type, ent_id)

    def to_pubtator(self):
        return Tag.create_pubtator(self.document_id, self.start, self.end, self.ent_str, self.ent_type, self.ent_id)


class DocumentTranslation(Base, DatabaseTable):
    __tablename__ = "document_translation"
    __table_args__ = (
        PrimaryKeyConstraint('document_id', 'document_collection', sqlite_on_conflict='IGNORE'),
    )
    document_id = Column(BigInteger)
    document_collection = Column(String)
    source_doc_id = Column(String, nullable=False)
    md5 = Column(String, nullable=False)
    date_inserted = Column(DateTime, nullable=False, default=datetime.now)
    source = Column(String)

    @staticmethod
    def text_to_md5_hash(text: str) -> str:
        m = hashlib.md5()
        m.update(text.encode())
        return m.hexdigest()


class DocumentClassification(Base, DatabaseTable):
    __tablename__ = "document_classification"
    __table_args__ = (
        PrimaryKeyConstraint('document_id', 'document_collection', 'classification', sqlite_on_conflict='IGNORE'),
        ForeignKeyConstraint(('document_id', 'document_collection'), ('document.id', 'document.collection'))
    )
    document_id = Column(BigInteger, index=True)
    document_collection = Column(String, index=True)
    classification = Column(String)
    explanation = Column(String)

    @staticmethod
    def get_document_ids_for_class(session, document_collection: str, document_class: str) -> Set[int]:
        query = session.query(DocumentClassification.document_id).filter(
            DocumentClassification.classification == document_class).filter(
            DocumentClassification.document_collection == document_collection
        )
        ids = set()
        for r in query:
            ids.add(int(r[0]))
        return ids


class DocumentSection(Base, DatabaseTable):
    __tablename__ = "document_section"
    __table_args__ = (
        PrimaryKeyConstraint('document_id', 'document_collection', 'position', sqlite_on_conflict='IGNORE'),
        ForeignKeyConstraint(('document_id', 'document_collection'), ('document.id', 'document.collection'))
    )
    document_id = Column(BigInteger)
    document_collection = Column(String)
    position = Column(Integer)
    title = Column(String, nullable=False)
    text = Column(String, nullable=False)


class Predication(Base, DatabaseTable):
    __tablename__ = "predication"
    __table_args__ = (
        ForeignKeyConstraint(('document_id', 'document_collection'), ('document.id', 'document.collection')),
        ForeignKeyConstraint(('sentence_id',), ('sentence.id',)),
        PrimaryKeyConstraint('id', sqlite_on_conflict='IGNORE')
    )

    id = Column(BigInteger().with_variant(Integer, "sqlite"), autoincrement=True, primary_key=True)
    document_id = Column(BigInteger, nullable=False, index=True)
    document_collection = Column(String, nullable=False, index=True)
    subject_id = Column(String, nullable=False)
    subject_str = Column(String, nullable=False)
    subject_type = Column(String, nullable=False)
    predicate_org = Column(String, nullable=True)
    predicate = Column(String, nullable=False, index=True)
    relation = Column(String, nullable=True)
    object_id = Column(String, nullable=False)
    object_str = Column(String, nullable=False)
    object_type = Column(String, nullable=False)
    confidence = Column(Float, nullable=True)
    sentence_id = Column(BigInteger, nullable=False)
    extraction_type = Column(String, nullable=False)

    def __str__(self):
        return "<{} ({})>\t<{}>\t<{} ({})>".format(self.subject_id, self.subject_type,
                                                   self.relation,
                                                   self.object_id, self.object_type)

    def __repr__(self):
        return "<Predication {}>".format(self.id)

    @staticmethod
    def iterate_predications(session, document_collection=None,
                             bulk_query_cursor_count=BULK_QUERY_CURSOR_COUNT_DEFAULT,
                             check_relation_not_null=False):
        pred_query = session.query(Predication)
        if check_relation_not_null:
            pred_query = pred_query.filter(Predication.relation != None)
        if document_collection:
            pred_query = pred_query.filter(Predication.document_collection == document_collection)
        pred_query = pred_query.yield_per(bulk_query_cursor_count)
        for res in pred_query:
            yield res

    @staticmethod
    def iterate_predications_joined_sentences(session, document_collection=None,
                                              bulk_query_cursor_count=BULK_QUERY_CURSOR_COUNT_DEFAULT,
                                              check_relation_not_null=False):
        pred_query = session.query(Predication, Sentence).join(Sentence, Predication.sentence_id == Sentence.id)
        if check_relation_not_null:
            pred_query = pred_query.filter(Predication.relation != None)
        if document_collection:
            pred_query = pred_query.filter(Predication.document_collection == document_collection)
        pred_query = pred_query.yield_per(bulk_query_cursor_count)
        for res in pred_query:
            yield res

    @staticmethod
    def query_predication_count(session, document_collection=None, relation=None):
        """
        Counts the number of rows in Predicate
        :param session: session handle
        :param document_collection: count only in document collection
        :param relation: if given the predication is filtered by this relation
        :return: the number of rows
        """
        query = session.query(Predication)
        if document_collection:
            query = query.filter(Predication.document_collection == document_collection)
        if relation:
            query = query.filter(Predication.relation == relation)
        return query.count()

    @staticmethod
    def query_predicates_with_count(session, document_collection=None) -> List[Tuple[str, int]]:
        """
        Queries predicates with the corresponding count of tuples
        :param session: session handle
        :param document_collection: document collection
        :return: a list of tuples (predicate, count of entries)
        """
        if not document_collection:
            query = session.query(Predication.predicate, func.count(Predication.predicate)) \
                .group_by(Predication.predicate)
        else:
            query = session.query(Predication.predicate, func.count(Predication.predicate)) \
                .filter(Predication.document_collection == document_collection) \
                .group_by(Predication.predicate)

        predicates_with_count = []
        start_time = datetime.now()
        for r in session.execute(query):
            predicates_with_count.append((r[0], int(r[1])))
        logging.info('{} predicates queried in {}s'.format(len(predicates_with_count), datetime.now() - start_time))
        return sorted(predicates_with_count, key=lambda x: x[1], reverse=True)

    @staticmethod
    def query_predicates_with_mapping_and_count(session, document_collection=None) -> List[Tuple[str, str, int]]:
        """
        Queries predicates with the corresponding relation mapping and count of tuples
        :param session: session handle
        :param document_collection: document collection
        :return: a list of tuples (predicate, relation, count of entries)
        """
        if not document_collection:
            query = session.query(Predication.predicate, Predication.relation,
                                  func.count(Predication.predicate)) \
                .group_by(Predication.predicate, Predication.relation)
        else:
            query = session.query(Predication.predicate, Predication.relation,
                                  func.count(Predication.predicate)) \
                .filter(Predication.document_collection == document_collection) \
                .group_by(Predication.predicate, Predication.relation)

        predicates_with_count = []
        start_time = datetime.now()
        for r in session.execute(query):
            predicates_with_count.append((r[0], r[1], int(r[2])))
        logging.info('{} predicates queried in {}s'.format(len(predicates_with_count), datetime.now() - start_time))
        return sorted(predicates_with_count, key=lambda x: x[2], reverse=True)


class PredicationToDelete(Base, DatabaseTable):
    __tablename__ = "predication_to_delete"
    __table_args__ = (
        PrimaryKeyConstraint('predication_id', sqlite_on_conflict='IGNORE'),
    )
    predication_id = Column(BigInteger)


class Sentence(Base, DatabaseTable):
    __tablename__ = "sentence"
    __table_args__ = (
        PrimaryKeyConstraint('id', sqlite_on_conflict='IGNORE'),
    )

    id = Column(BigInteger)
    document_collection = Column(String, nullable=False, index=True)
    text = Column(String, nullable=False)
    md5hash = Column(String, nullable=False)

    @staticmethod
    def iterate_sentences(session, document_collection=None, bulk_query_cursor_count=BULK_QUERY_CURSOR_COUNT_DEFAULT):
        sent_query = session.query(Sentence)
        if document_collection:
            sent_query = sent_query.filter(Sentence.document_collection == document_collection)
        sent_query = sent_query.yield_per(bulk_query_cursor_count)
        for res in sent_query:
            yield res


class DocProcessedByIE(Base, DatabaseTable):
    __tablename__ = "doc_processed_by_ie"
    __table_args__ = (
        ForeignKeyConstraint(('document_id', 'document_collection'), ('document.id', 'document.collection')),
        PrimaryKeyConstraint('document_id', 'document_collection', 'extraction_type', sqlite_on_conflict='IGNORE')
    )
    document_id = Column(BigInteger)
    document_collection = Column(String)
    extraction_type = Column(String)
    date_inserted = Column(DateTime, nullable=False, default=datetime.now)

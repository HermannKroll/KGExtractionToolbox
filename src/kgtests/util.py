import logging
import os
import tempfile

import kgextractiontoolbox.entitylinking.entity_linking_config as cnf
from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.document.document import TaggedEntity
from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.config import GIT_ROOT_DIR
from kgextractiontoolbox.config import ENTITY_LINKING_CONFIG

test_dir = 'src/kgtests/'


def create_test_kwargs():
    config = cnf.Config(ENTITY_LINKING_CONFIG)
    test_kwargs = dict(logger=logging, config=config, collection='TestCollection')
    return test_kwargs


def get_test_resource_filepath(filename):
    return resource_rel_path(filename)


def tmp_rel_path(path):
    return proj_rel_path(test_dir + "tmp/" + path)


def resource_rel_path(path):
    return proj_rel_path(test_dir + "resources/" + path)


def proj_rel_path(path):
    return os.path.join(GIT_ROOT_DIR, path)


def make_test_tempdir():
    return tempfile.mkdtemp()


def is_file_content_equal(file_1, file_2):
    with open(file_1) as f1, open(file_2) as f2:
        return f1.read() == f2.read()


def get_tags_from_database(doc_id=None):
    session = Session.get()
    if doc_id is None:
        result = session.execute("SELECT * FROM tag")
    else:
        result = session.execute(f"SELECT * FROM TAG WHERE document_id={doc_id}")
    for row in result:
        yield TaggedEntity((row["document_id"], row["start"], row["end"],
                            row["ent_str"], row["ent_type"], row["ent_id"]))


def get_docs_tagged_by_from_database(doc_id=None):
    session = Session.get()
    if doc_id is None:
        result = session.execute("SELECT * FROM doc_tagged_by")
    else:
        result = session.execute(f"SELECT * FROM doc_tagged_by WHERE document_id={doc_id}")
    return result


def clear_database():
    """DANGER! ONLY USE IN TESTS, NOWHERE IN PRODUCTION CODE!"""
    session = Session.get()
    if Session.is_sqlite:
        session.execute("DELETE FROM tag")
        session.execute("DELETE FROM doc_tagged_by")


def clear_doc_tagged_by_table():
    """DANGER! ONLY USE IN TESTS, NOWHERE IN PRODUCTION CODE!"""
    session = Session.get()
    if Session.is_sqlite:
        session.execute("DELETE FROM doc_tagged_by")
